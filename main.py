import telebot, threading, random, time, io
from telebot import types
from datetime import datetime, timedelta
import os
from flask import Flask

from config import (TOKEN, ADMIN_ID, MAPS, LOG_CHANNEL_ID, LOG_THREAD_ID,
                    ACCEPT_TIMEOUT, SHOP_ITEMS, ONE_TIME_TYPES)
from database import (
    init_db, get_player, get_player_by_username, register_player, register_bot,
    set_username, set_game_id, set_admin,
    add_coins, remove_coins, set_coins, set_elo, add_elo, set_level, elo_to_level,
    add_badge, remove_badge,
    get_inventory, get_inventory_item, add_inventory_item,
    remove_inventory_item, deactivate_inventory_item, activate_inventory_item,
    has_active_item_type, cleanup_expired_items,
    update_stats, get_league_stats,
    grant_qual, get_top_players,
    save_match, finalize_match, finalize_match_with_winner, save_match_player_stats,
    get_map_stats, reset_player_stats, set_player_stats,
    add_warn, remove_warn, clear_warns, get_warns, get_warns_full,
    mute_player, unmute_player, is_muted, is_muted_full,
    ban_player, unban_player, is_banned, is_banned_full,
    is_calibrated, calib_count, CALIB_THRESHOLD
)
from cards import (
    create_profile_card, create_map_card, create_top_card,
    create_shop_card, create_inventory_card,
    create_lobby_card, create_match_start_card, create_match_result_card
)

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
init_db()

# Flask приложение для Render
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

# Запускаем Flask в отдельном потоке
threading.Thread(target=run_flask, daemon=True).start()

# ── Global state ─────────────────────────────────────────────────────
active_lobbies  = {}
active_matches  = {}
user_match      = {}
user_lobby      = {}
accept_timers   = {}
user_flow       = {}
stats_pending   = {}
screenshot_pend = {}
manage_target   = {}

# ═══════════════════════════════════════════════════════════════════
# ПРОВЕРКА БАНА
# ═══════════════════════════════════════════════════════════════════

def check_ban(uid, chat_id=None):
    banned, ban_until, ban_reason, ban_by, ban_type = is_banned_full(uid)
    if banned and chat_id:
        if ban_type == "temporary" and ban_until:
            until_date = datetime.fromisoformat(ban_until).strftime("%d.%m.%Y %H:%M")
            msg = f"🚫 <b>Вы заблокированы!</b>\n\nДо: {until_date}\nПричина: {ban_reason or 'Нарушение правил'}\nАдминистратор: {ban_by or 'Система'}"
        else:
            msg = f"🚫 <b>Вы заблокированы НАВСЕГДА!</b>\n\nПричина: {ban_reason or 'Нарушение правил'}\nАдминистратор: {ban_by or 'Система'}"
        bot.send_message(chat_id, msg, parse_mode="HTML")
        return True
    return banned

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def _pname(uid):
    p = get_player(uid)
    return p[1] if p else str(uid)

def _is_admin(uid):
    p = get_player(uid)
    return bool(p and p[17])

def _is_bot_player(uid):
    p = get_player(uid)
    return bool(p and p[21])

def send_log(text):
    if LOG_CHANNEL_ID:
        try:
            bot.send_message(LOG_CHANNEL_ID, f"📋 {text}")
        except:
            pass

def _check_reg(uid, chat_id):
    if check_ban(uid, chat_id):
        return False
    p = get_player(uid)
    if not p or not p[18]:
        bot.send_message(chat_id, "❌ Не зарегистрирован. Напиши /start")
        return False
    return True

def _stats_for_league(player, league):
    if league == "all":
        kills   = player[9]  or 0
        deaths  = player[10] or 0
        assists = player[11] or 0
        wins    = player[7]  or 0
        losses  = player[8]  or 0
        elo     = player[5]  or 1000
        level   = player[4]  or 1
    else:
        row = get_league_stats(player[0], league)
        if row:
            kills=row[3]; deaths=row[4]; assists=row[5]
            wins=row[6];  losses=row[7]; elo=row[8]
        else:
            kills=deaths=assists=wins=losses=0; elo=1000
        level = elo_to_level(elo)
    games = wins + losses
    kd    = round(kills/deaths, 2) if deaths > 0 else float(kills)
    wr    = round(wins/games*100, 1) if games > 0 else 0.0
    hs_p  = round((player[13] or 0)/max(kills, 1)*100, 1)
    return {"kills":kills,"deaths":deaths,"assists":assists,
            "wins":wins,"losses":losses,"games":games,
            "kd":kd,"winrate":wr,"elo":elo,"level":level,
            "mvp":player[12] or 0,"headshots":hs_p,"coins":player[6] or 0}

def _league_label(league):
    return {"all":"Общая","default":"Default","quals":"QUALS"}.get(league,"Общая")

def _profile_kb(uid, current="all"):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton(("✅ " if current=="all" else "")+"📊 Общая", callback_data=f"pstats_all_{uid}"),
        types.InlineKeyboardButton(("✅ " if current=="default" else "")+"🎮 Default", callback_data=f"pstats_default_{uid}"),
        types.InlineKeyboardButton(("✅ " if current=="quals" else "")+"⭐ Quals", callback_data=f"pstats_quals_{uid}")
    )
    return kb

def _send_profile(uid, chat_id, league="all"):
    p = get_player(uid)
    if not p: bot.send_message(chat_id, "Игрок не найден."); return
    stats = _stats_for_league(p, league)
    badges = [b for b in (p[22] or "").split(",") if b]
    img = create_profile_card(p, stats, badges, _league_label(league))
    bot.send_photo(chat_id, img, reply_markup=_profile_kb(uid, league))

def _main_menu_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎮 Найти матч", "👤 Профиль")
    kb.row("🏆 Топ", "🛒 Магазин", "🎒 Инвентарь")
    if _is_admin(uid):
        kb.row("⚙️ Админ панель")
    return kb

