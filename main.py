import telebot, threading, random, time, io
from telebot import types
from datetime import datetime, timedelta
import os
import sqlite3
from flask import Flask

from config import (TOKEN, ADMIN_ID, MAPS, LOG_CHANNEL_ID, LOG_THREAD_ID,
                    ACCEPT_TIMEOUT, SHOP_ITEMS, ONE_TIME_TYPES)
from database import (
    init_db, get_player, get_player_by_username, register_player, register_bot,
    set_username, set_game_id, set_admin, get_admin_name,
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
    return "ACTUAL FACEIT Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ── Global state ─────────────────────────────────────────────────────
active_lobbies = {}
active_matches = {}
user_match = {}
user_lobby = {}
accept_timers = {}
user_flow = {}
stats_pending = {}
screenshot_pend = {}
manage_target = {}

# ═══════════════════════════════════════════════════════════════════
# ПРОВЕРКА БАНА
# ═══════════════════════════════════════════════════════════════════

def check_ban(uid, chat_id=None):
    banned, ban_until, ban_reason, ban_by, ban_type = is_banned_full(uid)
    if banned and chat_id:
        if ban_type == "temporary" and ban_until:
            try:
                until_date = datetime.fromisoformat(ban_until).strftime("%d.%m.%Y %H:%M")
                msg = (f"🚫 <b>Вы заблокированы!</b>\n\n"
                       f"До: {until_date}\n"
                       f"Причина: {ban_reason if ban_reason else 'Нарушение правил'}\n"
                       f"Администратор: {ban_by if ban_by else 'Система'}")
            except:
                msg = (f"🚫 <b>Вы заблокированы!</b>\n\n"
                       f"Причина: {ban_reason if ban_reason else 'Нарушение правил'}\n"
                       f"Администратор: {ban_by if ban_by else 'Система'}")
        else:
            msg = (f"🚫 <b>Вы заблокированы НАВСЕГДА!</b>\n\n"
                   f"Причина: {ban_reason if ban_reason else 'Нарушение правил'}\n"
                   f"Администратор: {ban_by if ban_by else 'Система'}")
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

def _notify(uid, text):
    try:
        bot.send_message(uid, text)
    except:
        pass

def _stats_for_league(player, league):
    if league == "all":
        kills = player[9] or 0
        deaths = player[10] or 0
        assists = player[11] or 0
        wins = player[7] or 0
        losses = player[8] or 0
        elo = player[5] or 1000
        level = player[4] or 1
    else:
        row = get_league_stats(player[0], league)
        if row:
            kills = row[3]
            deaths = row[4]
            assists = row[5]
            wins = row[6]
            losses = row[7]
            elo = row[8]
        else:
            kills = deaths = assists = wins = losses = 0
            elo = 1000
        level = elo_to_level(elo)
    games = wins + losses
    kd = round(kills / deaths, 2) if deaths > 0 else float(kills)
    wr = round(wins / games * 100, 1) if games > 0 else 0.0
    hs_p = round((player[13] or 0) / max(kills, 1) * 100, 1)
    return {"kills": kills, "deaths": deaths, "assists": assists,
            "wins": wins, "losses": losses, "games": games,
            "kd": kd, "winrate": wr, "elo": elo, "level": level,
            "mvp": player[12] or 0, "headshots": hs_p, "coins": player[6] or 0}

def _league_label(league):
    return {"all": "Общая", "default": "Default", "quals": "QUALS"}.get(league, "Общая")

def _profile_kb(uid, current="all"):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton(("✅ " if current == "all" else "") + "📊 Общая", callback_data=f"pstats_all_{uid}"),
        types.InlineKeyboardButton(("✅ " if current == "default" else "") + "🎮 Default", callback_data=f"pstats_default_{uid}"),
        types.InlineKeyboardButton(("✅ " if current == "quals" else "") + "⭐ Quals", callback_data=f"pstats_quals_{uid}")
    )
    return kb

def _send_profile(uid, chat_id, league="all"):
    p = get_player(uid)
    if not p:
        bot.send_message(chat_id, "Игрок не найден.")
        return
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
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ АДМИНКИ
# ═══════════════════════════════════════════════════════════════════

def _unmute_player_action(admin_uid, tid):
    unmute_player(tid)
    bot.send_message(admin_uid, f"✅ Мут снят с игрока {_pname(tid)}")
    _notify(tid, "✅ Администратор снял с вас мут")

def _unban_player_action(admin_uid, tid):
    unban_player(tid)
    bot.send_message(admin_uid, f"✅ Бан снят с игрока {_pname(tid)}")
    _notify(tid, "✅ Администратор снял с вас бан")

def _clear_warns_action(admin_uid, tid):
    clear_warns(tid)
    bot.send_message(admin_uid, f"✅ Варны сброшены у игрока {_pname(tid)}")
    _notify(tid, "✅ Администратор сбросил ваши варны")

# ═══════════════════════════════════════════════════════════════════
# /START
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    uid = msg.from_user.id
    if check_ban(uid, msg.chat.id):
        return
    p = get_player(uid)
    if p and p[18]:
        bot.send_message(uid, "⚡ <b>ACTUAL FACEIT</b>", reply_markup=_main_menu_kb(uid), parse_mode="HTML")
        return
    user_flow[uid] = {"state": "reg_nick"}
    bot.send_message(uid,
                    "👋 Добро пожаловать в <b>ACTUAL FACEIT</b>!\n\n"
                    "Шаг 1: Введи свой <b>никнейм</b>:", parse_mode="HTML")

@bot.message_handler(commands=['help'])
def cmd_help(msg):
    if check_ban(msg.from_user.id, msg.chat.id):
        return
    bot.send_message(msg.chat.id,
                     "📋 <b>Команды:</b>\n"
                     "/start — меню\n/profile — профиль\n/top — топ\n"
                     "/shop — магазин\n/inv — инвентарь\n"
                     "/play — калибровочные матчи\n"
                     "/ticket <id матча> <причина> — подать жалобу\n\n"
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
    if check_ban(uid, msg.chat.id):
        return
    state = user_flow[uid]["state"]
    text = (msg.text or "").strip()

    if state == "reg_nick":
        if not (2 <= len(text) <= 20):
            bot.send_message(uid, "❌ Никнейм 2–20 символов.")
            return
        user_flow[uid] = {"state": "reg_id", "nick": text}
        bot.send_message(uid, "📋 Введи свой <b>игровой ID</b>:", parse_mode="HTML")

    elif state == "reg_id":
        if not text.isdigit():
            bot.send_message(uid, "❌ ID — только цифры.")
            return
        user_flow[uid]["game_id"] = text
        user_flow[uid]["state"] = "reg_device"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.row("MOBILE", "PC")
        bot.send_message(uid, "📱 Выбери устройство:", reply_markup=kb)

    elif state == "reg_device":
        if text not in ("MOBILE", "PC"):
            bot.send_message(uid, "❌ Выбери MOBILE или PC.")
            return
        d = user_flow.pop(uid)
        register_player(uid, d["nick"], d["game_id"], text)
        send_log(f"📝 Новый игрок: {d['nick']} (#{uid})")
        bot.send_message(uid, f"✅ Зарегистрирован как <b>{d['nick']}</b>!",
                         reply_markup=_main_menu_kb(uid), parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════
# ПРОФИЛЬ
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['profile'])
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def cmd_profile(msg):
    if not _check_reg(msg.from_user.id, msg.chat.id):
        return
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
    if check_ban(uid, msg.chat.id):
        return
    if not _check_reg(uid, msg.chat.id):
        return

    muted, until = is_muted(uid)
    if muted:
        bot.send_message(uid, f"🔇 Вы замучены! До: {until[:16]}")
        return

    p = get_player(uid)
    if is_calibrated(p):
        bot.send_message(uid, "✅ Ты уже прошел калибровку! Используй «Найти матч» для обычных игр.")
        return

    cal = calib_count(p)
    bot.send_message(uid,
                     f"📊 Калибровочный матч {cal}/{CALIB_THRESHOLD}\nОсталось: {CALIB_THRESHOLD - cal} матчей.\nИспользуй «Найти матч» для поиска.")
    _show_lobby_browser(uid, msg.chat.id, p[3] or "MOBILE", "default")

# ═══════════════════════════════════════════════════════════════════
# ТОП
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['top'])
@bot.message_handler(func=lambda m: m.text == "🏆 Топ")
def cmd_top(msg):
    if check_ban(msg.from_user.id, msg.chat.id):
        return
    img = create_top_card(get_top_players(10))
    bot.send_photo(msg.chat.id, img)

