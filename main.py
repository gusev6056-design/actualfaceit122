import telebot, threading, random, time, re
from telebot import types
from datetime import datetime, timedelta
import os
import sqlite3
from flask import Flask

from config import *
from database import *
from cards import (
    create_profile_card,
    create_lobbies_list_card,
    create_lobby_card,
    create_top_card,
    create_shop_card,
    create_match_registration_card
)

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
init_db()

# Flask для Render
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "ACTUAL FACEIT Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ═══════════════════════════════════════════════════════════════════
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ═══════════════════════════════════════════════════════════════════

active_lobbies = {}      # lobby_id -> {"players": [], "league": str, "status": str}
user_lobby = {}          # user_id -> lobby_id
active_matches = {}      # match_id -> match_data
user_match = {}          # user_id -> match_id
pending_screenshots = {} # match_id -> [screenshot_data]
pending_stats = {}       # admin_id -> match_id
user_flow = {}           # user_id -> {"state": str, ...}
party_chats = {}         # party_id -> chat_id

# ═══════════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════

def _pname(uid):
    p = get_player(uid)
    return p[1] if p else str(uid)

def _is_admin(uid):
    p = get_player(uid)
    return bool(p and p[17]) or uid == ADMIN_ID

def send_log(text):
    if LOG_CHANNEL_ID:
        try:
            bot.send_message(LOG_CHANNEL_ID, f"📋 {text}")
        except:
            pass

def check_ban(uid, chat_id=None):
    if is_banned(uid):
        if chat_id:
            bot.send_message(chat_id, "🚫 <b>Вы заблокированы!</b>\n\nОбратитесь к администратору.", parse_mode="HTML")
        return True
    return False

def check_mute(uid, chat_id=None):
    muted, until = is_muted(uid)
    if muted and chat_id:
        bot.send_message(chat_id, f"🔇 <b>Вы замучены!</b>\n\nДо: {until[:16]}", parse_mode="HTML")
    return muted

def check_reg(uid, chat_id):
    if check_ban(uid, chat_id):
        return False
    p = get_player(uid)
    if not p or not p[18]:
        bot.send_message(chat_id, "❌ Не зарегистрирован. Напиши /start")
        return False
    if check_mute(uid, chat_id):
        return False
    return True

def get_calib_text(player):
    if is_calibrated(player):
        return f"ELO: {player[5]}"
    else:
        return f"({player[26]}/{CALIB_THRESHOLD})"

def get_player_short_info(uid):
    p = get_player(uid)
    if not p:
        return None
    return {
        "name": p[1],
        "elo": p[5],
        "calib_text": get_calib_text(p)
    }

def generate_party_code():
    return ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ0123456789', k=6))

# ═══════════════════════════════════════════════════════════════════
# ГЛАВНОЕ МЕНЮ
# ═══════════════════════════════════════════════════════════════════

def main_menu_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎮 Найти матч", "👤 Профиль")
    kb.row("🏆 Топ", "🛒 Магазин", "🎒 Инвентарь")
    kb.row("👥 Пати", "📋 Поддержка", "⭐ Сезон")
    if _is_admin(uid):
        kb.row("⚙️ Админ панель")
    return kb

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    uid = msg.from_user.id
    if check_ban(uid, msg.chat.id):
        return
    p = get_player(uid)
    if p and p[18]:
        bot.send_message(uid, "⚡ <b>ACTUAL FACEIT</b>\n\nДобро пожаловать обратно!", reply_markup=main_menu_kb(uid), parse_mode="HTML")
        return
    user_flow[uid] = {"state": "reg_nick"}
    bot.send_message(uid, "👋 Добро пожаловать в <b>ACTUAL FACEIT</b>!\n\nШаг 1: Введи свой <b>никнейм</b>:", parse_mode="HTML")

@bot.message_handler(commands=['help'])
def cmd_help(msg):
    if not check_reg(msg.from_user.id, msg.chat.id):
        return
    bot.send_message(msg.chat.id,
        "📋 <b>Команды:</b>\n"
        "/start — Главное меню\n"
        "/profile — Профиль\n"
        "/top — Топ игроков\n"
        "/shop — Магазин\n"
        "/inv — Инвентарь\n"
        "/party — Создать пати\n"
        "/join <код> — Присоединиться к пати\n"
        "/ticket <id матча> <причина> — Жалоба\n\n"
        "👮 <b>Админ:</b>\n"
        "/manage <id/@ник> — Управление игроком\n"
        "/addbot <ник> <id> [device] — Создать бота",
        parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════
# РЕГИСТРАЦИЯ
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: user_flow.get(m.from_user.id, {}).get("state", "").startswith("reg_"))
def handle_reg(msg):
    uid = msg.from_user.id
    state = user_flow[uid]["state"]
    text = msg.text.strip()

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
        bot.send_message(uid, f"✅ Зарегистрирован как <b>{d['nick']}</b>!\n\nДобро пожаловать в ACTUAL FACEIT!",
                         reply_markup=main_menu_kb(uid), parse_mode="HTML")
                         # ═══════════════════════════════════════════════════════════════════
# ПРОФИЛЬ
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['profile'])
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def cmd_profile(msg):
    uid = msg.from_user.id
    if not check_reg(uid, msg.chat.id):
        return
    
    p = get_player(uid)
    if not p:
        bot.send_message(uid, "❌ Ошибка: игрок не найден")
        return
    
    stats = get_player_stats(uid)
    if not stats:
        bot.send_message(uid, "❌ Ошибка: статистика не найдена")
        return
    
    badges = [b for b in (p[22] or "").split(",") if b]
    map_stats = get_map_stats_for_player(uid)
    
    try:
        img = create_profile_card(p, stats, badges, map_stats)
        bot.send_photo(uid, img, caption=f"📊 <b>Профиль игрока</b>", parse_mode="HTML")
    except Exception as e:
        # fallback текстовый профиль
        text = (f"👤 <b>{p[1]}</b>\n"
                f"🆔 ID: {p[0]}\n"
                f"🎮 Game ID: {p[2]}\n"
                f"📱 Device: {p[3] or 'MOBILE'}\n\n"
                f"⭐ Ранг: {stats['level']}\n"
                f"📊 ELO: {stats['elo']}\n"
                f"💰 WC: {stats['coins']}\n\n"
                f"📈 <b>Статистика</b>\n"
                f"🎯 Убийства: {stats['kills']}\n"
                f"💀 Смерти: {stats['deaths']}\n"
                f"🤝 Ассисты: {stats['assists']}\n"
                f"🏆 Победы: {stats['wins']}\n"
                f"❌ Поражения: {stats['losses']}\n"
                f"📊 K/D: {stats['kd']}\n"
                f"📈 Винрейт: {stats['winrate']}%\n"
                f"🎯 ХС: {stats['headshots']}%")
        bot.send_message(uid, text, parse_mode="HTML")


# ═══════════════════════════════════════════════════════════════════
# ТОП ИГРОКОВ
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['top'])
@bot.message_handler(func=lambda m: m.text == "🏆 Топ")
def cmd_top(msg):
    uid = msg.from_user.id
    if not check_reg(uid, msg.chat.id):
        return
    
    players = get_top_players(10)
    try:
        img = create_top_card(players)
        bot.send_photo(uid, img, caption="🏆 <b>Топ игроков ACTUAL FACEIT</b>", parse_mode="HTML")
    except:
        text = "🏆 <b>Топ игроков</b>\n\n"
        for i, (name, elo, wins, losses, kills, deaths) in enumerate(players, 1):
            kd = round(kills / deaths, 2) if deaths > 0 else kills
            text += f"{i}. {name} — {elo} ELO (K/D: {kd})\n"
        bot.send_message(uid, text, parse_mode="HTML")