# ═══════════════════════════════════════════════════════════════════
# /START
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    uid = msg.from_user.id
    if check_ban(uid, msg.chat.id): return
    p = get_player(uid)
    if p and p[18]:
        bot.send_message(uid, "⚡ <b>FLITE FACEIT</b>", reply_markup=_main_menu_kb(uid), parse_mode="HTML")
        return
    user_flow[uid] = {"state": "reg_nick"}
    bot.send_message(uid, "👋 Добро пожаловать в <b>FLITE FACEIT</b>!\n\nШаг 1: Введи свой <b>никнейм</b>:", parse_mode="HTML")

@bot.message_handler(commands=['help'])
def cmd_help(msg):
    if check_ban(msg.from_user.id, msg.chat.id): return
    bot.send_message(msg.chat.id,
        "📋 <b>Команды:</b>\n"
        "/start — меню\n/profile — профиль\n/top — топ\n"
        "/shop — магазин\n/inv — инвентарь\n"
        "/play — калибровочные матчи\n\n"
        "👮 <b>Админ:</b>\n"
        "/manage <id/@ник> — управление игроком\n"
        "/addbot ник id [device] — создать бота\n"
        "/warn /unwarn /mute /unmute /ban /unban",
        parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════
# РЕГИСТРАЦИЯ
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: user_flow.get(m.from_user.id, {}).get("state", "").startswith("reg_"))
def handle_reg(msg):
    uid = msg.from_user.id
    if check_ban(uid, msg.chat.id): return
    state = user_flow[uid]["state"]
    text = (msg.text or "").strip()

    if state == "reg_nick":
        if not (2 <= len(text) <= 20):
            bot.send_message(uid, "❌ Никнейм 2–20 символов."); return
        user_flow[uid] = {"state": "reg_id", "nick": text}
        bot.send_message(uid, "📋 Введи свой <b>игровой ID</b>:", parse_mode="HTML")

    elif state == "reg_id":
        if not text.isdigit():
            bot.send_message(uid, "❌ ID — только цифры."); return
        user_flow[uid]["game_id"] = text
        user_flow[uid]["state"] = "reg_device"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.row("MOBILE", "PC")
        bot.send_message(uid, "📱 Выбери устройство:", reply_markup=kb)

    elif state == "reg_device":
        if text not in ("MOBILE", "PC"):
            bot.send_message(uid, "❌ Выбери MOBILE или PC."); return
        d = user_flow.pop(uid)
        register_player(uid, d["nick"], d["game_id"], text)
        send_log(f"📝 Новый игрок: {d['nick']} (#{uid})")
        bot.send_message(uid, f"✅ Зарегистрирован как <b>{d['nick']}</b>!", reply_markup=_main_menu_kb(uid), parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════
# ПРОФИЛЬ
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['profile'])
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def cmd_profile(msg):
    if not _check_reg(msg.from_user.id, msg.chat.id): return
    _send_profile(msg.from_user.id, msg.chat.id, "all")

@bot.callback_query_handler(func=lambda c: c.data.startswith("pstats_"))
def cb_profile_stats(c):
    _, league, uid_str = c.data.split("_", 2)
    bot.answer_callback_query(c.id)
    _send_profile(int(uid_str), c.message.chat.id, league)

# ═══════════════════════════════════════════════════════════════════
# PLAY (калибровка)
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['play'])
def cmd_play(msg):
    uid = msg.from_user.id
    if check_ban(uid, msg.chat.id): return
    if not _check_reg(uid, msg.chat.id): return
    
    muted, until = is_muted(uid)
    if muted:
        bot.send_message(uid, f"🔇 Вы замучены! До: {until[:16]}")
        return
    
    p = get_player(uid)
    if is_calibrated(p):
        bot.send_message(uid, "✅ Ты уже прошел калибровку! Используй «Найти матч» для обычных игр.")
        return
    
    cal = calib_count(p)
    bot.send_message(uid, f"📊 Калибровочный матч {cal}/{CALIB_THRESHOLD}\nОсталось: {CALIB_THRESHOLD - cal} матчей.\nИспользуй «Найти матч» для поиска.")
    _show_lobby_browser(uid, msg.chat.id, p[3] or "MOBILE", "default")

# ═══════════════════════════════════════════════════════════════════
# ТОП
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['top'])
@bot.message_handler(func=lambda m: m.text == "🏆 Топ")
def cmd_top(msg):
    if check_ban(msg.from_user.id, msg.chat.id): return
    img = create_top_card(get_top_players(10))
    bot.send_photo(msg.chat.id, img)

# ═══════════════════════════════════════════════════════════════════
# МАГАЗИН
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['shop'])
@bot.message_handler(func=lambda m: m.text == "🛒 Магазин")
def cmd_shop(msg):
    if check_ban(msg.from_user.id, msg.chat.id): return
    _show_shop(msg.from_user.id, msg.chat.id, "goods")

def _shop_kb(cat, items):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("🎨 Скины", callback_data="shop_skins"),
        types.InlineKeyboardButton("🎭 Декор", callback_data="shop_decor"),
        types.InlineKeyboardButton("🛍 Товары", callback_data="shop_goods"),
    )
    for i, item in enumerate(items):
        kb.add(types.InlineKeyboardButton(f"💰{item['price']} — {item['name'][:22]}", callback_data=f"buy_{cat}_{i}"))
    return kb

def _show_shop(uid, chat_id, cat):
    p = get_player(uid)
    coins = p[6] if p else 0
    items = SHOP_ITEMS.get(cat, [])
    img = create_shop_card(cat, items, coins)
    bot.send_photo(chat_id, img, reply_markup=_shop_kb(cat, items))

@bot.callback_query_handler(func=lambda c: c.data.startswith("shop_"))
def cb_shop_tab(c):
    bot.answer_callback_query(c.id)
    _show_shop(c.from_user.id, c.message.chat.id, c.data.split("_", 1)[1])

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def cb_buy(c):
    _, cat, idx_s = c.data.split("_", 2)
    uid = c.from_user.id
    item = SHOP_ITEMS.get(cat, [])[int(idx_s)]
    p = get_player(uid)
    if not p: bot.answer_callback_query(c.id, "Ошибка"); return
    if (p[6] or 0) < item["price"]:
        bot.answer_callback_query(c.id, f"❌ Мало монет! Нужно {item['price']}", show_alert=True); return
    remove_coins(uid, item["price"])
    days = item.get("days")
    add_inventory_item(uid, item["name"], item["item_type"], days=days, item_id=item["id"])
    bot.answer_callback_query(c.id, f"✅ Куплено: {item['name']}", show_alert=True)
    send_log(f"🛒 {_pname(uid)} купил «{item['name']}» за {item['price']} монет")