# ═══════════════════════════════════════════════════════════════════
# МАГАЗИН
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['shop'])
@bot.message_handler(func=lambda m: m.text == "🛒 Магазин")
def cmd_shop(msg):
    if check_ban(msg.from_user.id, msg.chat.id):
        return
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
    if not p:
        bot.answer_callback_query(c.id, "Ошибка")
        return
    if (p[6] or 0) < item["price"]:
        bot.answer_callback_query(c.id, f"❌ Мало монет! Нужно {item['price']}", show_alert=True)
        return
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
    if check_ban(uid, msg.chat.id):
        return
    if not _check_reg(uid, msg.chat.id):
        return
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
        bot.answer_callback_query(c.id, "Ошибка")
        return

    iname = row[2]
    itype = row[3]
    activated = row[6]

    if itype == "unwarn":
        w = get_warns(uid)
        if w == 0:
            bot.answer_callback_query(c.id, "У тебя нет варнов!", show_alert=True)
            return
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
        bot.answer_callback_query(c.id, "Уже активировано!", show_alert=True)
        return

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
    if check_ban(uid, msg.chat.id):
        return
    text = (msg.text or "").strip()
    if not (2 <= len(text) <= 20):
        bot.send_message(uid, "❌ Никнейм 2–20 символов. Попробуй ещё раз:")
        return
    old = _pname(uid)
    set_username(uid, text)
    user_flow.pop(uid, None)
    bot.send_message(uid, f"✅ Ник изменён: <b>{old}</b> → <b>{text}</b>", parse_mode="HTML")
    send_log(f"✏️ {old} (#{uid}) → ник: {text}")

# ═══════════════════════════════════════════════════════════════════
# ПОИСК МАТЧА (ЛОББИ) - 2 КОЛОНКИ
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text == "🎮 Найти матч")
def cmd_find(msg):
    uid = msg.from_user.id
    if check_ban(uid, msg.chat.id):
        return
    if not _check_reg(uid, msg.chat.id):
        return

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

    # Ряд MOBILE (5 кнопок)
    mobile_btns = []
    for slot in range(1, 6):
        key = f"{league}_MOBILE_{slot}"
        lob = active_lobbies.get(key)
        count = len(lob["players"]) if lob else 0
        st = lob["status"] if lob else "empty"
        if st == "waiting":
            em = "🟢" if count > 0 else "⚪"
        else:
            em = "🔴"
        mobile_btns.append(types.InlineKeyboardButton(f"{em}{slot}({count})", callback_data=f"join_{league}_MOBILE_{slot}"))
    kb.row(*mobile_btns)

    # Ряд PC (5 кнопок)
    pc_btns = []
    for slot in range(1, 6):
        key = f"{league}_PC_{slot}"
        lob = active_lobbies.get(key)
        count = len(lob["players"]) if lob else 0
        st = lob["status"] if lob else "empty"
        if st == "waiting":
            em = "🟢" if count > 0 else "⚪"
        else:
            em = "🔴"
        pc_btns.append(types.InlineKeyboardButton(f"{em}{slot}({count})", callback_data=f"join_{league}_PC_{slot}"))
    kb.row(*pc_btns)

    # Кнопки переключения лиг
    kb.add(
        types.InlineKeyboardButton("🎮 Default", callback_data=f"browse_default_{device}"),
        types.InlineKeyboardButton("⭐ QUALS", callback_data=f"browse_quals_{device}")
    )

    # Кнопка добавления ботов (только для админов)
    if _is_admin(uid):
        kb.add(types.InlineKeyboardButton("🤖 Добавить ботов в лобби", callback_data=f"add_bots_{league}"))

    bot.send_photo(chat_id, img,
                   caption=f"🎮 Выбери слот (Лига: {'QUALS' if league != 'default' else 'Default'})",
                   reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("browse_"))
def cb_browse(c):
    _, league, device = c.data.split("_", 2)
    bot.answer_callback_query(c.id)
    _show_lobby_browser(c.from_user.id, c.message.chat.id, device, league)

# Добавление ботов в лобби
@bot.callback_query_handler(func=lambda c: c.data.startswith("add_bots_"))
def cb_add_bots(c):
    if not _is_admin(c.from_user.id):
        bot.answer_callback_query(c.id, "Нет доступа")
        return

    league = c.data.split("_")[2]
    bot.answer_callback_query(c.id)

    kb = types.InlineKeyboardMarkup(row_width=5)
    # Ряд MOBILE
    btns = []
    for slot in range(1, 6):
        btns.append(types.InlineKeyboardButton(f"MOBILE {slot}", callback_data=f"bots_do_{league}_MOBILE_{slot}"))
    kb.row(*btns)
    # Ряд PC
    btns2 = []
    for slot in range(1, 6):
        btns2.append(types.InlineKeyboardButton(f"PC {slot}", callback_data=f"bots_do_{league}_PC_{slot}"))
    kb.row(*btns2)
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data=f"browse_default_MOBILE"))

    bot.send_message(c.from_user.id, "🤖 Выбери слот для добавления ботов:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bots_do_"))
def cb_bots_do(c):
    if not _is_admin(c.from_user.id):
        bot.answer_callback_query(c.id, "Нет доступа")
        return

    parts = c.data.split("_")
    league = parts[2]
    device = parts[3]
    slot = int(parts[4])
    key = f"{league}_{device}_{slot}"

    # Получаем всех ботов из БД
    conn = sqlite3.connect("faceit.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM players WHERE is_bot=1")
    bots = [row[0] for row in cur.fetchall()]
    conn.close()

    # Создаём лобби если не существует
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

    added = 0
    for bot_id in bots:
        if len(lob["players"]) >= 10:
            break
        if bot_id not in lob["players"]:
            lob["players"].append(bot_id)
            user_lobby[bot_id] = key
            added += 1

    bot.answer_callback_query(c.id, f"✅ Добавлено {added} ботов в лобби {device} {slot}")
    send_log(f"🤖 Админ добавил {added} ботов в лобби {key}")
    _show_lobby_browser(c.from_user.id, c.message.chat.id, "MOBILE", league)