# ═══════════════════════════════════════════════════════════════════
# МАГАЗИН
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['shop'])
@bot.message_handler(func=lambda m: m.text == "🛒 Магазин")
def cmd_shop(msg):
    uid = msg.from_user.id
    if not check_reg(uid, msg.chat.id):
        return
    
    p = get_player(uid)
    coins = p[6] if p else 0
    
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("🎨 Скины", callback_data="shop_skins"),
        types.InlineKeyboardButton("🎭 Декор", callback_data="shop_decor"),
        types.InlineKeyboardButton("🛍 Товары", callback_data="shop_goods"),
        types.InlineKeyboardButton("❌ Закрыть", callback_data="shop_close")
    )
    
    bot.send_message(uid, f"🛒 <b>Магазин</b>\n💰 Ваш баланс: {coins} WC\n\nВыберите категорию:", reply_markup=kb, parse_mode="HTML")

def show_shop_category(uid, category):
    p = get_player(uid)
    coins = p[6] if p else 0
    items = SHOP_ITEMS.get(category, [])
    
    text = f"🛒 <b>{category.upper()}</b>\n💰 Баланс: {coins} WC\n\n"
    for i, item in enumerate(items):
        text += f"{i+1}. {item['name']} — {item['price']} WC\n"
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    for i, item in enumerate(items):
        kb.add(types.InlineKeyboardButton(f"💰 {item['name'][:20]}", callback_data=f"buy_{category}_{i}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="shop_back"))
    
    bot.send_message(uid, text, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("shop_"))
def cb_shop(c):
    action = c.data.split("_")[1]
    uid = c.from_user.id
    
    if action == "skins":
        show_shop_category(uid, "skins")
    elif action == "decor":
        show_shop_category(uid, "decor")
    elif action == "goods":
        show_shop_category(uid, "goods")
    elif action == "back":
        cmd_shop(c.message)
    elif action == "close":
        bot.delete_message(uid, c.message.message_id)
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def cb_buy(c):
    _, category, idx = c.data.split("_")
    uid = c.from_user.id
    idx = int(idx)
    
    item = SHOP_ITEMS.get(category, [])[idx]
    p = get_player(uid)
    
    if not p:
        bot.answer_callback_query(c.id, "Ошибка")
        return
    
    coins = p[6] or 0
    if coins < item["price"]:
        bot.answer_callback_query(c.id, f"❌ Не хватает WC! Нужно {item['price']} WC", show_alert=True)
        return
    
    remove_coins(uid, item["price"])
    days = item.get("days")
    add_inventory_item(uid, item["name"], item["item_type"], days=days, item_id=item["id"])
    
    bot.answer_callback_query(c.id, f"✅ Куплено: {item['name']}!", show_alert=True)
    send_log(f"🛒 {_pname(uid)} купил {item['name']} за {item['price']} WC")
    
    # Обновляем сообщение магазина
    show_shop_category(uid, category)


# ═══════════════════════════════════════════════════════════════════
# ИНВЕНТАРЬ
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['inv'])
@bot.message_handler(func=lambda m: m.text == "🎒 Инвентарь")
def cmd_inv(msg):
    uid = msg.from_user.id
    if not check_reg(uid, msg.chat.id):
        return
    
    p = get_player(uid)
    inv = get_inventory(uid)
    
    try:
        img = create_inventory_card(p, inv)
        bot.send_photo(uid, img, caption="🎒 <b>Инвентарь</b>", parse_mode="HTML")
    except:
        if not inv:
            bot.send_message(uid, "🎒 <b>Инвентарь пуст</b>", parse_mode="HTML")
            return
        
        text = "🎒 <b>Инвентарь</b>\n\n"
        for row in inv:
            inv_id, name, itype, item_id, activated, expires = row
            status = "✅" if activated else "⚡"
            text += f"{status} {name}\n"
        bot.send_message(uid, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("use_"))
def cb_use_item(c):
    inv_id = int(c.data.split("_")[1])
    uid = c.from_user.id
    
    row = get_inventory_item(inv_id)
    if not row or row[1] != uid:
        bot.answer_callback_query(c.id, "❌ Предмет не найден")
        return
    
    item_name, item_type, activated = row[2], row[3], row[6]
    
    if item_type == "unwarn":
        warns = get_warns(uid)
        if warns["count"] == 0:
            bot.answer_callback_query(c.id, "❌ У вас нет варнов!", show_alert=True)
            return
        remove_warn(uid)
        remove_inventory_item(inv_id)
        bot.answer_callback_query(c.id, f"✅ Варн снят! Осталось: {get_warns(uid)['count']}", show_alert=True)
        send_log(f"🟡 {_pname(uid)} использовал Снять Warn")
    
    elif item_type == "nick_change":
        remove_inventory_item(inv_id)
        user_flow[uid] = {"state": "nick_change"}
        bot.answer_callback_query(c.id)
        bot.send_message(uid, "✏️ Введи новый никнейм (2–20 символов):")
    
    elif item_type == "premium":
        if activated:
            bot.answer_callback_query(c.id, "❌ Уже активировано!", show_alert=True)
            return
        activate_inventory_item(inv_id)
        add_badge(uid, "premium")
        bot.answer_callback_query(c.id, f"✅ {item_name} активирован!", show_alert=True)
        send_log(f"⭐ {_pname(uid)} активировал {item_name}")
    
    elif item_type == "qual":
        if activated:
            bot.answer_callback_query(c.id, "❌ Уже активировано!", show_alert=True)
            return
        days = 30
        if row[7]:
            try:
                exp = datetime.fromisoformat(row[7])
                days = max(1, (exp - datetime.now()).days)
            except:
                pass
        activate_inventory_item(inv_id)
        grant_qual(uid, "FPL", days)
        bot.answer_callback_query(c.id, f"✅ FPL Quals активирован на {days} дней!", show_alert=True)
        send_log(f"⭐ {_pname(uid)} активировал FPL Quals")
    
    elif item_type in ["skin", "decor"]:
        if activated:
            bot.answer_callback_query(c.id, "❌ Уже активировано!", show_alert=True)
            return
        activate_inventory_item(inv_id)
        bot.answer_callback_query(c.id, f"✅ {item_name} активирован!", show_alert=True)
        send_log(f"⚡ {_pname(uid)} активировал {item_name}")
    
    else:
        bot.answer_callback_query(c.id, "❌ Неизвестный предмет")

@bot.message_handler(func=lambda m: user_flow.get(m.from_user.id, {}).get("state") == "nick_change")
def handle_nick_change(msg):
    uid = msg.from_user.id
    text = msg.text.strip()
    if not (2 <= len(text) <= 20):
        bot.send_message(uid, "❌ Никнейм 2–20 символов. Попробуй ещё раз:")
        return
    old = _pname(uid)
    set_username(uid, text)
    user_flow.pop(uid, None)
    bot.send_message(uid, f"✅ Ник изменён: <b>{old}</b> → <b>{text}</b>", parse_mode="HTML")
    send_log(f"✏️ {old} (#{uid}) → ник: {text}")


# ═══════════════════════════════════════════════════════════════════
# СЕЗОН
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text == "⭐ Сезон")
def cmd_season(msg):
    uid = msg.from_user.id
    if not check_reg(uid, msg.chat.id):
        return
    
    stats = get_season_stats()
    text = (f"⭐ <b>Сезон ACTUAL FACEIT</b>\n\n"
            f"📊 Статистика сезона:\n"
            f"👥 Всего игроков: {stats['total_players']}\n"
            f"📈 Средний ELO: {stats['avg_elo']}\n"
            f"👑 Топ игрок: {stats['top_player']} ({stats['top_elo']} ELO)\n\n"
            f"🎮 Калибровка: {CALIB_THRESHOLD} матчей\n"
            f"💰 Монеты за победу: {COINS_WIN_MIN}-{COINS_WIN_MAX}\n"
            f"📊 ELO за победу: +{ELO_WIN}\n"
            f"📊 ELO за поражение: -{ELO_LOSS_LOW} (лоутаб) / -{ELO_LOSS_HIGH} (хайтаб)")
    bot.send_message(uid, text, parse_mode="HTML")
    # ═══════════════════════════════════════════════════════════════════