# ═══════════════════════════════════════════════════════════════════
# ИНВЕНТАРЬ
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['inv'])
@bot.message_handler(func=lambda m: m.text == "🎒 Инвентарь")
def cmd_inv(msg):
    uid = msg.from_user.id
    if check_ban(uid, msg.chat.id): return
    if not _check_reg(uid, msg.chat.id): return
    p = get_player(uid)
    inv = get_inventory(uid)
    img = create_inventory_card(p, inv)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for row in inv:
        inv_id, iname, itype, item_id, activated, expires = row
        lbl = ("✅ " if activated else "⚡ ") + iname[:28]
        kb.add(types.InlineKeyboardButton(lbl, callback_data=f"inv_{inv_id}"))
    bot.send_photo(msg.chat.id, img, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("inv_") and not c.data.startswith("inv_act") and not c.data.startswith("inv_mg"))
def cb_inv(c):
    inv_id = int(c.data.split("_")[1])
    uid = c.from_user.id
    row = get_inventory_item(inv_id)
    if not row or row[1] != uid:
        bot.answer_callback_query(c.id, "Ошибка"); return

    iname = row[2]; itype = row[3]; activated = row[6]

    if itype == "unwarn":
        w = get_warns(uid)
        if w == 0:
            bot.answer_callback_query(c.id, "У тебя нет варнов!", show_alert=True); return
        remove_warn(uid)
        remove_inventory_item(inv_id)
        bot.answer_callback_query(c.id, f"✅ Варн снят! Осталось варнов: {get_warns(uid)}", show_alert=True)
        send_log(f"🟡 {_pname(uid)} использовал «Снять Warn»")
        return

    if itype == "nick_change":
        remove_inventory_item(inv_id)
        user_flow[uid] = {"state": "nick_change"}
        bot.answer_callback_query(c.id)
        bot.send_message(uid, "✏️ Введи новый никнейм (2–20 символов):")
        return

    if activated:
        bot.answer_callback_query(c.id, "Уже активировано!", show_alert=True); return

    if itype == "qual":
        days = 30
        if row[7]:
            try:
                exp = datetime.fromisoformat(row[7])
                days = max(1, (exp - datetime.now()).days)
            except:
                pass
        activate_inventory_item(inv_id)
        grant_qual(uid, "QUALS", days)
        bot.answer_callback_query(c.id, f"✅ QUALS активирован на {days} дней!", show_alert=True)
        send_log(f"⭐ {_pname(uid)} активировал QUALS на {days}д")
        return

    activate_inventory_item(inv_id)
    bot.answer_callback_query(c.id, f"✅ «{iname}» активировано!", show_alert=True)
    send_log(f"⚡ {_pname(uid)} активировал «{iname}»")

@bot.message_handler(func=lambda m: user_flow.get(m.from_user.id, {}).get("state") == "nick_change")
def handle_nick_change(msg):
    uid = msg.from_user.id
    if check_ban(uid, msg.chat.id): return
    text = (msg.text or "").strip()
    if not (2 <= len(text) <= 20):
        bot.send_message(uid, "❌ Никнейм 2–20 символов. Попробуй ещё раз:"); return
    old = _pname(uid)
    set_username(uid, text)
    user_flow.pop(uid, None)
    bot.send_message(uid, f"✅ Ник изменён: <b>{old}</b> → <b>{text}</b>", parse_mode="HTML")
    send_log(f"✏️ {old} (#{uid}) → ник: {text}")

# ═══════════════════════════════════════════════════════════════════
# ПОИСК МАТЧА (ЛОББИ)
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text == "🎮 Найти матч")
def cmd_find(msg):
    uid = msg.from_user.id
    if check_ban(uid, msg.chat.id): return
    if not _check_reg(uid, msg.chat.id): return
    
    muted, until = is_muted(uid)
    if muted:
        bot.send_message(uid, f"🔇 Вы замучены! До: {until[:16]}")
        return
    
    p = get_player(uid)
    _show_lobby_browser(uid, msg.chat.id, p[3] or "MOBILE", "default")

def _make_lobbies_data(league):
    result = []
    for dv in ("MOBILE", "PC"):
        for slot in range(1, 6):
            key = f"{league}_{dv}_{slot}"
            lob = active_lobbies.get(key)
            result.append({
                "key": key, "device": dv, "slot": slot,
                "count": len(lob["players"]) if lob else 0,
                "status": lob["status"] if lob else "empty"
            })
    return result

def _show_lobby_browser(uid, chat_id, device, league):
    lobbies_data = _make_lobbies_data(league)
    img = create_lobby_card(league, lobbies_data)
    kb = types.InlineKeyboardMarkup(row_width=5)
    for dv in ("MOBILE", "PC"):
        row_btns = []
        for slot in range(1, 6):
            key = f"{league}_{dv}_{slot}"
            lob = active_lobbies.get(key)
            count = len(lob["players"]) if lob else 0
            st = lob["status"] if lob else "empty"
            em = "🔴" if st not in ("waiting","empty") else ("🟢" if count > 0 else "⚪")
            row_btns.append(types.InlineKeyboardButton(f"{em}{dv[0]}{slot}({count})", callback_data=f"join_{league}_{dv}_{slot}"))
        kb.add(*row_btns)
    kb.add(
        types.InlineKeyboardButton("🎮 Default", callback_data=f"browse_default_{device}"),
        types.InlineKeyboardButton("⭐ QUALS", callback_data=f"browse_quals_{device}")
    )
    bot.send_photo(chat_id, img, caption=f"🎮 Выбери слот (Лига: {'QUALS' if league!='default' else 'Default'})", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("browse_"))
def cb_browse(c):
    _, league, device = c.data.split("_", 2)
    bot.answer_callback_query(c.id)
    _show_lobby_browser(c.from_user.id, c.message.chat.id, device, league)