@bot.callback_query_handler(func=lambda c: c.data.startswith("join_"))
def cb_join(c):
    parts = c.data.split("_")
    league = parts[1]
    device = parts[2]
    slot = int(parts[3])
    uid = c.from_user.id
    key = f"{league}_{device}_{slot}"
    bot.answer_callback_query(c.id)

    if check_ban(uid, c.message.chat.id):
        return

    muted, until = is_muted(uid)
    if muted:
        bot.send_message(uid, f"🔇 Вы замучены! До: {until[:16]}")
        return

    # Проверка калибровки для обычных матчей
    if league != "quals":
        p = get_player(uid)
        if not is_calibrated(p):
            cal = calib_count(p)
            bot.send_message(uid, f"❌ Нужно пройти калибровку! Осталось {CALIB_THRESHOLD - cal} матчей.\nИспользуй /play")
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
    if not lob:
        return
    if uid in lob["players"]:
        lob["players"].remove(uid)
    lob["ready"].discard(uid)
    user_lobby.pop(uid, None)
    _cancel_timer(key, uid)

def _cancel_timer(key, uid):
    tk = f"{key}_{uid}"
    t = accept_timers.pop(tk, None)
    if t:
        t.cancel()

# ═══════════════════════════════════════════════════════════════════
# ПРИНЯТИЕ МАТЧА
# ═══════════════════════════════════════════════════════════════════

def _start_accept(key):
    lob = active_lobbies.get(key)
    if not lob:
        return
    lob["status"] = "accept"
    lob["ready"] = set()
    send_log(f"⚔️ {key}: 10 игроков — Accept")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Принять матч", callback_data=f"accept_{key}"))
    for uid in lob["players"]:
        if _is_bot_player(uid):
            lob["ready"].add(uid)
            continue
        try:
            bot.send_message(uid,
                             f"⚔️ <b>Матч найден!</b>\n\n"
                             f"Лига: {lob['league'].upper()} | Слот: {lob['slot']}\n"
                             f"⏳ <b>{ACCEPT_TIMEOUT} секунд</b> чтобы принять!",
                             reply_markup=kb, parse_mode="HTML")
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
    if not lob or lob["status"] != "accept":
        return
    if uid in lob["ready"]:
        return
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
        bot.answer_callback_query(c.id, "Недоступно")
        return
    if uid not in lob["players"]:
        bot.answer_callback_query(c.id, "Ты не в этом лобби")
        return
    lob["ready"].add(uid)
    _cancel_timer(key, uid)
    bot.answer_callback_query(c.id, "✅ Принято!")
    _check_all_ready(key)

def _check_all_ready(key):
    lob = active_lobbies.get(key)
    if not lob or lob["status"] != "accept":
        return
    humans = [u for u in lob["players"] if not _is_bot_player(u)]
    if all(u in lob["ready"] for u in humans) and len(lob["players"]) == 10:
        _start_veto(key)

# ═══════════════════════════════════════════════════════════════════
# ВЕТО
# ═══════════════════════════════════════════════════════════════════

def _start_veto(key):
    lob = active_lobbies.get(key)
    if not lob:
        return
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
        try:
            bot.send_message(uid, "🟦 Ты в команде <b>CT</b>!", parse_mode="HTML")
        except:
            pass
    for uid in lob["team_t"]:
        try:
            bot.send_message(uid, "🟧 Ты в команде <b>T</b>!", parse_mode="HTML")
        except:
            pass
    send_log(f"🗺 {key}: Вето. CT: {_pname(lob['captain_ct'])} / T: {_pname(lob['captain_t'])}")
    _send_veto(key)

def _send_veto(key):
    lob = active_lobbies.get(key)
    if not lob or lob["status"] != "veto":
        return
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
    caption = (f"🗺 <b>ВЕТО</b> — Бан {lob['ban_count'] + 1}/4\n"
               f"Ход <b>{'CT' if turn == 'ct' else 'T'}</b> — {cap_name}")
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
    if not lob or lob["status"] != "veto" or not lob["map_pool"]:
        return
    _do_ban(key, random.choice(lob["map_pool"]))

@bot.callback_query_handler(func=lambda c: c.data.startswith("ban_"))
def cb_ban(c):
    parts = c.data.split("_", 2)
    key = parts[1]
    mname = parts[2]
    uid = c.from_user.id
    lob = active_lobbies.get(key)
    if not lob or lob["status"] != "veto":
        bot.answer_callback_query(c.id, "Вето недоступно")
        return
    turn = lob["veto_turn"]
    cap_id = lob["captain_ct"] if turn == "ct" else lob["captain_t"]
    if uid != cap_id:
        bot.answer_callback_query(c.id, "Сейчас не твой ход!")
        return
    if mname not in lob["map_pool"]:
        bot.answer_callback_query(c.id, "Карта уже забанена")
        return
    bot.answer_callback_query(c.id)
    _do_ban(key, mname)