# ПОИСК МАТЧА И ЛОББИ
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text == "🎮 Найти матч")
def cmd_find_match(msg):
    uid = msg.from_user.id
    if not check_reg(uid, msg.chat.id):
        return
    
    # Проверка на наличие в пати
    party_id = get_user_party(uid)
    if party_id:
        members = get_party_members(party_id)
        if len(members) > 5:
            bot.send_message(uid, "❌ В пати больше 5 человек, нельзя искать матч!")
            return
        bot.send_message(uid, f"👥 Вы в пати! Будет создано лобби для {len(members)} человек.")
        _create_party_lobby(uid, party_id)
        return
    
    # Обычный поиск
    kb = types.InlineKeyboardMarkup(row_width=2)
    for league in LEAGUES:
        kb.add(types.InlineKeyboardButton(league, callback_data=f"find_{league}"))
    bot.send_message(uid, "🎮 <b>Выберите лигу</b>", reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("find_"))
def cb_find_league(c):
    uid = c.from_user.id
    league = c.data.split("_")[1]
    
    # Проверка на квалификацию для FPL
    if league == "FPL" and not has_qual(uid, "FPL"):
        bot.answer_callback_query(c.id, "❌ У вас нет FPL квалификации! Купите в магазине.", show_alert=True)
        return
    
    bot.answer_callback_query(c.id)
    _show_lobbies_list(uid, league)