@bot.callback_query_handler(func=lambda c: c.data.startswith("join_"))
def cb_join(c):
    parts = c.data.split("_"); league = parts[1]; device = parts[2]; slot = int(parts[3])
    uid = c.from_user.id
    key = f"{league}_{device}_{slot}"
    bot.answer_callback_query(c.id)
    
    if check_ban(uid, c.message.chat.id): return
    
    muted, until = is_muted(uid)
    if muted:
        bot.send_message(uid, f"🔇 Вы замучены! До: {until[:16]}")
        return

    old = user_lobby.get(uid)
    if old and old != key:
        _leave_lobby(uid, old)

    if key not in active_lobbies:
        active_lobbies[key] = {
            "key": key, "league": league, "device": device, "slot": slot,
            "players": [], "status": "waiting", "ready": set(),
            "bans": [], "map_pool": list(MAPS), "all_maps": list(MAPS),
            "captain_ct": None, "captain_t": None,
            "team_ct": [], "team_t": [], "veto_turn": "ct", "ban_count": 0,
            "match_id": None
        }
    lob = active_lobbies[key]
    
    if lob["status"] != "waiting":
        bot.send_message(uid, "❌ Лобби уже в игре.")
        return
    if uid in lob["players"]:
        bot.send_message(uid, f"✅ Ты уже в лобби {key}.")
        return
    if len(lob["players"]) >= 10:
        bot.send_message(uid, "❌ Лобби полное.")
        return

    lob["players"].append(uid)
    user_lobby[uid] = key
    name = _pname(uid)
    _bcast(lob, f"👤 <b>{name}</b> вошёл. [{len(lob['players'])}/10]")
    send_log(f"👤 {name} → {key} [{len(lob['players'])}/10]")
    
    if len(lob["players"]) >= 10:
        _start_accept(key)

@bot.callback_query_handler(func=lambda c: c.data.startswith("leave_lobby_"))
def cb_leave_lobby(c):
    uid = c.from_user.id
    key = c.data.split("_", 2)[2]
    bot.answer_callback_query(c.id)
    
    lob = active_lobbies.get(key)
    if not lob or uid not in lob["players"]:
        bot.send_message(uid, "❌ Ты не в этом лобби.")
        return
    
    _leave_lobby(uid, key)
    bot.send_message(uid, f"✅ Ты покинул лобби {key}")
    _bcast(lob, f"👤 {_pname(uid)} покинул лобби. [{len(lob['players'])}/10]")

def _bcast(lob, text, markup=None):
    for uid in lob["players"]:
        try:
            if lob["status"] == "waiting":
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("🚪 Выйти из лобби", callback_data=f"leave_lobby_{lob['key']}"))
                bot.send_message(uid, text, parse_mode="HTML", reply_markup=kb)
            else:
                kw = {"reply_markup": markup} if markup else {}
                bot.send_message(uid, text, parse_mode="HTML", **kw)
        except Exception:
            pass

def _leave_lobby(uid, key):
    lob = active_lobbies.get(key)
    if not lob: return
    if uid in lob["players"]:
        lob["players"].remove(uid)
    lob["ready"].discard(uid)
    user_lobby.pop(uid, None)
    _cancel_timer(key, uid)

def _cancel_timer(key, uid):
    tk = f"{key}_{uid}"
    t = accept_timers.pop(tk, None)
    if t: t.cancel()

# ═══════════════════════════════════════════════════════════════════
# ПРИНЯТИЕ МАТЧА
# ═══════════════════════════════════════════════════════════════════