def _do_ban(key, mname):
    lob = active_lobbies.get(key)
    if not lob:
        return
    turn = lob["veto_turn"]
    lob["bans"].append({"map": mname, "by": turn})
    lob["map_pool"].remove(mname)
    lob["ban_count"] += 1
    cap_name = _pname(lob["captain_ct"] if turn == "ct" else lob["captain_t"])
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
    if not lob:
        return
    lob["status"] = "active"
    league = lob["league"]
    mid = save_match(key, map_name, lob["team_ct"], lob["team_t"], league)
    match = {
        "match_id": mid, "lobby_key": key, "map_name": map_name,
        "league": league, "team_ct": list(lob["team_ct"]),
        "team_t": list(lob["team_t"]),
        "captain_ct": lob["captain_ct"], "captain_t": lob["captain_t"],
        "status": "active", "screenshot_file_id": None,
        "ready": set()
    }
    active_matches[mid] = match
    lob["match_id"] = mid
    for uid in lob["team_ct"] + lob["team_t"]:
        user_match[uid] = mid
    ct_rows = [get_player(u) for u in lob["team_ct"]]
    t_rows = [get_player(u) for u in lob["team_t"]]
    img = create_match_start_card(mid, map_name, league,
                                  lob["team_ct"], lob["team_t"], ct_rows, t_rows)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📸 Отправить результат", callback_data=f"result_{mid}"))
    for uid in lob["team_ct"] + lob["team_t"]:
        side = "CT" if uid in lob["team_ct"] else "T"
        try:
            bot.send_photo(uid, img,
                           caption=f"⚔️ <b>Матч #{mid} начался!</b>\nКарта: {map_name} | Команда: <b>{side}</b>",
                           reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
    send_log(f"⚔️ Матч #{mid} | {map_name} | {key}")

# ═══════════════════════════════════════════════════════════════════
# РЕЗУЛЬТАТ МАТЧА (сокращённо)
# ═══════════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data.startswith("result_"))
def cb_result(c):
    mid = int(c.data.split("_")[1])
    uid = c.from_user.id
    if user_match.get(uid) != mid:
        bot.answer_callback_query(c.id, "Ты не в этом матче")
        return
    bot.answer_callback_query(c.id)
    screenshot_pend[uid] = mid
    bot.send_message(uid, "📸 Отправь <b>фото-скриншот</b> результата:", parse_mode="HTML")

@bot.message_handler(content_types=['photo'], func=lambda m: m.from_user.id in screenshot_pend)
def handle_screenshot(msg):
    uid = msg.from_user.id
    mid = screenshot_pend.pop(uid, None)
    if not mid:
        return
    match = active_matches.get(mid)
    if not match:
        return
    file_id = msg.photo[-1].file_id
    match["screenshot_file_id"] = file_id
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✏️ Ввести статистику", callback_data=f"enterstats_{mid}"))
    caption = (f"📸 Скриншот матча <b>#{mid}</b>\n"
               f"Карта: {match['map_name']} | Лига: {match['league']}\n\n"
               f"CT: {', '.join(_pname(u) for u in match['team_ct'])}\n"
               f"T: {', '.join(_pname(u) for u in match['team_t'])}")
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
        bot.answer_callback_query(c.id, "Нет доступа")
        return
    bot.answer_callback_query(c.id)
    match = active_matches.get(mid, {})
    ct_names = " | ".join(_pname(u) for u in match.get("team_ct", []))
    t_names = " | ".join(_pname(u) for u in match.get("team_t", []))
    stats_pending[uid] = mid
    bot.send_message(uid,
                     f"✏️ <b>Статистика матча #{mid}</b>\n\n"
                     f"<b>CT:</b> {ct_names}\n<b>T:</b> {t_names}\n\n"
                     f"Формат:\n"
                     f"<code>13:11\nCT\nID K A D\nID K A D\n...(5 CT)\nT\nID K A D\n...(5 T)</code>\n\n"
                     f"• Счёт: победители:проигравшие\n"
                     f"• ID = telegram user_id",
                     parse_mode="HTML")

@bot.message_handler(func=lambda m: m.from_user.id in stats_pending and not user_flow.get(m.from_user.id, {}).get("state", "").startswith("adm_"))
def handle_stats_input(msg):
    uid = msg.from_user.id
    mid = stats_pending.pop(uid, None)
    if not mid:
        return
    match = active_matches.get(mid)
    if not match:
        bot.send_message(uid, "❌ Матч не найден.")
        return
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
    if not match:
        return
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
            kd_v = round(k / d, 2) if d > 0 else float(k)
            rating = round(kd_v * 0.85 + a * 0.02, 2)
            impact = round(kd_v * 0.9, 2)
            save_match_player_stats(mid, pid, side, k, d, a, rating, impact, kd_v)
            coin_txt = f"{'x2! ' if x2 else ''}💰 +{coins} монет"
            calib_txt = (f"\n📊 Калибровка: {calib}/{CALIB_THRESHOLD}"
                         if calib < CALIB_THRESHOLD else f"\n📊 ELO: {new_elo} → LV{new_lv}")
            try:
                bot.send_message(pid,
                                 f"{'🏆 Победа!' if won else '💀 Поражение'}\n"
                                 f"K: {k}  A: {a}  D: {d}\n"
                                 f"{coin_txt}{calib_txt}")
            except Exception:
                pass
            card_list.append((p, k, d, a))

    _process(ct_entries[:5], "ct", ct_card_data)
    _process(t_entries[:5], "t", t_card_data)

    img = create_match_result_card(mid, map_name, league, score_ct, score_t, winner, ct_card_data, t_card_data)

    for uid in match["team_ct"] + match["team_t"]:
        try:
            bot.send_photo(uid, img,
                           caption=(f"📊 <b>Результат матча #{mid}</b>\n"
                                    f"{'🏆 CT победили' if winner == 'ct' else '🏆 T победили'} "
                                    f"{score_ct}:{score_t}"),
                           parse_mode="HTML")
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
# СИСТЕМА ЖАЛОБ/ТИКЕТОВ
# ═══════════════════════════════════════════════════════════════════

def create_ticket(user_id, match_id, reason):
    conn = sqlite3.connect("faceit.db")
    cur = conn.cursor()
    created_at = datetime.now().isoformat()
    cur.execute("""
        INSERT INTO tickets(user_id, match_id, reason, status, created_at)
        VALUES(?,?,?,?,?)
    """, (user_id, match_id, reason, 'open', created_at))
    ticket_id = cur.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

def get_tickets(status=None):
    conn = sqlite3.connect("faceit.db")
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM tickets WHERE status=?", (status,))
    else:
        cur.execute("SELECT * FROM tickets ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_ticket(ticket_id):
    conn = sqlite3.connect("faceit.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,))
    row = cur.fetchone()
    conn.close()
    return row

def resolve_ticket(ticket_id, admin_id, admin_comment):
    conn = sqlite3.connect("faceit.db")
    cur = conn.cursor()
    resolved_at = datetime.now().isoformat()
    cur.execute("""
        UPDATE tickets SET 
            status='resolved', 
            resolved_by=?, 
            resolved_at=?,
            admin_comment=?
        WHERE id=?
    """, (admin_id, resolved_at, admin_comment, ticket_id))
    conn.commit()
    conn.close()

def reset_season():
    conn = sqlite3.connect("faceit.db")
    cur = conn.cursor()
    cur.execute("UPDATE players SET elo=1000, level=1, calibration_matches=0")
    cur.execute("DELETE FROM league_stats")
    conn.commit()
    conn.close()

def get_season_stats():
    conn = sqlite3.connect("faceit.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM players WHERE registered=1")
    total_players = cur.fetchone()[0]
    cur.execute("SELECT AVG(elo) FROM players WHERE registered=1 AND is_bot=0")
    avg_elo = cur.fetchone()[0] or 1000
    cur.execute("SELECT username, elo FROM players WHERE registered=1 AND is_bot=0 ORDER BY elo DESC LIMIT 1")
    top_player = cur.fetchone()
    conn.close()
    return {
        "total_players": total_players,
        "avg_elo": int(avg_elo),
        "top_player": top_player[0] if top_player else "None",
        "top_elo": top_player[1] if top_player else 0
    }

@bot.message_handler(commands=['ticket'])
def cmd_ticket(msg):
    uid = msg.from_user.id
    if not _check_reg(uid, msg.chat.id):
        return

    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(msg, "❌ Формат: /ticket <ID матча> <причина>\nПример: /ticket 12345 Неправильный результат матча")
        return

    try:
        match_id = int(parts[0].split()[1] if len(parts[0].split()) > 1 else parts[0].split()[0])
    except:
        bot.reply_to(msg, "❌ Укажите ID матча (число)")
        return

    reason = parts[1] if len(parts) > 1 else "Не указана причина"

    ticket_id = create_ticket(uid, match_id, reason)
    bot.reply_to(msg, f"✅ Жалоба #{ticket_id} создана! Администратор рассмотрит её в ближайшее время.")
    send_log(f"📋 Новая жалоба #{ticket_id} от {_pname(uid)} на матч #{match_id}")

# ═══════════════════════════════════════════════════════════════════
# АДМИН ПАНЕЛЬ (УПРАВЛЕНИЕ ИГРОКОМ)
# ═══════════════════════════════════════════════════════════════════

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
            f"Мут: {'Да (до ' + until[:16] + ')' if muted_f else 'Нет'}\n"
            f"Бан: {'Да' if banned_f else 'Нет'}")

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✏️ Изменить ник", callback_data=f"mg_nick_{tid}"),
        types.InlineKeyboardButton("🔢 Game ID", callback_data=f"mg_gameid_{tid}"),
        types.InlineKeyboardButton("💰 Монеты", callback_data=f"mg_coins_{tid}"),
        types.InlineKeyboardButton("📊 ELO", callback_data=f"mg_elo_{tid}"),
        types.InlineKeyboardButton("⚠️ Выдать варн", callback_data=f"mg_warn_{tid}"),
        types.InlineKeyboardButton("🔇 Выдать мут", callback_data=f"mg_mute_{tid}"),
        types.InlineKeyboardButton("🚫 Выдать бан", callback_data=f"mg_ban_{tid}"),
        types.InlineKeyboardButton("✅ Снять мут", callback_data=f"mg_unmute_{tid}"),
        types.InlineKeyboardButton("✅ Снять бан", callback_data=f"mg_unban_{tid}"),
        types.InlineKeyboardButton("🔄 Сбросить варны", callback_data=f"mg_clrwarn_{tid}"),
    )
    bot.send_message(admin_uid, text, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("mg_"))
def cb_manage(c):
    parts = c.data.split("_", 2)
    if len(parts) < 3:
        bot.answer_callback_query(c.id, "Ошибка")
        return
    
    action = parts[1]
    tid = int(parts[2])
    uid = c.from_user.id
    
    if not _is_admin(uid):
        bot.answer_callback_query(c.id, "Нет доступа")
        return
    
    manage_target[uid] = tid
    bot.answer_callback_query(c.id)

    # Мгновенные действия (без ввода текста)
    INSTANT = {
        "unmute": lambda: (_unmute_player_action(uid, tid), _manage_panel(uid, tid)),
        "unban": lambda: (_unban_player_action(uid, tid), _manage_panel(uid, tid)),
        "clrwarn": lambda: (_clear_warns_action(uid, tid), _manage_panel(uid, tid)),
    }
    
    if action in INSTANT:
        INSTANT[action]()
        return

    # Действия с вводом текста
    INPUT_STATES = {
        "nick": {"state": "adm_mg_nick", "prompt": "✏️ Введи новый никнейм (2-20 символов):"},
        "gameid": {"state": "adm_mg_gameid", "prompt": "🔢 Введи новый Game ID:"},
        "coins": {"state": "adm_mg_coins", "prompt": "💰 Введи количество монет:"},
        "elo": {"state": "adm_mg_elo", "prompt": "📊 Введи новое значение ELO:"},
        "warn": {"state": "adm_mg_warn", "prompt": "⚠️ Сколько варнов выдать? (1-3):"},
        "mute": {"state": "adm_mg_mute", "prompt": "🔇 На сколько часов замутить? (по умолч. 2):"},
        "ban": {"state": "adm_mg_ban", "prompt": "🚫 Введи данные для бана в формате:\n\n<code>дни | причина</code>\n\nПримеры:\n<code>7 | Оскорбления</code> - бан на 7 дней\n<code>0 | Нарушение правил</code> - бан навсегда", parse_mode="HTML"},
    }
    
    if action in INPUT_STATES:
        info = INPUT_STATES[action]
        user_flow[uid] = {"state": info["state"], "target": tid}
        bot.send_message(uid, info["prompt"], parse_mode="HTML" if "parse_mode" in info else None)

@bot.message_handler(func=lambda m: user_flow.get(m.from_user.id, {}).get("state", "").startswith("adm_mg_"))
def handle_admin_mg_input(msg):
    uid = msg.from_user.id
    state = user_flow.get(uid, {}).get("state", "")
    text = (msg.text or "").strip()
    
    if not _is_admin(uid):
        user_flow.pop(uid, None)
        return
    
    flow = user_flow.get(uid, {})
    tid = flow.get("target")
    
    if not tid:
        bot.send_message(uid, "❌ Ошибка: цель не найдена")
        user_flow.pop(uid, None)
        return
    
    try:
        # ── Изменение ника ─────────────────────────────────────────────
        if state == "adm_mg_nick":
            if not (2 <= len(text) <= 20):
                bot.send_message(uid, "❌ Никнейм должен быть 2-20 символов. Попробуй ещё раз:")
                return
            old_name = _pname(tid)
            set_username(tid, text)
            bot.send_message(uid, f"✅ Ник изменён: <b>{old_name}</b> → <b>{text}</b>", parse_mode="HTML")
            _notify(tid, f"✏️ Администратор изменил ваш никнейм: {old_name} → {text}")
            send_log(f"✏️ {_pname(uid)} изменил ник {old_name} → {text}")
        
        # ── Изменение Game ID ─────────────────────────────────────────
        elif state == "adm_mg_gameid":
            if not text.isdigit():
                bot.send_message(uid, "❌ Game ID должен содержать только цифры. Попробуй ещё раз:")
                return
            set_game_id(tid, text)
            bot.send_message(uid, f"✅ Game ID изменён на: {text}")
            _notify(tid, f"🔢 Администратор изменил ваш Game ID на: {text}")
        
        # ── Изменение монет ───────────────────────────────────────────
        elif state == "adm_mg_coins":
            if not text.isdigit():
                bot.send_message(uid, "❌ Введи число (количество монет):")
                return
            set_coins(tid, int(text))
            bot.send_message(uid, f"✅ Монеты установлены: {text}")
            _notify(tid, f"💰 Администратор изменил количество монет: {text}")
        
        # ── Изменение ELO ─────────────────────────────────────────────
        elif state == "adm_mg_elo":
            if not text.isdigit():
                bot.send_message(uid, "❌ Введи число (ELO):")
                return
            e = int(text)
            set_elo(tid, e)
            set_level(tid, elo_to_level(e))
            bot.send_message(uid, f"✅ ELO установлено: {e} (уровень {elo_to_level(e)})")
            _notify(tid, f"📊 Администратор изменил ваш ELO на: {e}")
        
        # ── Выдача варна ──────────────────────────────────────────────
        elif state == "adm_mg_warn":
            if not text.isdigit():
                bot.send_message(uid, "❌ Введи число (количество варнов):")
                return
            cnt = min(int(text), 3)
            w = 0
            for _ in range(cnt):
                w = add_warn(tid, reason="Выдан администратором", admin_id=uid)
            bot.send_message(uid, f"✅ Выдано варнов: {cnt}. Теперь у игрока {w}/3")
            _notify(tid, f"⚠️ Администратор выдал вам {cnt} варн(а)! Всего: {w}/3")
        
        # ── Выдача мута ───────────────────────────────────────────────
        elif state == "adm_mg_mute":
            h = int(text) if text.isdigit() else 2
            until = mute_player(tid, h, reason="По решению администратора", admin_id=uid)
            bot.send_message(uid, f"✅ Мут на {h} час(ов). До: {until[:16]}")
            _notify(tid, f"🔇 Администратор замутил вас на {h} час(ов)")
        
        # ── Выдача бана ───────────────────────────────────────────────
        elif state == "adm_mg_ban":
            parts = text.split("|")
            if len(parts) < 2:
                bot.send_message(uid, "❌ Неверный формат!\nИспользуй: <code>дни | причина</code>", parse_mode="HTML")
                user_flow[uid] = {"state": "adm_mg_ban", "target": tid}
                return
            
            days_str = parts[0].strip()
            reason = parts[1].strip() if len(parts) > 1 else "Нарушение правил"
            
            if not days_str.isdigit():
                bot.send_message(uid, "❌ Дни должны быть числом! 0 = навсегда")
                user_flow[uid] = {"state": "adm_mg_ban", "target": tid}
                return
            
            days = int(days_str)
            if days == 0:
                days = None
            
            ban_player(tid, days=days, reason=reason, admin_id=uid)
            ban_text = f"на {days} дней" if days else "НАВСЕГДА"
            bot.send_message(uid, f"✅ Бан выдан: {ban_text}\nПричина: {reason}")
            _notify(tid, f"🚫 Администратор заблокировал вас {ban_text}\nПричина: {reason}")
            send_log(f"🚫 {_pname(uid)} выдал бан {_pname(tid)} | {ban_text} | {reason}")
    
    except Exception as e:
        bot.send_message(uid, f"❌ Ошибка: {e}")
    
    user_flow.pop(uid, None)
    _manage_panel(uid, tid)

# ═══════════════════════════════════════════════════════════════════
# ОСНОВНАЯ АДМИН ПАНЕЛЬ
# ═══════════════════════════════════════════════════════════════════

def _admin_panel(uid, chat_id):
    is_creator = (uid == 8521250777)

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👤 Найти игрока", callback_data="adm_find"),
        types.InlineKeyboardButton("🤖 Добавить бота", callback_data="adm_addbot"),
        types.InlineKeyboardButton("📋 Лобби", callback_data="adm_lobbies"),
        types.InlineKeyboardButton("⚔️ Матчи", callback_data="adm_matches"),
    )

    if is_creator:
        kb.add(
            types.InlineKeyboardButton("🏆 Управление сезонами", callback_data="adm_season"),
            types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_mailing"),
            types.InlineKeyboardButton("🎮 Управление матчами", callback_data="adm_match_manage"),
            types.InlineKeyboardButton("📋 Жалобы/Тикеты", callback_data="adm_tickets"),
        )

    bot.send_message(chat_id, "⚙️ <b>Панель администратора</b>", reply_markup=kb, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "⚙️ Админ панель")