def _show_lobbies_list(uid, league):
    """Показывает список всех лобби (как в Walker Faceit)"""
    lobbies_data = {}
    for i in range(1, 11):
        lobbies_data[f"mobile_{i}"] = 0
        lobbies_data[f"pc_{i}"] = 0
    
    for lobby_id, lobby in active_lobbies.items():
        if lobby["league"] == league and lobby["status"] == "waiting":
            device = lobby["device"]
            slot = lobby["slot"]
            count = len(lobby["players"])
            lobbies_data[f"{device}_{slot}"] = count
    
    try:
        img = create_lobbies_list_card(lobbies_data, league)
        bot.send_photo(uid, img, caption=f"🎮 <b>Лобби {league}</b>\n\nВыберите лобби для входа:", parse_mode="HTML")
    except:
        text = f"🎮 <b>Лобби {league}</b>\n\n"
        for i in range(1, 6):
            mobile_count = lobbies_data[f"mobile_{i}"]
            pc_count = lobbies_data[f"pc_{i}"]
            text += f"Лобби #{i}: Mobile({mobile_count}/10) | PC({pc_count}/10)\n"
        bot.send_message(uid, text, parse_mode="HTML")
    
    # Кнопки для выбора лобби
    kb = types.InlineKeyboardMarkup(row_width=5)
    for i in range(1, 6):
        kb.add(
            types.InlineKeyboardButton(f"📱#{i}", callback_data=f"join_{league}_mobile_{i}"),
            types.InlineKeyboardButton(f"💻#{i}", callback_data=f"join_{league}_pc_{i}")
        )
    bot.send_message(uid, "🎮 Выберите лобби:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("join_"))
def cb_join_lobby(c):
    _, league, device, slot = c.data.split("_")
    slot = int(slot)
    uid = c.from_user.id
    lobby_id = f"{league}_{device}_{slot}"
    
    if not check_reg(uid, c.message.chat.id):
        return
    
    # Проверка на бан и мут
    if check_ban(uid, c.message.chat.id) or check_mute(uid, c.message.chat.id):
        return
    
    # Выход из старого лобби
    old_lobby = user_lobby.get(uid)
    if old_lobby:
        _leave_lobby(uid, old_lobby)
    
    # Создание или получение лобби
    if lobby_id not in active_lobbies:
        active_lobbies[lobby_id] = {
            "id": lobby_id,
            "league": league,
            "device": device,
            "slot": slot,
            "players": [],
            "status": "waiting",
            "ready": set(),
            "map_pool": list(MAPS)
        }
    
    lobby = active_lobbies[lobby_id]
    
    if lobby["status"] != "waiting":
        bot.answer_callback_query(c.id, "❌ Лобби уже в игре!")
        return
    
    if len(lobby["players"]) >= 10:
        bot.answer_callback_query(c.id, "❌ Лобби полное!")
        return
    
    # Добавление игрока
    lobby["players"].append(uid)
    user_lobby[uid] = lobby_id
    
    bot.answer_callback_query(c.id, "✅ Вы вошли в лобби!")
    
    # Обновление отображения для всех в лобби
    _update_lobby_display(lobby_id)
    
    # Проверка на заполнение
    if len(lobby["players"]) >= 10:
        _start_match_accept(lobby_id)

def _update_lobby_display(lobby_id):
    """Обновляет отображение лобби для всех участников"""
    lobby = active_lobbies.get(lobby_id)
    if not lobby:
        return
    
    players_info = []
    for uid in lobby["players"]:
        info = get_player_short_info(uid)
        if info:
            players_info.append((uid, info["name"], info["calib_text"]))
    
    try:
        img = create_lobby_card(lobby["slot"], players_info, lobby["league"], len(lobby["players"]))
        caption = f"🎮 Лобби #{lobby['slot']} ({lobby['league']})\n👥 Игроков: {len(lobby['players'])}/10"
    except:
        caption = f"🎮 Лобби #{lobby['slot']} ({lobby['league']})\n👥 Игроков: {len(lobby['players'])}/10\n\n"
        for i, (uid, name, calib) in enumerate(players_info, 1):
            caption += f"{i}. {name} ({calib})\n"
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🚪 Покинуть лобби", callback_data=f"leave_{lobby_id}"))
    
    for uid in lobby["players"]:
        try:
            bot.send_message(uid, caption, reply_markup=kb, parse_mode="HTML")
        except:
            pass

def _leave_lobby(uid, lobby_id):
    lobby = active_lobbies.get(lobby_id)
    if not lobby:
        return
    
    if uid in lobby["players"]:
        lobby["players"].remove(uid)
    if uid in lobby["ready"]:
        lobby["ready"].discard(uid)
    user_lobby.pop(uid, None)
    
    if len(lobby["players"]) == 0:
        del active_lobbies[lobby_id]
    else:
        _update_lobby_display(lobby_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("leave_"))
def cb_leave_lobby(c):
    lobby_id = c.data.split("_", 1)[1]
    uid = c.from_user.id
    
    _leave_lobby(uid, lobby_id)
    bot.answer_callback_query(c.id, "✅ Вы покинули лобби")


# ═══════════════════════════════════════════════════════════════════
# ПРИНЯТИЕ МАТЧА
# ═══════════════════════════════════════════════════════════════════

def _start_match_accept(lobby_id):
    lobby = active_lobbies[lobby_id]
    if lobby["status"] != "waiting":
        return
    
    lobby["status"] = "accept"
    lobby["ready"] = set()
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Принять матч", callback_data=f"accept_{lobby_id}"))
    kb.add(types.InlineKeyboardButton("🚪 Выйти", callback_data=f"leave_{lobby_id}"))
    
    for uid in lobby["players"]:
        try:
            bot.send_message(uid, f"⚔️ <b>МАТЧ НАЙДЕН!</b>\n\n⏳ У вас есть {ACCEPT_TIMEOUT} секунд, чтобы принять!\n\nНажмите кнопку ниже:", reply_markup=kb, parse_mode="HTML")
        except:
            pass
        _start_accept_timer(lobby_id, uid)
    
    threading.Timer(ACCEPT_TIMEOUT, _check_accept_timeout, [lobby_id]).start()

def _start_accept_timer(lobby_id, uid):
    t = threading.Timer(ACCEPT_TIMEOUT, _accept_timeout, [lobby_id, uid])
    t.start()
    if "timers" not in active_lobbies[lobby_id]:
        active_lobbies[lobby_id]["timers"] = {}
    active_lobbies[lobby_id]["timers"][uid] = t

def _accept_timeout(lobby_id, uid):
    lobby = active_lobbies.get(lobby_id)
    if not lobby or lobby["status"] != "accept":
        return
    if uid in lobby["ready"]:
        return
    
    _leave_lobby(uid, lobby_id)
    warns = add_warn(uid, reason="Не принял матч")
    try:
        bot.send_message(uid, f"⚠️ <b>Варн!</b> Не принял матч.\nВарнов: {warns['count']}/3", parse_mode="HTML")
    except:
        pass
    
    if warns["count"] >= 3:
        mute_player(uid, hours=2, reason="3 варна (не принятие матчей)")
        clear_warns(uid)
        try:
            bot.send_message(uid, f"🔇 <b>Мут 2 часа!</b>\nПричина: 3 варна за не принятие матчей", parse_mode="HTML")
        except:
            pass

def _check_accept_timeout(lobby_id):
    lobby = active_lobbies.get(lobby_id)
    if not lobby or lobby["status"] != "accept":
        return
    
    all_ready = all(uid in lobby["ready"] for uid in lobby["players"])
    if all_ready and len(lobby["players"]) == 10:
        _start_veto(lobby_id)
    else:
        lobby["status"] = "waiting"
        for uid in lobby["players"]:
            try:
                bot.send_message(uid, "❌ Не все приняли матч. Поиск возобновлён...")
            except:
                pass
        _update_lobby_display(lobby_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("accept_"))
def cb_accept_match(c):
    lobby_id = c.data.split("_", 1)[1]
    uid = c.from_user.id
    lobby = active_lobbies.get(lobby_id)
    
    if not lobby or lobby["status"] != "accept":
        bot.answer_callback_query(c.id, "❌ Недоступно")
        return
    
    if uid not in lobby["players"]:
        bot.answer_callback_query(c.id, "❌ Вы не в этом лобби")
        return
    
    lobby["ready"].add(uid)
    bot.answer_callback_query(c.id, "✅ Вы приняли матч!")
    
    # Остановка таймера
    if "timers" in lobby and uid in lobby["timers"]:
        lobby["timers"][uid].cancel()
        del lobby["timers"][uid]
    
    # Проверка, все ли приняли
    if len(lobby["ready"]) == len(lobby["players"]):
        _start_veto(lobby_id)
        # ═══════════════════════════════════════════════════════════════════
# ВЕТО (ВЫБОР КАРТ)
# ═══════════════════════════════════════════════════════════════════

def _start_veto(lobby_id):
    lobby = active_lobbies[lobby_id]
    if lobby["status"] != "accept":
        return
    
    lobby["status"] = "veto"
    lobby["bans"] = []
    lobby["map_pool"] = list(MAPS)
    lobby["ban_count"] = 0
    lobby["veto_turn"] = "ct"  # CT начинает банить
    
    # Случайное распределение игроков по командам (пока скрыто)
    players = list(lobby["players"])
    random.shuffle(players)
    lobby["team_ct"] = players[:5]
    lobby["team_t"] = players[5:]
    lobby["captain_ct"] = lobby["team_ct"][0]
    lobby["captain_t"] = lobby["team_t"][0]
    
    send_log(f"🗺 Лобби {lobby_id}: Начало вето. Капитан CT: {_pname(lobby['captain_ct'])}, T: {_pname(lobby['captain_t'])}")
    
    _send_veto_message(lobby_id)

def _send_veto_message(lobby_id):
    lobby = active_lobbies[lobby_id]
    if not lobby or lobby["status"] != "veto":
        return
    
    turn = lobby["veto_turn"]
    captain = lobby["captain_ct"] if turn == "ct" else lobby["captain_t"]
    
    # Статистика карт для отображения
    map_stats = get_map_stats_for_veto()
    
    # Формируем сообщение со списком карт
    text = f"🗺 <b>ВЫБОР КАРТЫ</b>\n\n"
    text += f"📊 Бан {lobby['ban_count'] + 1}/4\n"
    text += f"🎮 Ход: <b>{'🟦 CT' if turn == 'ct' else '🟧 T'}</b>\n"
    text += f"👑 Капитан: {_pname(captain)}\n\n"
    text += "📋 Доступные карты:\n"
    
    for i, map_name in enumerate(lobby["map_pool"], 1):
        stats = map_stats.get(map_name, {"pick_pct": 0, "ct_wr": 50, "t_wr": 50})
        text += f"{i}. <b>{map_name}</b> — выбор: {stats['pick_pct']}% | CT: {stats['ct_wr']}% | T: {stats['t_wr']}%\n"
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    for map_name in lobby["map_pool"]:
        kb.add(types.InlineKeyboardButton(f"❌ Забанить {map_name}", callback_data=f"ban_{lobby_id}_{map_name}"))
    
    # Отправляем капитану с кнопками, остальным без кнопок
    for uid in lobby["players"]:
        try:
            if uid == captain:
                bot.send_message(uid, text, reply_markup=kb, parse_mode="HTML")
            else:
                bot.send_message(uid, text, parse_mode="HTML")
        except:
            pass

def get_map_stats_for_veto():
    """Получает статистику карт для отображения в вето"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT map_name, times_played, times_picked, ct_wins, t_wins FROM map_stats")
    rows = cur.fetchall()
    conn.close()
    
    total_played = sum(r[1] for r in rows) or 1
    total_picked = sum(r[2] for r in rows) or 1
    
    result = {}
    for map_name, played, picked, ct_w, t_w in rows:
        total_m = ct_w + t_w or 1
        result[map_name] = {
            "pick_pct": round(picked / total_picked * 100, 1),
            "ct_wr": round(ct_w / total_m * 100, 1),
            "t_wr": round(t_w / total_m * 100, 1),
            "played": played
        }
    
    # Для карт без статистики
    from config import MAPS
    for map_name in MAPS:
        if map_name not in result:
            result[map_name] = {"pick_pct": 0, "ct_wr": 50, "t_wr": 50, "played": 0}
    
    return result

@bot.callback_query_handler(func=lambda c: c.data.startswith("ban_"))
def cb_ban_map(c):
    _, lobby_id, map_name = c.data.split("_", 2)
    uid = c.from_user.id
    lobby = active_lobbies.get(lobby_id)
    
    if not lobby or lobby["status"] != "veto":
        bot.answer_callback_query(c.id, "❌ Вето недоступно")
        return
    
    turn = lobby["veto_turn"]
    captain = lobby["captain_ct"] if turn == "ct" else lobby["captain_t"]
    
    if uid != captain:
        bot.answer_callback_query(c.id, "❌ Сейчас не ваш ход!")
        return
    
    if map_name not in lobby["map_pool"]:
        bot.answer_callback_query(c.id, "❌ Карта уже забанена")
        return
    
    # Бан карты
    lobby["map_pool"].remove(map_name)
    lobby["bans"].append({"map": map_name, "by": turn})
    lobby["ban_count"] += 1
    
    # Уведомление о бане
    ban_text = f"🚫 <b>{'CT' if turn == 'ct' else 'T'}</b> забанил <b>{map_name}</b>"
    for uid_in_lobby in lobby["players"]:
        try:
            bot.send_message(uid_in_lobby, ban_text, parse_mode="HTML")
        except:
            pass
    
    send_log(f"🚫 Лобби {lobby_id}: {'CT' if turn == 'ct' else 'T'} забанил {map_name}")
    
    # Меняем ход
    lobby["veto_turn"] = "t" if turn == "ct" else "ct"
    
    # Проверяем, осталась ли одна карта
    if lobby["ban_count"] >= 4 and len(lobby["map_pool"]) == 1:
        final_map = lobby["map_pool"][0]
        final_text = f"✅ <b>Финальная карта: {final_map}</b>"
        for uid_in_lobby in lobby["players"]:
            try:
                bot.send_message(uid_in_lobby, final_text, parse_mode="HTML")
            except:
                pass
        send_log(f"✅ Лобби {lobby_id}: Финальная карта → {final_map}")
        _start_match_registration(lobby_id, final_map)
    else:
        # Обновляем сообщение вето
        _send_veto_message(lobby_id)
    
    bot.answer_callback_query(c.id, f"✅ Карта {map_name} забанена!")


# ═══════════════════════════════════════════════════════════════════
# РЕГИСТРАЦИЯ МАТЧА (ОТДЕЛЬНЫЙ ЧАТ)
# ═══════════════════════════════════════════════════════════════════

# Канал/чат для регистрации матчей (нужно создать и указать ID)
MATCH_REGISTRATION_CHAT_ID = -1003701987520   # Замени на ID чата

def _start_match_registration(lobby_id, map_name):
    lobby = active_lobbies[lobby_id]
    if not lobby:
        return
    
    lobby["status"] = "registration"
    league = lobby["league"]
    team_ct = lobby["team_ct"]
    team_t = lobby["team_t"]
    
    # Получаем информацию об игроках
    ct_players = [get_player(uid) for uid in team_ct]
    t_players = [get_player(uid) for uid in team_t]
    
    # Создаём карточку для регистрации
    try:
        img = create_match_registration_card(0, map_name, league, team_ct, team_t, ct_players, t_players)
    except:
        img = None
    
    # Формируем текст
    text = f"⚔️ <b>МАТЧ НА РЕГИСТРАЦИЮ</b>\n\n"
    text += f"🏆 Лига: {league}\n"
    text += f"🗺 Карта: {map_name}\n\n"
    text += f"🟦 <b>КОМАНДА CT</b>\n"
    for i, uid in enumerate(team_ct, 1):
        p = get_player(uid)
        if p:
            text += f"{i}. {p[1]} — ID: {uid} — {p[5]} ELO\n"
    text += f"\n🟧 <b>КОМАНДА T</b>\n"
    for i, uid in enumerate(team_t, 1):
        p = get_player(uid)
        if p:
            text += f"{i}. {p[1]} — ID: {uid} — {p[5]} ELO\n"
    text += f"\n📸 Скриншоты игроков появятся ниже. Когда все скриншоты получены — нажмите кнопку регистрации."
    
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✔ Зарегистрировать матч", callback_data=f"reg_match_{lobby_id}"),
        types.InlineKeyboardButton("❌ Отменить матч", callback_data=f"cancel_match_{lobby_id}")
    )
    
    # Сохраняем матч в БД
    match_id = save_match(lobby["slot"], map_name, team_ct, team_t, league)
    
    # Отправляем в чат регистрации
    chat_id = MATCH_REGISTRATION_CHAT_ID
    if chat_id:
        if img:
            msg = bot.send_photo(chat_id, img, caption=text, reply_markup=kb, parse_mode="HTML")
        else:
            msg = bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
        
        # Закрепляем сообщение
        try:
            bot.pin_chat_message(chat_id, msg.message_id)
        except:
            pass
        
        update_match_registration(match_id, chat_id, msg.message_id)
    
    # Сохраняем в память
    active_matches[match_id] = {
        "id": match_id,
        "lobby_id": lobby_id,
        "map_name": map_name,
        "league": league,
        "team_ct": team_ct,
        "team_t": team_t,
        "screenshots": [],
        "status": "registration",
        "chat_id": chat_id,
        "message_id": msg.message_id if chat_id else None
    }
    
    # Уведомляем игроков
    for uid in team_ct + team_t:
        try:
            bot.send_message(uid, f"⚔️ <b>Матч #{match_id} создан!</b>\n\n"
                                  f"🗺 Карта: {map_name}\n"
                                  f"🏆 Лига: {league}\n\n"
                                  f"📸 Отправьте скриншот результата матча сюда или в чат регистрации.",
                                  parse_mode="HTML")
        except:
            pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("reg_match_"))
def cb_register_match(c):
    lobby_id = c.data.split("_")[2]
    admin_uid = c.from_user.id
    
    if not _is_admin(admin_uid):
        bot.answer_callback_query(c.id, "❌ Только администратор может регистрировать матчи!")
        return
    
    # Ищем матч
    match = None
    for mid, m in active_matches.items():
        if m.get("lobby_id") == lobby_id:
            match = m
            break
    
    if not match:
        bot.answer_callback_query(c.id, "❌ Матч не найден")
        return
    
    pending_stats[admin_uid] = match["id"]
    
    # Получаем составы команд
    ct_names = "\n".join([f"• {_pname(uid)} (ID: {uid})" for uid in match["team_ct"]])
    t_names = "\n".join([f"• {_pname(uid)} (ID: {uid})" for uid in match["team_t"]])
    
    bot.send_message(admin_uid,
                     f"✏️ <b>Ввод статистики матча #{match['id']}</b>\n\n"
                     f"🟦 <b>CT</b>:\n{ct_names}\n\n"
                     f"🟧 <b>T</b>:\n{t_names}\n\n"
                     f"📝 <b>Формат ввода (каждого игрока через запятую):</b>\n"
                     f"<code>ID_игрока K A D, ID_игрока K A D, ...</code>\n\n"
                     f"📌 <b>ВАЖНО!</b>\n"
                     f"• Сначала введите статистику команды, которая ВЫИГРАЛА\n"
                     f"• Указывайте сторону, за которую победившая команда НАЧИНАЛА игру\n\n"
                     f"Пример:\n"
                     f"<code>13:11\n"
                     f"8521250777 18 5 2, 123456789 15 8 3, ...\n"
                     f"987654321 12 10 4, ...</code>\n\n"
                     f"💡 Счёт укажите первой строкой",
                     parse_mode="HTML")
    
    bot.answer_callback_query(c.id, "✅ Введите статистику матча")
    # ═══════════════════════════════════════════════════════════════════
# ОБРАБОТКА СТАТИСТИКИ И НАЧИСЛЕНИЕ ELO
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.from_user.id in pending_stats)
def handle_stats_input(msg):
    admin_uid = msg.from_user.id
    match_id = pending_stats.pop(admin_uid, None)
    
    if not match_id:
        return
    
    match = active_matches.get(match_id)
    if not match:
        bot.send_message(admin_uid, "❌ Матч не найден")
        return
    
    try:
        lines = [l.strip() for l in msg.text.splitlines() if l.strip()]
        if len(lines) < 2:
            raise ValueError("Слишком мало строк")
        
        # Парсим счёт
        score_parts = lines[0].replace(" ", "").split(":")
        if len(score_parts) != 2:
            raise ValueError("Неверный формат счёта. Используйте X:Y")
        
        score_w, score_l = int(score_parts[0]), int(score_parts[1])
        
        # Определяем победителя по счёту
        winner_side = "ct" if score_w >= score_l else "t"
        
        # Парсим статистику игроков
        winner_entries = []
        loser_entries = []
        current_is_winner = True
        
        for line in lines[1:]:
            if line.upper() == "CT" or line.upper() == "T":
                continue
            
            parts = line.split(",")
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                nums = part.split()
                if len(nums) >= 4:
                    try:
                        pid = int(nums[0])
                        k = int(nums[1])
                        a = int(nums[2])
                        d = int(nums[3])
                        if current_is_winner:
                            winner_entries.append((pid, k, a, d))
                        else:
                            loser_entries.append((pid, k, a, d))
                    except ValueError:
                        continue
            
            current_is_winner = False
        
        if not winner_entries or not loser_entries:
            raise ValueError("Не найдены данные игроков")
        
        # Определяем счёт
        if winner_side == "ct":
            score_ct, score_t = score_w, score_l
        else:
            score_ct, score_t = score_l, score_w
        
        # Начисление ELO и монет
        _process_match_results(match_id, winner_side, score_ct, score_t, winner_entries, loser_entries, admin_uid)
        
    except Exception as e:
        bot.send_message(admin_uid, f"❌ Ошибка: {e}\n\nПроверьте формат и попробуйте снова.\n\nФормат:\n<code>13:11\nID K A D, ID K A D, ...\nID K A D, ID K A D, ...</code>", parse_mode="HTML")
        pending_stats[admin_uid] = match_id

def _process_match_results(match_id, winner_side, score_ct, score_t, winner_entries, loser_entries, admin_uid):
    match = active_matches.get(match_id)
    if not match:
        return
    
    map_name = match["map_name"]
    league = match["league"]
    team_ct = set(match["team_ct"])
    team_t = set(match["team_t"])
    
    # Словарь для хранения изменений ELO
    elo_changes = {}
    coin_changes = {}
    
    # Обработка победителей
    for pid, k, a, d in winner_entries:
        p = get_player(pid)
        if not p:
            continue
        
        is_calibrating = not is_calibrated(p)
        kills_threshold = KILLS_THRESHOLD
        
        # Расчёт ELO для победителей
        if is_calibrating:
            elo_change = ELO_WIN  # +17 для калибровки (будет добавлено позже)
            actual_elo_change = ELO_WIN + CALIB_WIN_BONUS  # скрытый бонус
        else:
            elo_change = ELO_WIN
            actual_elo_change = ELO_WIN
        
        # Монеты за победу
        coins = random.randint(COINS_WIN_MIN, COINS_WIN_MAX)
        x2 = has_active_item(pid, "x2coins")
        if x2:
            coins *= 2
        
        # Определяем, в какой команде был игрок
        side = "ct" if pid in team_ct else "t"
        
        # Обновление статистики
        update_player_stats(pid, k, d, a, 0, True, map_name)
        add_coins(pid, coins)
        
        # Сохраняем статистику матча
        kd = round(k / d, 2) if d > 0 else k
        rating = round(kd * 0.85 + a * 0.02, 2)
        save_match_stats(match_id, pid, side, k, d, a, kd, rating)
        
        # Обновляем ELO (сохраняем фактическое изменение для внутреннего расчёта)
        current_elo = p[5]
        new_elo = current_elo + actual_elo_change
        set_elo(pid, new_elo)
        
        elo_changes[pid] = actual_elo_change
        coin_changes[pid] = coins
        
        send_log(f"📊 {p[1]} +{actual_elo_change} ELO, +{coins} монет (победа)")
    
    # Обработка проигравших
    for pid, k, a, d in loser_entries:
        p = get_player(pid)
        if not p:
            continue
        
        is_calibrating = not is_calibrated(p)
        
        # Определяем хайтаб/лоутаб по количеству убийств
        if k >= KILLS_THRESHOLD:
            elo_change = -ELO_LOSS_HIGH  # -15 для хайтаб
        else:
            elo_change = -ELO_LOSS_LOW   # -25 для лоутаб
        
        # Монеты за поражение
        coins = random.randint(COINS_LOSS_MIN, COINS_LOSS_MAX)
        x2 = has_active_item(pid, "x2coins")
        if x2:
            coins *= 2
        
        # Определяем, в какой команде был игрок
        side = "ct" if pid in team_ct else "t"
        
        # Обновление статистики
        update_player_stats(pid, k, d, a, 0, False, map_name)
        add_coins(pid, coins)
        
        # Сохраняем статистику матча
        kd = round(k / d, 2) if d > 0 else k
        rating = round(kd * 0.85 + a * 0.02, 2)
        save_match_stats(match_id, pid, side, k, d, a, kd, rating)
        
        # Обновляем ELO
        current_elo = p[5]
        new_elo = current_elo + elo_change
        set_elo(pid, new_elo)
        
        elo_changes[pid] = elo_change
        coin_changes[pid] = coins
        
        send_log(f"📊 {p[1]} {elo_change} ELO, +{coins} монет (поражение, {'хайтаб' if k >= KILLS_THRESHOLD else 'лоутаб'})")
    
    # Обновляем калибровку для всех игроков
    for pid in elo_changes.keys():
        p = get_player(pid)
        if p and not is_calibrated(p):
            calib = calib_count(p) + 1
            conn = sqlite3.connect(DB)
            conn.execute("UPDATE players SET calibration_matches=? WHERE user_id=?", (calib, pid))
            conn.commit()
            conn.close()
    
    # Отправляем уведомления игрокам
    for pid in elo_changes:
        change = elo_changes[pid]
        coins = coin_changes[pid]
        sign = "+" if change > 0 else ""
        result = "🏆 ПОБЕДА" if change > 0 else "💀 ПОРАЖЕНИЕ"
        
        try:
            bot.send_message(pid, f"{result}!\n\n📊 ELO: {sign}{change}\n💰 Монеты: +{coins}", parse_mode="HTML")
        except:
            pass
    
    # Завершаем матч в БД
    finalize_match(match_id, winner_side, score_ct, score_t)
    
    # Отправляем результат в чат регистрации
    chat_id = match.get("chat_id")
    if chat_id:
        result_text = (f"✅ <b>Матч #{match_id} зарегистрирован!</b>\n\n"
                       f"🗺 Карта: {map_name}\n"
                       f"🏆 Победитель: {'CT' if winner_side == 'ct' else 'T'}\n"
                       f"📋 Счёт: {score_ct}:{score_t}")
        
        try:
            bot.send_message(chat_id, result_text, parse_mode="HTML")
            # Открепляем сообщение
            if match.get("message_id"):
                try:
                    bot.unpin_chat_message(chat_id, match["message_id"])
                except:
                    pass
        except:
            pass
    
    # Очищаем лобби
    lobby_id = match.get("lobby_id")
    if lobby_id and lobby_id in active_lobbies:
        del active_lobbies[lobby_id]
    
    # Удаляем из активных матчей
    del active_matches[match_id]
    
    bot.send_message(admin_uid, f"✅ Матч #{match_id} успешно зарегистрирован! Статистика сохранена.")
    send_log(f"✅ Матч #{match_id}: {winner_side.upper()} {score_ct}:{score_t} | Зарегистрировал {_pname(admin_uid)}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("cancel_match_"))
def cb_cancel_match(c):
    lobby_id = c.data.split("_")[2]
    admin_uid = c.from_user.id
    
    if not _is_admin(admin_uid):
        bot.answer_callback_query(c.id, "❌ Только администратор может отменить матч!")
        return
    
    # Ищем матч
    match = None
    for mid, m in active_matches.items():
        if m.get("lobby_id") == lobby_id:
            match = m
            break
    
    if not match:
        bot.answer_callback_query(c.id, "❌ Матч не найден")
        return
    
    # Уведомляем игроков
    for uid in match["team_ct"] + match["team_t"]:
        try:
            bot.send_message(uid, f"❌ <b>Матч #{match['id']} отменён администратором!</b>", parse_mode="HTML")
        except:
            pass
    
    # Очищаем лобби
    if lobby_id in active_lobbies:
        del active_lobbies[lobby_id]
    
    # Удаляем из активных матчей
    del active_matches[match["id"]]
    
    # Отправляем в чат регистрации
    chat_id = match.get("chat_id")
    if chat_id:
        try:
            bot.send_message(chat_id, f"❌ <b>Матч #{match['id']} отменён!</b>", parse_mode="HTML")
            if match.get("message_id"):
                try:
                    bot.unpin_chat_message(chat_id, match["message_id"])
                except:
                    pass
        except:
            pass
    
    bot.answer_callback_query(c.id, "✅ Матч отменён")
    send_log(f"❌ Матч #{match['id']} отменён администратором {_pname(admin_uid)}")


# ═══════════════════════════════════════════════════════════════════
# СКРИНШОТЫ ОТ ИГРОКОВ
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(content_types=['photo'])
def handle_match_screenshot(msg):
    uid = msg.from_user.id
    
    # Проверяем, есть ли у игрока активный матч
    match_id = user_match.get(uid)
    if not match_id:
        return
    
    match = active_matches.get(match_id)
    if not match or match["status"] != "registration":
        return
    
    file_id = msg.photo[-1].file_id
    
    # Сохраняем скриншот
    if "screenshots" not in match:
        match["screenshots"] = []
    match["screenshots"].append({"user_id": uid, "file_id": file_id, "timestamp": datetime.now().isoformat()})
    
    bot.send_message(uid, "✅ Скриншот отправлен! Администратор обработает результат.")
    
    # Отправляем скриншот в чат регистрации
    chat_id = match.get("chat_id")
    if chat_id:
        try:
            bot.send_photo(chat_id, file_id, caption=f"📸 Скриншот от: {_pname(uid)}\nМатч: #{match_id}", parse_mode="HTML")
        except:
            pass
    
    send_log(f"📸 Скриншот матча #{match_id} от {_pname(uid)}")


# ═══════════════════════════════════════════════════════════════════
# АДМИН ПАНЕЛЬ
# ═══════════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text == "⚙️ Админ панель")
@bot.message_handler(commands=['admin'])
def cmd_admin(msg):
    if not _is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "🚫 Нет доступа")
        return
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👤 Найти игрока", callback_data="admin_find"),
        types.InlineKeyboardButton("🤖 Добавить бота", callback_data="admin_addbot"),
        types.InlineKeyboardButton("📋 Лобби", callback_data="admin_lobbies"),
        types.InlineKeyboardButton("⚔️ Матчи", callback_data="admin_matches"),
        types.InlineKeyboardButton("🏆 Сезон", callback_data="admin_season"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_mailing"),
        types.InlineKeyboardButton("📋 Жалобы", callback_data="admin_tickets")
    )
    bot.send_message(msg.chat.id, "⚙️ <b>Панель администратора</b>", reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "admin_lobbies")
def cb_admin_lobbies(c):
    if not _is_admin(c.from_user.id):
        return
    text = "📋 <b>Активные лобби:</b>\n\n"
    for lobby_id, lobby in active_lobbies.items():
        text += f"• {lobby_id} — {len(lobby['players'])}/10 — {lobby['status']}\n"
    if not active_lobbies:
        text += "Нет активных лобби"
    bot.send_message(c.from_user.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "admin_matches")
def cb_admin_matches(c):
    if not _is_admin(c.from_user.id):
        return
    text = "⚔️ <b>Активные матчи:</b>\n\n"
    for mid, match in active_matches.items():
        text += f"• #{mid} — {match['map_name']} — {match['league']} — {match['status']}\n"
    if not active_matches:
        text += "Нет активных матчей"
    bot.send_message(c.from_user.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "admin_find")
def cb_admin_find(c):
    if not _is_admin(c.from_user.id):
        return
    user_flow[c.from_user.id] = {"state": "admin_find"}
    bot.send_message(c.from_user.id, "👤 Введите ID, @ник или Game ID игрока:")

@bot.callback_query_handler(func=lambda c: c.data == "admin_addbot")
def cb_admin_addbot(c):
    if not _is_admin(c.from_user.id):
        return
    user_flow[c.from_user.id] = {"state": "admin_addbot"}
    bot.send_message(c.from_user.id, "🤖 Формат: <code>Имя GameID [Device]</code>\nПример: <code>BotNick 9999 PC</code>", parse_mode="HTML")

@bot.message_handler(func=lambda m: user_flow.get(m.from_user.id, {}).get("state") == "admin_find")
def handle_admin_find(msg):
    uid = msg.from_user.id
    text = msg.text.strip()
    
    target = None
    if text.startswith("@"):
        target = get_player_by_username(text[1:])
    elif text.isdigit():
        target = get_player(int(text))
    
    if not target:
        bot.send_message(uid, "❌ Игрок не найден")
        user_flow.pop(uid, None)
        return
    
    user_flow.pop(uid, None)
    _show_player_manage(uid, target[0])

@bot.message_handler(func=lambda m: user_flow.get(m.from_user.id, {}).get("state") == "admin_addbot")
def handle_admin_addbot(msg):
    uid = msg.from_user.id
    parts = msg.text.split()
    
    if len(parts) < 2:
        bot.send_message(uid, "❌ Формат: Имя GameID [Device]")
        return
    
    name = parts[0]
    game_id = parts[1]
    device = parts[2] if len(parts) > 2 else "PC"
    bot_id = random.randint(10000000, 99999999)
    
    register_bot(bot_id, name, game_id, device)
    bot.send_message(uid, f"✅ Бот <b>{name}</b> создан!\nID: {bot_id}", parse_mode="HTML")
    user_flow.pop(uid, None)

def _show_player_manage(admin_uid, target_id):
    p = get_player(target_id)
    if not p:
        bot.send_message(admin_uid, "❌ Игрок не найден")
        return
    
    warns = get_warns(target_id)
    muted, _ = is_muted(target_id)
    banned = is_banned(target_id)
    
    text = (f"👤 <b>{p[1]}</b>\n"
            f"🆔 ID: {target_id}\n"
            f"🎮 Game ID: {p[2]}\n"
            f"⭐ Уровень: {p[4]}\n"
            f"📊 ELO: {p[5]}\n"
            f"💰 WC: {p[6]}\n"
            f"⚠️ Варны: {warns['count']}/3\n"
            f"🔇 Мут: {'Да' if muted else 'Нет'}\n"
            f"🚫 Бан: {'Да' if banned else 'Нет'}")
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✏️ Ник", callback_data=f"mg_nick_{target_id}"),
        types.InlineKeyboardButton("💰 WC", callback_data=f"mg_coins_{target_id}"),
        types.InlineKeyboardButton("📊 ELO", callback_data=f"mg_elo_{target_id}"),
        types.InlineKeyboardButton("⚠️ Варн", callback_data=f"mg_warn_{target_id}"),
        types.InlineKeyboardButton("🔇 Мут", callback_data=f"mg_mute_{target_id}"),
        types.InlineKeyboardButton("🚫 Бан", callback_data=f"mg_ban_{target_id}"),
        types.InlineKeyboardButton("✅ Снять мут", callback_data=f"mg_unmute_{target_id}"),
        types.InlineKeyboardButton("✅ Снять бан", callback_data=f"mg_unban_{target_id}"),
        types.InlineKeyboardButton("🔄 Сброс варнов", callback_data=f"mg_clear_warns_{target_id}"),
        types.InlineKeyboardButton("🎁 Выдать предмет", callback_data=f"mg_item_{target_id}"),
        types.InlineKeyboardButton("⭐ Quals", callback_data=f"mg_quals_{target_id}")
    )
    
    bot.send_message(admin_uid, text, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("mg_"))
def cb_player_manage(c):
    _, action, target_id = c.data.split("_", 2)
    target_id = int(target_id)
    admin_uid = c.from_user.id
    
    if not _is_admin(admin_uid):
        bot.answer_callback_query(c.id, "Нет доступа")
        return
    
    # Мгновенные действия
    if action == "unmute":
        unmute_player(target_id)
        bot.answer_callback_query(c.id, "✅ Мут снят")
        _show_player_manage(admin_uid, target_id)
    elif action == "unban":
        unban_player(target_id)
        bot.answer_callback_query(c.id, "✅ Бан снят")
        _show_player_manage(admin_uid, target_id)
    elif action == "clear_warns":
        clear_warns(target_id)
        bot.answer_callback_query(c.id, "✅ Варны сброшены")
        _show_player_manage(admin_uid, target_id)
    else:
        # Действия с вводом
        user_flow[admin_uid] = {"state": f"mg_{action}", "target": target_id}
        
        prompts = {
            "nick": "✏️ Введите новый никнейм:",
            "coins": "💰 Введите количество WC:",
            "elo": "📊 Введите новое значение ELO:",
            "warn": "⚠️ Введите количество варнов (1-3):",
            "mute": "🔇 Введите количество часов мута:",
            "ban": "🚫 Введите данные бана в формате: дни | причина\nПример: 7 | Оскорбления",
            "item": "🎁 Введите данные предмета: название | тип | дни\nПример: PREMIUM | premium | 30",
            "quals": "⭐ Введите количество дней Quals:"
        }
        
        bot.send_message(admin_uid, prompts.get(action, "Введите значение:"))
        bot.answer_callback_query(c.id)

@bot.message_handler(func=lambda m: user_flow.get(m.from_user.id, {}).get("state", "").startswith("mg_"))
def handle_player_manage_input(msg):
    admin_uid = msg.from_user.id
    state = user_flow[admin_uid]["state"]
    text = msg.text.strip()
    target_id = user_flow[admin_uid]["target"]
    
    action = state.split("_")[1]
    
    try:
        if action == "nick":
            set_username(target_id, text)
            bot.send_message(admin_uid, f"✅ Ник изменён на {text}")
        elif action == "coins":
            set_coins(target_id, int(text))
            bot.send_message(admin_uid, f"✅ WC установлены: {text}")
        elif action == "elo":
            set_elo(target_id, int(text))
            bot.send_message(admin_uid, f"✅ ELO установлен: {text}")
        elif action == "warn":
            cnt = min(int(text), 3)
            for _ in range(cnt):
                add_warn(target_id, reason="Выдан администратором", admin_id=admin_uid)
            bot.send_message(admin_uid, f"✅ Выдано {cnt} варн(а)")
        elif action == "mute":
            hours = int(text) if text.isdigit() else 2
            mute_player(target_id, hours, reason="По решению администратора", admin_id=admin_uid)
            bot.send_message(admin_uid, f"✅ Мут на {hours} часов")
        elif action == "ban":
            parts = text.split("|")
            if len(parts) < 2:
                bot.send_message(admin_uid, "❌ Формат: дни | причина")
                return
            days = int(parts[0].strip()) if parts[0].strip().isdigit() else None
            reason = parts[1].strip()
            ban_player(target_id, days=days, reason=reason, admin_id=admin_uid)
            ban_text = f"на {days} дней" if days else "НАВСЕГДА"
            bot.send_message(admin_uid, f"✅ Бан выдан: {ban_text}\nПричина: {reason}")
        elif action == "item":
            parts = text.split("|")
            if len(parts) < 2:
                bot.send_message(admin_uid, "❌ Формат: название | тип | дни")
                return
            name = parts[0].strip()
            item_type = parts[1].strip()
            days = int(parts[2].strip()) if len(parts) > 2 and parts[2].strip().isdigit() else None
            add_inventory_item(target_id, name, item_type, days=days)
            bot.send_message(admin_uid, f"✅ Предмет {name} добавлен")
        elif action == "quals":
            days = int(text) if text.isdigit() else 30
            grant_qual(target_id, "FPL", days)
            bot.send_message(admin_uid, f"✅ FPL Quals выданы на {days} дней")
    except Exception as e:
        bot.send_message(admin_uid, f"❌ Ошибка: {e}")
    
    user_flow.pop(admin_uid, None)
    _show_player_manage(admin_uid, target_id)


# ═══════════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("⚡ ACTUAL FACEIT Bot запущен!")
    bot.infinity_polling(skip_pending=True)