def _start_accept(key):
    lob = active_lobbies.get(key)
    if not lob: return
    lob["status"] = "accept"
    lob["ready"] = set()
    send_log(f"⚔️ {key}: 10 игроков — Accept")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Принять матч", callback_data=f"accept_{key}"))
    for uid in lob["players"]:
        if _is_bot_player(uid):
            lob["ready"].add(uid); continue
        try:
            bot.send_message(uid, f"⚔️ <b>Матч найден!</b>\n\nЛига: {lob['league'].upper()} | Слот: {lob['slot']}\n⏳ <b>{ACCEPT_TIMEOUT} секунд</b> чтобы принять!", reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
        _start_accept_timer(key, uid)
    threading.Timer(0.5, _check_all_ready, [key]).start()

def _start_accept_timer(key, uid):
    tk = f"{key}_{uid}"
    t = threading.Timer(ACCEPT_TIMEOUT, _timeout_warn, [key, uid])
    t.start()
    accept_timers[tk] = t

def _timeout_warn(key, uid):
    lob = active_lobbies.get(key)
    if not lob or lob["status"] != "accept": return
    if uid in lob["ready"]: return
    _leave_lobby(uid, key)
    
    warns = add_warn(uid, reason="Не принял матч", admin_id=None)
    name = _pname(uid)
    
    try:
        bot.send_message(uid, 
            f"⚠️ <b>Варн!</b> Не принял матч.\n"
            f"Варнов: {warns}/3\n"
            f"Причина: Не принял матч в течение {ACCEPT_TIMEOUT} секунд",
            parse_mode="HTML")
    except:
        pass
    
    send_log(f"⚠️ {name} не принял матч. Варнов: {warns}")
    
    if warns >= 3:
        clear_warns(uid)
        until = mute_player(uid, hours=2, reason="3 варна (не принятие матчей)", admin_id=None)
        try:
            bot.send_message(uid, 
                f"🔇 <b>Мут 2 часа!</b>\n"
                f"Причина: Накоплено 3 варна за не принятие матчей\n"
                f"До: {until[:16]}",
                parse_mode="HTML")
        except:
            pass
        send_log(f"🔇 {name} мут 2ч за 3 варна")
    
    if len(lob["players"]) < 10 and lob["status"] == "accept":
        lob["status"] = "waiting"
        _bcast(lob, "❌ Игрок не принял. Набор возобновлён...")

@bot.callback_query_handler(func=lambda c: c.data.startswith("accept_"))
def cb_accept(c):
    key = c.data.split("_", 1)[1]
    uid = c.from_user.id
    lob = active_lobbies.get(key)
    if not lob or lob["status"] != "accept":
        bot.answer_callback_query(c.id, "Недоступно"); return
    if uid not in lob["players"]:
        bot.answer_callback_query(c.id, "Ты не в этом лобби"); return
    lob["ready"].add(uid)
    _cancel_timer(key, uid)
    bot.answer_callback_query(c.id, "✅ Принято!")
    _check_all_ready(key)

def _check_all_ready(key):
    lob = active_lobbies.get(key)
    if not lob or lob["status"] != "accept": return
    humans = [u for u in lob["players"] if not _is_bot_player(u)]
    if all(u in lob["ready"] for u in humans) and len(lob["players"]) == 10:
        _start_veto(key)

# ═══════════════════════════════════════════════════════════════════
# ВЕТО
# ═══════════════════════════════════════════════════════════════════

def _start_veto(key):
    lob = active_lobbies.get(key)
    if not lob: return
    lob["status"] = "veto"
    lob["bans"] = []
    lob["map_pool"] = list(MAPS)
    lob["all_maps"] = list(MAPS)
    lob["ban_count"] = 0
    lob["veto_turn"] = "ct"
    players = list(lob["players"])
    random.shuffle(players)
    lob["team_ct"] = players[:5]
    lob["team_t"] = players[5:]
    lob["captain_ct"] = lob["team_ct"][0]
    lob["captain_t"] = lob["team_t"][0]
    for uid in lob["team_ct"]:
        try: bot.send_message(uid, "🟦 Ты в команде <b>CT</b>!", parse_mode="HTML")
        except: pass
    for uid in lob["team_t"]:
        try: bot.send_message(uid, "🟧 Ты в команде <b>T</b>!", parse_mode="HTML")
        except: pass
    send_log(f"🗺 {key}: Вето. CT: {_pname(lob['captain_ct'])} / T: {_pname(lob['captain_t'])}")
    _send_veto(key)

def _send_veto(key):
    lob = active_lobbies.get(key)
    if not lob or lob["status"] != "veto": return
    turn = lob["veto_turn"]
    cap_id = lob["captain_ct"] if turn == "ct" else lob["captain_t"]
    if _is_bot_player(cap_id):
        threading.Timer(2.0, _bot_ban, [key]).start()
        return
    ms = get_map_stats()
    img = create_map_card(lob, ms)
    kb = types.InlineKeyboardMarkup(row_width=3)
    for m in lob["map_pool"]:
        kb.add(types.InlineKeyboardButton(f"❌ {m}", callback_data=f"ban_{key}_{m}"))
    cap_name = _pname(cap_id)
    caption = f"🗺 <b>ВЕТО</b> — Бан {lob['ban_count']+1}/4\nХод <b>{'CT' if turn=='ct' else 'T'}</b> — {cap_name}"
    for uid in lob["players"]:
        try:
            if uid == cap_id:
                bot.send_photo(uid, img, caption=caption, reply_markup=kb, parse_mode="HTML")
            else:
                bot.send_photo(uid, img, caption=caption, parse_mode="HTML")
        except Exception:
            pass

def _bot_ban(key):
    lob = active_lobbies.get(key)
    if not lob or lob["status"] != "veto" or not lob["map_pool"]: return
    _do_ban(key, random.choice(lob["map_pool"]))

@bot.callback_query_handler(func=lambda c: c.data.startswith("ban_"))
def cb_ban(c):
    parts = c.data.split("_", 2)
    key = parts[1]
    mname = parts[2]
    uid = c.from_user.id
    lob = active_lobbies.get(key)
    if not lob or lob["status"] != "veto":
        bot.answer_callback_query(c.id, "Вето недоступно"); return
    turn = lob["veto_turn"]
    cap_id = lob["captain_ct"] if turn == "ct" else lob["captain_t"]
    if uid != cap_id:
        bot.answer_callback_query(c.id, "Сейчас не твой ход!"); return
    if mname not in lob["map_pool"]:
        bot.answer_callback_query(c.id, "Карта уже забанена"); return
    bot.answer_callback_query(c.id)
    _do_ban(key, mname)

def _do_ban(key, mname):
    lob = active_lobbies.get(key)
    if not lob: return
    turn = lob["veto_turn"]
    lob["bans"].append({"map": mname, "by": turn})
    lob["map_pool"].remove(mname)
    lob["ban_count"] += 1
    cap_name = _pname(lob["captain_ct"] if turn=="ct" else lob["captain_t"])
    _bcast(lob, f"🚫 <b>{cap_name} ({turn.upper()})</b> забанил <b>{mname}</b>")
    send_log(f"🚫 {key}: {cap_name} забанил {mname}")
    lob["veto_turn"] = "t" if turn == "ct" else "ct"
    if lob["ban_count"] >= 4 and len(lob["map_pool"]) == 1:
        final = lob["map_pool"][0]
        _bcast(lob, f"✅ <b>Финальная карта: {final}</b>")
        send_log(f"✅ {key}: Финал → {final}")
        _start_match(key, final)
    else:
        _send_veto(key)

# ═══════════════════════════════════════════════════════════════════
# НАЧАЛО МАТЧА
# ═══════════════════════════════════════════════════════════════════

def _start_match(key, map_name):
    lob = active_lobbies.get(key)
    if not lob: return
    lob["status"] = "active"
    league = lob["league"]
    mid = save_match(key, map_name, lob["team_ct"], lob["team_t"], league)
    match = {
        "match_id": mid, "lobby_key": key, "map_name": map_name,
        "league": league, "team_ct": list(lob["team_ct"]),
        "team_t": list(lob["team_t"]),
        "captain_ct": lob["captain_ct"], "captain_t": lob["captain_t"],
        "status": "active", "screenshot_file_id": None,
    }
    active_matches[mid] = match
    lob["match_id"] = mid
    for uid in lob["team_ct"] + lob["team_t"]:
        user_match[uid] = mid
    ct_rows = [get_player(u) for u in lob["team_ct"]]
    t_rows = [get_player(u) for u in lob["team_t"]]
    img = create_match_start_card(mid, map_name, league, lob["team_ct"], lob["team_t"], ct_rows, t_rows)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📸 Отправить результат", callback_data=f"result_{mid}"))
    for uid in lob["team_ct"] + lob["team_t"]:
        side = "CT" if uid in lob["team_ct"] else "T"
        try:
            bot.send_photo(uid, img, caption=f"⚔️ <b>Матч #{mid} начался!</b>\nКарта: {map_name} | Команда: <b>{side}</b>", reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
    send_log(f"⚔️ Матч #{mid} | {map_name} | {key}")

# ═══════════════════════════════════════════════════════════════════
# РЕЗУЛЬТАТ МАТЧА
# ═══════════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data.startswith("result_"))
def cb_result(c):
    mid = int(c.data.split("_")[1])
    uid = c.from_user.id
    if user_match.get(uid) != mid:
        bot.answer_callback_query(c.id, "Ты не в этом матче"); return
    bot.answer_callback_query(c.id)
    screenshot_pend[uid] = mid
    bot.send_message(uid, "📸 Отправь <b>фото-скриншот</b> результата:", parse_mode="HTML")

@bot.message_handler(content_types=['photo'], func=lambda m: m.from_user.id in screenshot_pend)
def handle_screenshot(msg):
    uid = msg.from_user.id
    mid = screenshot_pend.pop(uid, None)
    if not mid: return
    match = active_matches.get(mid)
    if not match: return
    file_id = msg.photo[-1].file_id
    match["screenshot_file_id"] = file_id
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✏️ Ввести статистику", callback_data=f"enterstats_{mid}"))
    caption = f"📸 Скриншот матча <b>#{mid}</b>\nКарта: {match['map_name']} | Лига: {match['league']}\n\nCT: {', '.join(_pname(u) for u in match['team_ct'])}\nT: {', '.join(_pname(u) for u in match['team_t'])}"
    notified = set()
    for aid in match["team_ct"] + match["team_t"]:
        if _is_admin(aid) and aid not in notified:
            try:
                bot.send_photo(aid, file_id, caption=caption, reply_markup=kb, parse_mode="HTML")
                notified.add(aid)
            except:
                pass
    if ADMIN_ID not in notified:
        try:
            bot.send_photo(ADMIN_ID, file_id, caption=caption, reply_markup=kb, parse_mode="HTML")
        except:
            pass
    bot.send_message(uid, "✅ Скриншот отправлен. Ожидай результата!")
    send_log(f"📸 Скриншот матча #{mid} от {_pname(uid)}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("enterstats_"))
def cb_enter_stats(c):
    mid = int(c.data.split("_")[1])
    uid = c.from_user.id
    if not _is_admin(uid):
        bot.answer_callback_query(c.id, "Нет доступа"); return
    bot.answer_callback_query(c.id)
    match = active_matches.get(mid, {})
    ct_names = " | ".join(_pname(u) for u in match.get("team_ct", []))
    t_names = " | ".join(_pname(u) for u in match.get("team_t", []))
    stats_pending[uid] = mid
    bot.send_message(uid, f"✏️ <b>Статистика матча #{mid}</b>\n\n<b>CT:</b> {ct_names}\n<b>T:</b> {t_names}\n\nФормат:\n<code>13:11\nCT\nID K A D\nID K A D\n...(5 CT)\nT\nID K A D\n...(5 T)</code>\n\n• Счёт: победители:проигравшие\n• ID = telegram user_id", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.from_user.id in stats_pending and not user_flow.get(m.from_user.id, {}).get("state", "").startswith("adm_"))
def handle_stats_input(msg):
    uid = msg.from_user.id
    mid = stats_pending.pop(uid, None)
    if not mid: return
    match = active_matches.get(mid)
    if not match:
        bot.send_message(uid, "❌ Матч не найден."); return
    try:
        lines = [l.strip() for l in (msg.text or "").strip().splitlines() if l.strip()]
        sc = lines[0].replace(" ", "").split(":")
        score_w, score_l = int(sc[0]), int(sc[1])
        ct_entries = []
        t_entries = []
        cur_side = None
        for line in lines[1:]:
            if line.upper() == "CT":
                cur_side = "ct"
                continue
            if line.upper() == "T":
                cur_side = "t"
                continue
            parts = line.split()
            if len(parts) >= 4:
                pid, k, a, d = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                if cur_side == "ct":
                    ct_entries.append((pid, k, a, d))
                else:
                    t_entries.append((pid, k, a, d))
        if not ct_entries and not t_entries:
            raise ValueError("Нет данных")
        winner = "ct" if score_w >= score_l else "t"
        score_ct = score_w if winner == "ct" else score_l
        score_t = score_l if winner == "ct" else score_w
        _finalize_match(mid, winner, score_ct, score_t, ct_entries, t_entries, uid)
    except Exception as e:
        bot.send_message(uid, f"❌ Ошибка: {e}\n\nПроверь формат и повтори.")
        stats_pending[uid] = mid

def _finalize_match(mid, winner, score_ct, score_t, ct_entries, t_entries, admin_uid):
    match = active_matches.get(mid)
    if not match: return
    league = match["league"]
    map_name = match["map_name"]
    finalize_match_with_winner(mid, winner, map_name, score_ct, score_t)
    ct_card_data = []
    t_card_data = []

    def _process(entries, side, card_list):
        won = (side == winner)
        for pid, k, a, d in entries:
            p = get_player(pid)
            if not p:
                card_list.append((None, k, d, a))
                continue
            base = random.randint(15, 20) if won else random.randint(5, 6)
            x2 = has_active_item_type(pid, "x2coins")
            coins = base * 2 if x2 else base
            add_coins(pid, coins)
            calib, new_elo = update_stats(pid, k, d, a, 0, 0.0, won, league=league)
            new_lv = elo_to_level(new_elo)
            kd_v = round(k/d, 2) if d > 0 else float(k)
            rating = round(kd_v * 0.85 + a * 0.02, 2)
            impact = round(kd_v * 0.9, 2)
            save_match_player_stats(mid, pid, side, k, d, a, rating, impact, kd_v)
            coin_txt = f"{'x2! ' if x2 else ''}💰 +{coins} монет"
            calib_txt = f"\n📊 Калибровка: {calib}/{CALIB_THRESHOLD}" if calib < CALIB_THRESHOLD else f"\n📊 ELO: {new_elo} → LV{new_lv}"
            try:
                bot.send_message(pid, f"{'🏆 Победа!' if won else '💀 Поражение'}\nK: {k}  A: {a}  D: {d}\n{coin_txt}{calib_txt}")
            except Exception:
                pass
            card_list.append((p, k, d, a))

    _process(ct_entries[:5], "ct", ct_card_data)
    _process(t_entries[:5], "t", t_card_data)

    img = create_match_result_card(mid, map_name, league, score_ct, score_t, winner, ct_card_data, t_card_data)

    for uid in match["team_ct"] + match["team_t"]:
        try:
            bot.send_photo(uid, img, caption=f"📊 <b>Результат матча #{mid}</b>\n{'🏆 CT победили' if winner=='ct' else '🏆 T победили'} {score_ct}:{score_t}", parse_mode="HTML")
        except Exception:
            pass

    key = match.get("lobby_key")
    if key and key in active_lobbies:
        for u in active_lobbies[key]["players"]:
            user_match.pop(u, None)
            user_lobby.pop(u, None)
        del active_lobbies[key]
    active_matches.pop(mid, None)
    bot.send_message(admin_uid, f"✅ Матч #{mid} завершён и статистика сохранена!")
    send_log(f"✅ Матч #{mid}: {winner.upper()} {score_ct}:{score_t}")

# ═══════════════════════════════════════════════════════════════════
# АДМИН ПАНЕЛЬ
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text == "⚙️ Админ панель")
@bot.message_handler(commands=['admin'])
def cmd_admin(msg):
    if not _is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "🚫 Нет доступа.")
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👤 Найти игрока", callback_data="adm_find"),
        types.InlineKeyboardButton("🤖 Добавить бота", callback_data="adm_addbot"),
        types.InlineKeyboardButton("📋 Лобби", callback_data="adm_lobbies"),
        types.InlineKeyboardButton("⚔️ Матчи", callback_data="adm_matches"),
    )
    bot.send_message(msg.chat.id, "⚙️ <b>Панель администратора</b>", reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "adm_lobbies")