@bot.message_handler(commands=['admin'])
def cmd_admin(msg):
    if not _is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "🚫 Нет доступа.")
        return
    _admin_panel(msg.from_user.id, msg.chat.id)

@bot.callback_query_handler(func=lambda c: c.data == "adm_lobbies")
def cb_lobbies_info(c):
    if not _is_admin(c.from_user.id):
        return
    bot.answer_callback_query(c.id)
    text = "📋 <b>Лобби:</b>\n"
    for k, l in active_lobbies.items():
        text += f"• {k} [{len(l['players'])}/10] — {l['status']}\n"
    if not active_lobbies:
        text += "Нет активных."
    bot.send_message(c.from_user.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "adm_matches")
def cb_matches_info(c):
    if not _is_admin(c.from_user.id):
        return
    bot.answer_callback_query(c.id)
    text = "⚔️ <b>Матчи:</b>\n"
    for mid, m in active_matches.items():
        text += f"• #{mid} {m['map_name']} | {m['league']}\n"
    if not active_matches:
        text += "Нет активных."
    bot.send_message(c.from_user.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "adm_find")
def cb_adm_find(c):
    if not _is_admin(c.from_user.id):
        return
    bot.answer_callback_query(c.id)
    user_flow[c.from_user.id] = {"state": "adm_find_player"}
    bot.send_message(c.from_user.id, "👤 Введи ID, @ник или Game ID игрока:")