def cb_lobbies_info(c):
    if not _is_admin(c.from_user.id): return
    bot.answer_callback_query(c.id)
    text = "📋 <b>Лобби:</b>\n"
    for k, l in active_lobbies.items():
        text += f"• {k} [{len(l['players'])}/10] — {l['status']}\n"
    if not active_lobbies:
        text += "Нет активных."
    bot.send_message(c.from_user.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "adm_matches")
def cb_matches_info(c):
    if not _is_admin(c.from_user.id): return
    bot.answer_callback_query(c.id)
    text = "⚔️ <b>Матчи:</b>\n"
    for mid, m in active_matches.items():
        text += f"• #{mid} {m['map_name']} | {m['league']}\n"
    if not active_matches:
        text += "Нет активных."
    bot.send_message(c.from_user.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "adm_find")
def cb_adm_find(c):
    if not _is_admin(c.from_user.id): return
    bot.answer_callback_query(c.id)
    user_flow[c.from_user.id] = {"state": "adm_find_player"}
    bot.send_message(c.from_user.id, "👤 Введи ID, @ник или Game ID игрока:")

@bot.callback_query_handler(func=lambda c: c.data == "adm_addbot")
def cb_adm_addbot_ui(c):
    if not _is_admin(c.from_user.id): return
    bot.answer_callback_query(c.id)
    user_flow[c.from_user.id] = {"state": "adm_bot_input"}
    bot.send_message(c.from_user.id, "🤖 Формат: <code>Имя GameID Device</code>\nПример: <code>BotNick 9999 PC</code>", parse_mode="HTML")

@bot.message_handler(func=lambda m: user_flow.get(m.from_user.id, {}).get("state", "").startswith("adm_"))
def handle_admin_flow(msg):
    uid = msg.from_user.id
    state = user_flow.get(uid, {}).get("state", "")
    text = (msg.text or "").strip()
    if not _is_admin(uid):
        user_flow.pop(uid, None)
        return

    if state == "adm_find_player":
        user_flow.pop(uid, None)
        target = None
        if text.startswith("@"):
            target = get_player_by_username(text[1:])
        elif text.isdigit():
            target = get_player(int(text))
        if not target:
            bot.send_message(uid, "❌ Не найден.")
            return
        manage_target[uid] = target[0]
        _manage_panel(uid, target[0])

    elif state == "adm_bot_input":
        user_flow.pop(uid, None)
        parts = text.split()
        if len(parts) < 2:
            bot.send_message(uid, "❌ Формат: Имя ID [Device]")
            return
        bname = parts[0]
        bgid = parts[1]
        bdev = parts[2] if len(parts) > 2 else "PC"
        buid = random.randint(10000000, 99999999)
        register_bot(buid, bname, bgid, bdev)
        bot.send_message(uid, f"✅ Бот <b>{bname}</b> создан, UID: {buid}", parse_mode="HTML")

def _manage_panel(admin_uid, tid):
    p = get_player(tid)
    if not p:
        bot.send_message(admin_uid, "❌ Игрок не найден")
        return
    muted_f, until, mute_reason, mute_by = is_muted_full(tid)
    banned_f, ban_until, ban_reason, ban_by, ban_type = is_banned_full(tid)
    warns_info = get_warns_full(tid)
    
    text = (f"👤 <b>{p[1]}</b> (#{tid})\n"
            f"GameID: {p[2]} | LV{p[4]} | {p[5]} ELO | 💰{p[6]}\n"
            f"Варны: {warns_info['count']}/3\n"
            f"Мут: {'Да (до '+until[:16]+')' if muted_f else 'Нет'}\n"
            f"Бан: {'Да' if banned_f else 'Нет'}")
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✏️ Ник", callback_data=f"mg_nick_{tid}"),
        types.InlineKeyboardButton("💰 Монеты", callback_data=f"mg_coins_{tid}"),
        types.InlineKeyboardButton("📊 ELO", callback_data=f"mg_elo_{tid}"),
        types.InlineKeyboardButton("⚠️ Варн", callback_data=f"mg_warn_{tid}"),
        types.InlineKeyboardButton("🔇 Мут", callback_data=f"mg_mute_{tid}"),
        types.InlineKeyboardButton("🚫 Бан", callback_data=f"mg_ban_{tid}"),
        types.InlineKeyboardButton("✅ Снять мут", callback_data=f"mg_unmute_{tid}"),
        types.InlineKeyboardButton("✅ Разбан", callback_data=f"mg_unban_{tid}"),
        types.InlineKeyboardButton("🔄 Сброс варнов", callback_data=f"mg_clrwarn_{tid}"),
    )
    bot.send_message(admin_uid, text, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("mg_"))