@bot.callback_query_handler(func=lambda c: c.data == "adm_addbot")
def cb_adm_addbot_ui(c):
    if not _is_admin(c.from_user.id):
        return
    bot.answer_callback_query(c.id)
    user_flow[c.from_user.id] = {"state": "adm_bot_input"}
    bot.send_message(c.from_user.id,
                     "🤖 Формат: <code>Имя GameID Device</code>\n"
                     "Пример: <code>BotNick 9999 PC</code>", parse_mode="HTML")

@bot.message_handler(func=lambda m: user_flow.get(m.from_user.id, {}).get("state", "").startswith("adm_") and user_flow.get(m.from_user.id, {}).get("state") not in ["adm_mg_nick", "adm_mg_gameid", "adm_mg_coins", "adm_mg_elo", "adm_mg_warn", "adm_mg_mute", "adm_mg_ban"])
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

# ═══════════════════════════════════════════════════════════════════
# УПРАВЛЕНИЕ СЕЗОНАМИ (только создатель)
# ═══════════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data == "adm_season")
def cb_season_menu(c):
    if c.from_user.id != 8521250777:
        bot.answer_callback_query(c.id, "❌ Доступно только создателю бота")
        return

    stats = get_season_stats()

    text = (f"🏆 <b>Управление сезонами</b>\n\n"
            f"📊 <b>Статистика текущего сезона</b>\n"
            f"👥 Всего игроков: {stats['total_players']}\n"
            f"📈 Средний ELO: {stats['avg_elo']}\n"
            f"👑 Топ игрок: {stats['top_player']} ({stats['top_elo']} ELO)\n\n"
            f"⚠️ <b>Внимание!</b> Сброс сезона обнулит ELO всем игрокам до 1000")

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔄 СБРОСИТЬ СЕЗОН", callback_data="season_reset_confirm"),
        types.InlineKeyboardButton("📊 Статистика сезона", callback_data="season_stats"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin")
    )

    bot.send_message(c.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "season_reset_confirm")
def cb_season_reset_confirm(c):
    if c.from_user.id != 8521250777:
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ ДА, СБРОСИТЬ", callback_data="season_reset_do"),
        types.InlineKeyboardButton("❌ ОТМЕНА", callback_data="adm_season")
    )
    bot.send_message(c.message.chat.id, "⚠️ <b>ПОДТВЕРЖДЕНИЕ</b>\nВы уверены, что хотите сбросить сезон?\nЭто действие НЕЛЬЗЯ отменить!", reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "season_reset_do")
def cb_season_reset_do(c):
    if c.from_user.id != 8521250777:
        return
    reset_season()
    bot.send_message(c.message.chat.id, "✅ <b>Сезон сброшен!</b>\nELO всех игроков установлен на 1000", parse_mode="HTML")
    send_log("🔄 Сезон был сброшен администратором")

@bot.callback_query_handler(func=lambda c: c.data == "season_stats")
def cb_season_stats(c):
    if c.from_user.id != 8521250777:
        return
    stats = get_season_stats()
    text = (f"📊 <b>Детальная статистика сезона</b>\n\n"
            f"👥 Всего игроков: {stats['total_players']}\n"
            f"📈 Средний ELO: {stats['avg_elo']}\n"
            f"👑 Топ игрок: {stats['top_player']} ({stats['top_elo']} ELO)\n\n"
            f"🎮 <b>Активные матчи:</b> {len(active_matches)}\n"
            f"🔄 <b>Активные лобби:</b> {len(active_lobbies)}")
    bot.send_message(c.message.chat.id, text, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════
# РАССЫЛКА (только создатель)
# ═══════════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data == "adm_mailing")
def cb_mailing_menu(c):
    if c.from_user.id != 8521250777:
        bot.answer_callback_query(c.id, "❌ Доступно только создателю бота")
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("📢 Рассылка всем", callback_data="mailing_all"),
        types.InlineKeyboardButton("👥 Рассылка онлайн", callback_data="mailing_online"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin")
    )
    bot.send_message(c.message.chat.id, "📢 <b>Рассылка сообщений</b>\n\nВыберите тип рассылки:", reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("mailing_"))
def cb_mailing_type(c):
    if c.from_user.id != 8521250777:
        return

    mailing_type = c.data.split("_")[1]
    user_flow[c.from_user.id] = {"state": f"mailing_{mailing_type}"}
    bot.send_message(c.message.chat.id, "📝 Введите текст для рассылки:\n(Можно использовать HTML теги)")

@bot.message_handler(func=lambda m: user_flow.get(m.from_user.id, {}).get("state", "").startswith("mailing_"))
def handle_mailing_input(msg):
    uid = msg.from_user.id
    if uid != 8521250777:
        user_flow.pop(uid, None)
        return

    state = user_flow[uid]["state"]
    text = msg.text

    user_flow[uid] = {"state": f"mailing_confirm_{state.split('_')[1]}", "text": text}

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ ОТПРАВИТЬ", callback_data="mailing_send"),
        types.InlineKeyboardButton("❌ ОТМЕНА", callback_data="back_to_admin")
    )

    bot.send_message(uid, f"📢 <b>Предпросмотр рассылки</b>\n\n{text}\n\nОтправить?", reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "mailing_send")
def cb_mailing_send(c):
    uid = c.from_user.id
    if uid != 8521250777:
        return

    flow = user_flow.get(uid, {})
    if not flow:
        return

    mailing_type = flow["state"].split("_")[2]
    text = flow.get("text", "")

    conn = sqlite3.connect("faceit.db")
    cur = conn.cursor()

    if mailing_type == "all":
        cur.execute("SELECT user_id FROM players WHERE registered=1")
        rows = cur.fetchall()
    else:
        online_users = set(user_lobby.keys()) | set(user_match.keys())
        if not online_users:
            bot.send_message(uid, "❌ Нет активных игроков")
            return
        rows = [(uid,) for uid in online_users]

    conn.close()

    sent = 0
    for row in rows:
        try:
            bot.send_message(row[0], f"📢 <b>РАССЫЛКА ОТ АДМИНИСТРАЦИИ</b>\n\n{text}", parse_mode="HTML")
            sent += 1
        except:
            pass

    bot.send_message(uid, f"✅ Рассылка отправлена {sent} игрокам")
    send_log(f"📢 Админ отправил рассылку ({sent} получателей)")
    user_flow.pop(uid, None)

# ═══════════════════════════════════════════════════════════════════
# УПРАВЛЕНИЕ МАТЧАМИ
# ═══════════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data == "adm_match_manage")
def cb_match_manage(c):
    if c.from_user.id != 8521250777:
        bot.answer_callback_query(c.id, "❌ Доступно только создателю бота")
        return

    text = "🎮 <b>Управление активными матчами</b>\n\n"
    if not active_matches:
        text += "Нет активных матчей"
    else:
        for mid, match in active_matches.items():
            text += f"• #{mid} | {match['map_name']} | {match['league']}\n"

    kb = types.InlineKeyboardMarkup()
    for mid in active_matches.keys():
        kb.add(types.InlineKeyboardButton(f"🎮 Матч #{mid}", callback_data=f"match_manage_{mid}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin"))

    bot.send_message(c.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("match_manage_"))
def cb_match_manage_action(c):
    mid = int(c.data.split("_")[2])
    match = active_matches.get(mid)
    if not match:
        bot.answer_callback_query(c.id, "Матч не найден")
        return

    text = (f"🎮 <b>Матч #{mid}</b>\n"
            f"Карта: {match['map_name']}\n"
            f"Лига: {match['league']}\n"
            f"CT: {', '.join(_pname(u) for u in match['team_ct'])}\n"
            f"T: {', '.join(_pname(u) for u in match['team_t'])}\n"
            f"Статус: {match['status']}")

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("❌ Отменить матч", callback_data=f"match_cancel_{mid}"),
        types.InlineKeyboardButton("🚀 Форс-старт", callback_data=f"match_forcestart_{mid}"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="adm_match_manage")
    )

    bot.send_message(c.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("match_cancel_"))
def cb_match_cancel(c):
    mid = int(c.data.split("_")[2])
    match = active_matches.get(mid)
    if not match:
        return

    key = match.get("lobby_key")
    if key and key in active_lobbies:
        for uid in active_lobbies[key]["players"]:
            user_match.pop(uid, None)
            user_lobby.pop(uid, None)
        del active_lobbies[key]

    finalize_match(mid, "cancelled")
    active_matches.pop(mid, None)

    bot.answer_callback_query(c.id, f"✅ Матч #{mid} отменён")
    send_log(f"❌ Матч #{mid} был отменён администратором")

@bot.callback_query_handler(func=lambda c: c.data.startswith("match_forcestart_"))
def cb_match_forcestart(c):
    mid = int(c.data.split("_")[2])
    match = active_matches.get(mid)
    if not match:
        return

    for uid in match["team_ct"] + match["team_t"]:
        if uid not in match.get("ready", set()):
            match["ready"].add(uid)

    bot.answer_callback_query(c.id, f"✅ Матч #{mid} принудительно запущен")
    send_log(f"🚀 Матч #{mid} принудительно запущен администратором")

# ═══════════════════════════════════════════════════════════════════
# ЖАЛОБЫ/ТИКЕТЫ (админ)
# ═══════════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data == "adm_tickets")
def cb_tickets_menu(c):
    if c.from_user.id != 8521250777:
        bot.answer_callback_query(c.id, "❌ Доступно только создателю бота")
        return

    tickets = get_tickets(status="open")

    if not tickets:
        bot.send_message(c.message.chat.id, "📋 Нет открытых жалоб")
        return

    kb = types.InlineKeyboardMarkup(row_width=1)
    for ticket in tickets:
        ticket_id, user_id, match_id, reason, status, created_at, _, _, _ = ticket
        username = _pname(user_id)
        kb.add(types.InlineKeyboardButton(f"📌 #{ticket_id} | {username} | матч #{match_id}", callback_data=f"ticket_view_{ticket_id}"))

    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin"))

    bot.send_message(c.message.chat.id, f"📋 <b>Открытые жалобы ({len(tickets)})</b>", reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("ticket_view_"))