def cb_manage(c):
    parts = c.data.split("_", 2)
    action = parts[1]
    tid = int(parts[2])
    uid = c.from_user.id
    if not _is_admin(uid):
        bot.answer_callback_query(c.id, "Нет доступа")
        return
    manage_target[uid] = tid
    bot.answer_callback_query(c.id)

    INSTANT = {
        "unmute": lambda: (unmute_player(tid), bot.send_message(uid, "✅ Мут снят"), _notify(tid, "✅ Администратор снял с вас мут")),
        "unban": lambda: (unban_player(tid), bot.send_message(uid, "✅ Бан снят"), _notify(tid, "✅ Администратор снял с вас бан")),
        "clrwarn": lambda: (clear_warns(tid), bot.send_message(uid, "✅ Варны сброшены"), _notify(tid, "✅ Администратор сбросил ваши варны")),
    }
    if action in INSTANT:
        INSTANT[action]()
        _manage_panel(uid, tid)
        return

    INPUT_STATES = {
        "nick": ("adm_mg_nick", "Введи новый никнейм:"),
        "coins": ("adm_mg_coins", "Введи количество монет:"),
        "elo": ("adm_mg_elo", "Введи новое ELO:"),
        "mute": ("adm_mg_mute", "Часов мута (по умолч. 2):"),
        "warn": ("adm_mg_warn", "Сколько варнов выдать (по умолч. 1):"),
        "ban": ("adm_mg_ban", "Формат: <дни> <причина>\nПример: 7 Оскорбления\nИли: 0 Навсегда"),
    }
    if action in INPUT_STATES:
        st, prompt = INPUT_STATES[action]
        user_flow[uid] = {"state": st}
        bot.send_message(uid, prompt)

def _notify(uid, text):
    try:
        bot.send_message(uid, text)
    except:
        pass

@bot.message_handler(func=lambda m: user_flow.get(m.from_user.id, {}).get("state", "").startswith("adm_mg_"))
def handle_admin_mg_input(msg):
    uid = msg.from_user.id
    state = user_flow.get(uid, {}).get("state", "")
    text = (msg.text or "").strip()
    if not _is_admin(uid):
        user_flow.pop(uid, None)
        return
    
    tid = manage_target.get(uid)
    if not tid:
        bot.send_message(uid, "❌ Ошибка: цель не найдена")
        user_flow.pop(uid, None)
        return
    
    try:
        if state == "adm_mg_nick":
            set_username(tid, text)
            bot.send_message(uid, f"✅ Ник → <b>{text}</b>", parse_mode="HTML")
        elif state == "adm_mg_coins":
            if text.isdigit():
                set_coins(tid, int(text))
                bot.send_message(uid, f"✅ Монеты → {text}")
            else:
                bot.send_message(uid, "❌ Введи число")
        elif state == "adm_mg_elo":
            if text.isdigit():
                e = int(text)
                set_elo(tid, e)
                set_level(tid, elo_to_level(e))
                bot.send_message(uid, f"✅ ELO→{e} LV{elo_to_level(e)}")
            else:
                bot.send_message(uid, "❌ Введи число")
        elif state == "adm_mg_mute":
            h = int(text) if text.isdigit() else 2
            until = mute_player(tid, h, reason="По решению администратора", admin_id=uid)
            bot.send_message(uid, f"✅ Мут на {h}ч. До: {until[:16]}")
            _notify(tid, f"🔇 Вы замучены на {h} часов администратором")
        elif state == "adm_mg_warn":
            cnt = int(text) if text.isdigit() else 1
            w = 0
            for _ in range(cnt):
                w = add_warn(tid, reason="Выдан администратором", admin_id=uid)
            bot.send_message(uid, f"✅ Варнов выдано: {cnt}. Итого: {w}")
            _notify(tid, f"⚠️ Получен варн от администратора! Итого: {w}/3")
        elif state == "adm_mg_ban":
            parts = text.split(" ", 1)
            if len(parts) < 2:
                bot.send_message(uid, "❌ Формат: <дни> <причина>\nПример: 7 Оскорбления\nИли: 0 Навсегда")
                user_flow[uid] = {"state": "adm_mg_ban"}
                return
            days_str = parts[0].strip()
            reason = parts[1].strip()
            
            if days_str.isdigit():
                days = int(days_str)
                if days == 0:
                    days = None
            else:
                bot.send_message(uid, "❌ Первым аргументом должны быть дни (число). 0 = навсегда")
                user_flow[uid] = {"state": "adm_mg_ban"}
                return
            
            ban_player(tid, days=days, reason=reason, admin_id=uid)
            if days:
                bot.send_message(uid, f"✅ Бан на {days} дней. Причина: {reason}")
                _notify(tid, f"🚫 Вы забанены на {days} дней. Причина: {reason} (Администратор: {_pname(uid)})")
            else:
                bot.send_message(uid, f"✅ Бан НАВСЕГДА. Причина: {reason}")
                _notify(tid, f"🚫 Вы забанены НАВСЕГДА. Причина: {reason} (Администратор: {_pname(uid)})")
    except Exception as e:
        bot.send_message(uid, f"❌ Ошибка: {e}")
    
    user_flow.pop(uid, None)
    _manage_panel(uid, tid)

# ═══════════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("⚡ FLITE FACEIT Bot запущен!")
    bot.infinity_polling(skip_pending=True)