def cb_ticket_view(c):
    ticket_id = int(c.data.split("_")[2])
    ticket = get_ticket(ticket_id)

    if not ticket:
        bot.answer_callback_query(c.id, "Тикет не найден")
        return

    tid, user_id, match_id, reason, status, created_at, resolved_by, resolved_at, admin_comment = ticket

    text = (f"📋 <b>Жалоба #{tid}</b>\n\n"
            f"👤 Игрок: {_pname(user_id)} (#{user_id})\n"
            f"🎮 Матч: #{match_id}\n"
            f"📝 Причина: {reason}\n"
            f"📅 Создана: {created_at[:16]}\n"
            f"🔘 Статус: {'🟡 Открыта' if status == 'open' else '✅ Закрыта'}")

    kb = types.InlineKeyboardMarkup()
    if status == "open":
        kb.add(types.InlineKeyboardButton("✅ Закрыть жалобу", callback_data=f"ticket_resolve_{tid}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="adm_tickets"))

    bot.send_message(c.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("ticket_resolve_"))
def cb_ticket_resolve(c):
    ticket_id = int(c.data.split("_")[2])
    user_flow[c.from_user.id] = {"state": f"ticket_comment_{ticket_id}"}
    bot.send_message(c.message.chat.id, "📝 Введите комментарий по жалобе (для игрока):")

@bot.message_handler(func=lambda m: user_flow.get(m.from_user.id, {}).get("state", "").startswith("ticket_comment_"))
def handle_ticket_comment(msg):
    uid = msg.from_user.id
    if uid != 8521250777:
        return

    ticket_id = int(user_flow[uid]["state"].split("_")[2])
    comment = msg.text

    resolve_ticket(ticket_id, uid, comment)

    ticket = get_ticket(ticket_id)
    if ticket:
        user_id = ticket[1]
        match_id = ticket[2]
        try:
            bot.send_message(user_id,
                             f"✅ <b>Ваша жалоба #{ticket_id} на матч #{match_id} рассмотрена!</b>\n\nОтвет администратора:\n{comment}",
                             parse_mode="HTML")
        except:
            pass

    bot.send_message(uid, f"✅ Жалоба #{ticket_id} закрыта! Игрок уведомлён.")
    send_log(f"✅ Жалоба #{ticket_id} закрыта администратором")
    user_flow.pop(uid, None)

# ═══════════════════════════════════════════════════════════════════
# КНОПКА ВОЗВРАТА
# ═══════════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data == "back_to_admin")
def cb_back_to_admin(c):
    _admin_panel(c.from_user.id, c.message.chat.id)

# ═══════════════════════════════════════════════════════════════════
# ОБЫЧНЫЕ АДМИН-КОМАНДЫ
# ═══════════════════════════════════════════════════════════════════

def _resolve(msg):
    parts = msg.text.split()
    q = parts[1].strip() if len(parts) > 1 else ""
    if q.startswith("@"):
        return get_player_by_username(q[1:])
    if q.isdigit():
        return get_player(int(q))
    return None

@bot.message_handler(commands=['manage'])
def cmd_manage(msg):
    if not _is_admin(msg.from_user.id):
        return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(msg, "Использование: /manage ID или @ник")
        return
    q = parts[1].strip()
    target = None
    if q.startswith("@"):
        target = get_player_by_username(q[1:])
    elif q.isdigit():
        target = get_player(int(q))
    if not target:
        bot.reply_to(msg, "❌ Не найден")
        return
    _manage_panel(msg.from_user.id, target[0])

@bot.message_handler(commands=['warn'])
def cmd_warn(msg):
    if not _is_admin(msg.from_user.id):
        return
    t = _resolve(msg)
    if not t:
        bot.reply_to(msg, "❌ Не найден")
        return
    w = add_warn(t[0], reason="Выдан администратором", admin_id=msg.from_user.id)
    bot.reply_to(msg, f"⚠️ Варн {t[1]}. Итого: {w}/3")
    _notify(t[0], f"⚠️ Вам выдан варн! Итого: {w}/3")

@bot.message_handler(commands=['unwarn'])
def cmd_unwarn(msg):
    if not _is_admin(msg.from_user.id):
        return
    t = _resolve(msg)
    if not t:
        bot.reply_to(msg, "❌ Не найден")
        return
    w = remove_warn(t[0])
    bot.reply_to(msg, f"✅ Варн снят у {t[1]}. Осталось: {w}")

@bot.message_handler(commands=['mute'])
def cmd_mute(msg):
    if not _is_admin(msg.from_user.id):
        return
    t = _resolve(msg)
    if not t:
        bot.reply_to(msg, "❌ Не найден")
        return
    parts = msg.text.split()
    h = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 2
    until = mute_player(t[0], h, reason="По решению администратора", admin_id=msg.from_user.id)
    bot.reply_to(msg, f"🔇 {t[1]} замучен на {h}ч")
    _notify(t[0], f"🔇 Вы замучены на {h} часов администратором")

@bot.message_handler(commands=['unmute'])
def cmd_unmute(msg):
    if not _is_admin(msg.from_user.id):
        return
    t = _resolve(msg)
    if not t:
        bot.reply_to(msg, "❌ Не найден")
        return
    unmute_player(t[0])
    bot.reply_to(msg, f"✅ Мут снят с {t[1]}")
    _notify(t[0], "✅ Администратор снял с вас мут")

@bot.message_handler(commands=['ban'])
def cmd_ban(msg):
    if not _is_admin(msg.from_user.id):
        return
    t = _resolve(msg)
    if not t:
        bot.reply_to(msg, "❌ Не найден")
        return
    parts = msg.text.split()
    days = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
    reason = " ".join(parts[3:]) if len(parts) > 3 else "Нарушение правил"
    ban_player(t[0], days=days, reason=reason, admin_id=msg.from_user.id)
    if days:
        bot.reply_to(msg, f"🚫 {t[1]} забанен на {days} дней")
        _notify(t[0], f"🚫 Вы забанены на {days} дней. Причина: {reason} (Администратор: {_pname(msg.from_user.id)})")
    else:
        bot.reply_to(msg, f"🚫 {t[1]} забанен НАВСЕГДА")
        _notify(t[0], f"🚫 Вы забанены НАВСЕГДА. Причина: {reason} (Администратор: {_pname(msg.from_user.id)})")
    send_log(f"🚫 Бан {t[1]} от {_pname(msg.from_user.id)}")

@bot.message_handler(commands=['unban'])
def cmd_unban(msg):
    if not _is_admin(msg.from_user.id):
        return
    t = _resolve(msg)
    if not t:
        bot.reply_to(msg, "❌ Не найден")
        return
    unban_player(t[0])
    bot.reply_to(msg, f"✅ Бан снят с {t[1]}")
    _notify(t[0], "✅ Администратор снял с вас бан")

@bot.message_handler(commands=['addbot'])
def cmd_addbot(msg):
    if not _is_admin(msg.from_user.id):
        return
    parts = msg.text.split()
    if len(parts) < 3:
        bot.reply_to(msg, "Формат: /addbot Имя GameID [Device]")
        return
    bdev = parts[3] if len(parts) > 3 else "PC"
    buid = random.randint(10000000, 99999999)
    register_bot(buid, parts[1], parts[2], bdev)
    bot.reply_to(msg, f"✅ Бот <b>{parts[1]}</b> создан, UID: {buid}", parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("⚡ ACTUAL FACEIT Bot запущен!")
    bot.infinity_polling(skip_pending=True)