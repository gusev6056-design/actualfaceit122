from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import random

# Цвета как на твоих скриншотах
BRAND_COLORS = {
    "primary": (0, 200, 100),       # Зелёный FLITE
    "secondary": (30, 35, 45),      # Тёмный фон карточек
    "dark": (15, 20, 28),           # Основной фон
    "card": (25, 30, 40),           # Цвет карточек
    "light": (240, 245, 250),       # Светлый текст
    "gold": (255, 200, 0),          # Золотой
    "danger": (255, 60, 60),        # Красный
    "warning": (255, 150, 50),      # Оранжевый
    "info": (50, 150, 255),         # Синий
    "accent": (255, 100, 50),       # Акцент
    "purple": (150, 50, 200),       # Фиолетовый
    "ct": (50, 100, 200),           # CT команда
    "t": (200, 100, 50),            # T команда
}

def get_font(size, bold=False):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\Arial.ttf",
    ]
    bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica-Bold.ttc",
        "C:\\Windows\\Fonts\\Arialbd.ttf",
    ]
    try:
        if bold:
            return ImageFont.truetype(bold_paths[0], size)
        return ImageFont.truetype(font_paths[0], size)
    except:
        try:
            return ImageFont.truetype(font_paths[1], size)
        except:
            return ImageFont.load_default()

def draw_rounded_rectangle(draw, xy, radius, fill, outline=None):
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=fill)
    draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=fill)

def create_profile_card(player, stats, badges, league_name):
    """Профиль как на твоём скриншоте"""
    width, height = 800, 900
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Верхняя зелёная полоса с ACTUAL FACEIT
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 180, 18), "PROFILE", fill=BRAND_COLORS["gold"], font=get_font(20, bold=True))
    
    # Аватар и имя как на скриншоте
    draw.text((40, 90), f"#{player[0]}", fill=BRAND_COLORS["light"], font=get_font(18))
    draw.text((40, 125), f"{player[1]} ★", fill=BRAND_COLORS["gold"], font=get_font(32, bold=True))
    
    # Бейджи (Лоутаб, PREMIUM и т.д.)
    badge_x = 40
    for badge in badges[:3]:
        badge_colors = {
            "admin": BRAND_COLORS["danger"],
            "premium": BRAND_COLORS["gold"],
            "lowtab": BRAND_COLORS["info"],
            "wheelchair": (120, 120, 120)
        }
        color = badge_colors.get(badge, BRAND_COLORS["accent"])
        draw_rounded_rectangle(draw, [badge_x, 170, badge_x + 70, 195], 10, color)
        draw.text((badge_x + 12, 177), badge[:6], fill=BRAND_COLORS["light"], font=get_font(14))
        badge_x += 80
    
    # Устройство и премиум
    draw.text((40, 210), player[3] or "MOBILE", fill=BRAND_COLORS["light"], font=get_font(16))
    if "premium" in badges:
        draw.text((160, 210), "PREMIUM", fill=BRAND_COLORS["gold"], font=get_font(16, bold=True))
    
    # Левая колонка с цифрами (LVL, GAME, MVP, K/D, AVG, ELO)
    left_x = 40
    draw.text((left_x, 250), "УРОВЕНЬ", fill=BRAND_COLORS["light"], font=get_font(14))
    draw.text((left_x, 270), str(stats["level"]), fill=BRAND_COLORS["gold"], font=get_font(28, bold=True))
    
    draw.text((left_x + 80, 250), "GAME", fill=BRAND_COLORS["light"], font=get_font(14))
    draw.text((left_x + 80, 270), str(stats["games"]), fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    
    draw.text((left_x + 160, 250), "MVP", fill=BRAND_COLORS["light"], font=get_font(14))
    draw.text((left_x + 160, 270), str(stats["mvp"]), fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    
    draw.text((left_x + 240, 250), "K/D", fill=BRAND_COLORS["light"], font=get_font(14))
    draw.text((left_x + 240, 270), str(stats["kd"]), fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    
    draw.text((left_x + 320, 250), "AVG", fill=BRAND_COLORS["light"], font=get_font(14))
    draw.text((left_x + 320, 270), str(stats["kills"] // max(stats["games"], 1)), fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    
    draw.text((left_x + 400, 250), "ELO", fill=BRAND_COLORS["light"], font=get_font(14))
    draw.text((left_x + 400, 270), str(stats["elo"]), fill=BRAND_COLORS["gold"], font=get_font(28, bold=True))
    
    # Карточка статистики
    stat_y = 330
    draw_rounded_rectangle(draw, [30, stat_y, width - 30, stat_y + 120], 15, BRAND_COLORS["card"])
    
    # Заголовки таблицы статистики
    headers = ["MAP INFO", "K", "D", "A", "K/D", "AVG", "IMP", "LEAGUE", "SCORE", "ELO"]
    x_positions = [50, 130, 180, 230, 280, 330, 380, 440, 520, 600]
    for i, h in enumerate(headers):
        draw.text((x_positions[i], stat_y + 10), h, fill=BRAND_COLORS["accent"], font=get_font(12, bold=True))
    
    # Пример данных матчей (последние 3)
    matches_data = [
        {"map": "Rust", "k": 18, "d": 5, "a": 2, "kd": 3.60, "avg": 18, "imp": 2.52, "score": "13:2", "elo": "+25"},
        {"map": "Sakura", "k": 28, "d": 15, "a": 5, "kd": 1.87, "avg": 28, "imp": 1.68, "score": "13:11", "elo": "+25"},
        {"map": "Breeze", "k": 33, "d": 10, "a": 7, "kd": 3.30, "avg": 33, "imp": 2.64, "score": "13:7", "elo": "+25"},
    ]
    
    match_y = stat_y + 35
    for i, m in enumerate(matches_data[:3]):
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, match_y, width - 30, match_y + 28], 8, color)
        draw.text((50, match_y + 5), m["map"], fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((130, match_y + 5), str(m["k"]), fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((180, match_y + 5), str(m["d"]), fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((230, match_y + 5), str(m["a"]), fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((280, match_y + 5), str(m["kd"]), fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((330, match_y + 5), str(m["avg"]), fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((380, match_y + 5), str(m["imp"]), fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((460, match_y + 5), "F", fill=BRAND_COLORS["gold"], font=get_font(14))
        draw.text((520, match_y + 5), m["score"], fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((610, match_y + 5), m["elo"], fill=BRAND_COLORS["primary"], font=get_font(14))
        match_y += 32
    
    # Нижняя часть с winstrike и графиками
    bottom_y = match_y + 15
    
    # Winstrike блок
    draw_rounded_rectangle(draw, [30, bottom_y, width // 2 - 15, bottom_y + 140], 15, BRAND_COLORS["card"])
    draw.text((50, bottom_y + 10), "WINSTRIKE INFO", fill=BRAND_COLORS["gold"], font=get_font(16, bold=True))
    
    wins = stats["wins"]
    losses = stats["losses"]
    winrate = stats["winrate"]
    
    draw.text((50, bottom_y + 45), f"W {wins}", fill=BRAND_COLORS["primary"], font=get_font(20, bold=True))
    draw.text((130, bottom_y + 45), f"L {losses}", fill=BRAND_COLORS["danger"], font=get_font(20, bold=True))
    draw.text((50, bottom_y + 80), f"WINRATE {winrate}%", fill=BRAND_COLORS["light"], font=get_font(18, bold=True))
    draw.text((50, bottom_y + 110), "Most Kills", fill=BRAND_COLORS["light"], font=get_font(14))
    draw.text((50, bottom_y + 130), str(stats["kills"]), fill=BRAND_COLORS["gold"], font=get_font(18, bold=True))
    
    # График ELO
    draw_rounded_rectangle(draw, [width // 2 + 15, bottom_y, width - 30, bottom_y + 140], 15, BRAND_COLORS["card"])
    draw.text((width // 2 + 35, bottom_y + 10), "GROWTH ELO", fill=BRAND_COLORS["gold"], font=get_font(16, bold=True))
    
    # Рисуем простой график
    graph_y = bottom_y + 50
    for i in range(5):
        x = width // 2 + 40 + i * 35
        height_val = random.randint(30, 100)
        draw.rectangle([x, graph_y + 60 - height_val, x + 20, graph_y + 60], fill=BRAND_COLORS["primary"])
    
    draw.text((width // 2 + 35, bottom_y + 115), "15", fill=BRAND_COLORS["light"], font=get_font(12))
    draw.text((width // 2 + 70, bottom_y + 115), "0", fill=BRAND_COLORS["light"], font=get_font(12))
    draw.text((width // 2 + 105, bottom_y + 115), "-15", fill=BRAND_COLORS["light"], font=get_font(12))
    draw.text((width // 2 + 140, bottom_y + 115), "-30", fill=BRAND_COLORS["light"], font=get_font(12))
    
    # Нижний текст
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    return _to_bytes(img)

def create_top_card(players):
    """Топ игроков как на скриншоте"""
    width, height = 800, 700
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 180, 18), "ЛУЧШИЕ ИГРОКИ", fill=BRAND_COLORS["gold"], font=get_font(18, bold=True))
    
    # Заголовки
    draw.text((40, 90), "Default", fill=BRAND_COLORS["gold"], font=get_font(24, bold=True))
    draw.text((180, 90), "Season 4", fill=BRAND_COLORS["light"], font=get_font(16))
    
    # Таблица
    headers = ["PLACE", "PLAYER", "GAMES", "WINRATE", "POINTS", "K/D", "AVG"]
    x_pos = [40, 100, 280, 380, 480, 580, 660]
    y = 130
    
    for i, h in enumerate(headers):
        draw.text((x_pos[i], y), h, fill=BRAND_COLORS["accent"], font=get_font(12, bold=True))
    
    y += 25
    
    for i, (name, gid, elo, wins, losses, kills, deaths) in enumerate(players[:8], 1):
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 40], 8, color)
        
        if i == 1:
            draw.text((45, y + 10), "1", fill=BRAND_COLORS["gold"], font=get_font(18, bold=True))
        else:
            draw.text((48, y + 10), str(i), fill=BRAND_COLORS["light"], font=get_font(16))
        
        draw.text((100, y + 10), name[:18], fill=BRAND_COLORS["light"], font=get_font(16))
        
        games = wins + losses
        draw.text((285, y + 10), f"Win {wins}", fill=BRAND_COLORS["primary"], font=get_font(12))
        draw.text((285, y + 25), f"Lose {losses}", fill=BRAND_COLORS["danger"], font=get_font(12))
        
        winrate = round(wins / games * 100, 1) if games > 0 else 0
        draw.text((390, y + 15), f"{winrate}%", fill=BRAND_COLORS["light"], font=get_font(14))
        
        draw.text((490, y + 15), str(elo), fill=BRAND_COLORS["gold"], font=get_font(14))
        
        kd = round(kills / deaths, 2) if deaths > 0 else kills
        draw.text((590, y + 15), str(kd), fill=BRAND_COLORS["light"], font=get_font(14))
        
        avg = kills // games if games > 0 else 0
        draw.text((670, y + 15), str(avg), fill=BRAND_COLORS["light"], font=get_font(14))
        
        y += 45
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 120, height - 20), "ACTUAL FACEIT · Лучшие игроки", fill=BRAND_COLORS["light"], font=get_font(14))
    
    return _to_bytes(img)

def create_shop_card(category, items, coins):
    """Магазин как на скриншоте"""
    width, height = 800, 700
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 150, 18), "МАГАЗИН", fill=BRAND_COLORS["gold"], font=get_font(22, bold=True))
    draw.text((width - 130, 45), f"💰 {coins}", fill=BRAND_COLORS["gold"], font=get_font(16, bold=True))
    
    y = 90
    
    if category == "skins":
        draw.text((30, y), "СКИНЫ", fill=BRAND_COLORS["accent"], font=get_font(26, bold=True))
        y += 50
        skin_items = [
            {"name": "Butterfly 'Legacy'", "price": 1500},
            {"name": "M9 Bayonet 'Frozen'", "price": 1200},
            {"name": "Karambit 'Dragon Glass'", "price": 2000},
            {"name": "FlipKnife 'Stone Cold'", "price": 800},
            {"name": "StatTrack M4A1 'Bubblegum'", "price": 600},
            {"name": "StatTrack AKR 'Necromancer'", "price": 750},
        ]
        for i, item in enumerate(skin_items):
            color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
            draw_rounded_rectangle(draw, [30, y, width - 30, y + 50], 10, color)
            draw.text((50, y + 12), item["name"], fill=BRAND_COLORS["light"], font=get_font(18))
            draw.text((width - 120, y + 12), f"{item['price']} 💰", fill=BRAND_COLORS["gold"], font=get_font(16, bold=True))
            y += 55
    
    elif category == "decor":
        draw.text((30, y), "ДЕКОР", fill=BRAND_COLORS["accent"], font=get_font(26, bold=True))
        y += 50
        decor_items = [
            {"name": "Фон 'Склеп неизвестного'", "price": 300},
            {"name": "Баннер 'Helper'", "price": 150},
            {"name": "Баннер 'Guard'", "price": 200},
            {"name": "Рамка 'Золотая'", "price": 500},
            {"name": "Стикер 'Flite'", "price": 50},
        ]
        for i, item in enumerate(decor_items):
            color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
            draw_rounded_rectangle(draw, [30, y, width - 30, y + 50], 10, color)
            draw.text((50, y + 12), item["name"], fill=BRAND_COLORS["light"], font=get_font(18))
            draw.text((width - 120, y + 12), f"{item['price']} 💰", fill=BRAND_COLORS["gold"], font=get_font(16, bold=True))
            y += 55
    
    else:  # goods
        draw.text((30, y), "ТОВАРЫ", fill=BRAND_COLORS["accent"], font=get_font(26, bold=True))
        y += 50
        goods_items = [
            {"name": "Premium Статус", "price": 600, "days": 30},
            {"name": "x2 Farm Coins", "price": 300, "days": 7},
            {"name": "FPL Quals", "price": 1000, "days": 30},
            {"name": "Снять Warn", "price": 500},
            {"name": "Сброс статистики", "price": 800},
            {"name": "Изменить никнейм", "price": 300},
        ]
        for i, item in enumerate(goods_items):
            color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
            draw_rounded_rectangle(draw, [30, y, width - 30, y + 50], 10, color)
            draw.text((50, y + 12), item["name"], fill=BRAND_COLORS["light"], font=get_font(18))
            days_text = f"{item.get('days', '')}д" if item.get('days') else ""
            draw.text((width - 200, y + 12), days_text, fill=BRAND_COLORS["info"], font=get_font(14))
            draw.text((width - 120, y + 12), f"{item['price']} 💰", fill=BRAND_COLORS["gold"], font=get_font(16, bold=True))
            y += 55
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    return _to_bytes(img)

def create_inventory_card(player, inventory):
    """Инвентарь как на скриншоте"""
    width, height = 800, 700
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], get_font(28, bold=True))
    draw.text((width - 180, 18), "ИНВЕНТАРЬ", fill=BRAND_COLORS["gold"], get_font(20, bold=True))
    
    draw.text((40, 80), f"#{player[0]}", fill=BRAND_COLORS["light"], get_font(16))
    draw.text((40, 105), f"{player[1]} ★", fill=BRAND_COLORS["gold"], get_font(24, bold=True))
    
    draw.text((40, 140), "Здесь хранятся все дорогие вам предметы!", fill=BRAND_COLORS["light"], get_font(14))
    
    y = 180
    
    if not inventory:
        draw.text((width // 2 - 100, y + 50), "Инвентарь пуст", fill=BRAND_COLORS["light"], get_font(20))
    else:
        for i, (inv_id, item_name, item_type, item_id, activated, expires) in enumerate(inventory[:8]):
            color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
            draw_rounded_rectangle(draw, [30, y, width - 30, y + 55], 10, color)
            
            status = "Активирован" if activated else "Не активирован"
            status_color = BRAND_COLORS["primary"] if activated else BRAND_COLORS["warning"]
            
            draw.text((50, y + 12), item_name[:30], fill=BRAND_COLORS["light"], get_font(18))
            draw.text((50, y + 35), status, fill=status_color, get_font(12))
            
            if expires:
                try:
                    exp_date = datetime.fromisoformat(expires)
                    days_left = (exp_date - datetime.now()).days
                    if days_left > 0 and activated:
                        draw.text((width - 100, y + 20), f"{days_left}д.", fill=BRAND_COLORS["gold"], get_font(16))
                except:
                    pass
            
            if item_id:
                draw.text((width - 150, y + 35), f"{item_id}", fill=BRAND_COLORS["info"], get_font(12))
            
            y += 65
    
    draw.text((width // 2 - 50, height - 35), "Страница 1 из 1", fill=BRAND_COLORS["light"], get_font(14))
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], get_font(14, bold=True))
    
    return _to_bytes(img)

def create_lobby_card(league, lobbies):
    """Лобби"""
    width, height = 800, 500
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], get_font(28, bold=True))
    draw.text((width - 150, 18), "ЛОББИ", fill=BRAND_COLORS["gold"], get_font(22, bold=True))
    
    y = 90
    league_name = "QUALS" if league == "quals" else "DEFAULT"
    draw.text((width // 2 - 60, y), f"ЛИГА {league_name}", fill=BRAND_COLORS["accent"], get_font(24, bold=True))
    
    y += 60
    
    # MOBILE
    draw.text((50, y), "MOBILE", fill=BRAND_COLORS["info"], get_font(20, bold=True))
    for slot in range(1, 6):
        key = f"{league}_MOBILE_{slot}"
        lob = next((l for l in lobbies if l["slot"] == slot and l["device"] == "MOBILE"), None)
        count = lob["count"] if lob else 0
        emoji = "🟢" if count > 0 else "⚪"
        draw.text((50 + (slot - 1) * 100, y + 30), f"{emoji} {slot}({count})", fill=BRAND_COLORS["light"], get_font(14))
    
    y += 70
    
    # PC
    draw.text((50, y), "PC", fill=BRAND_COLORS["info"], get_font(20, bold=True))
    for slot in range(1, 6):
        key = f"{league}_PC_{slot}"
        lob = next((l for l in lobbies if l["slot"] == slot and l["device"] == "PC"), None)
        count = lob["count"] if lob else 0
        emoji = "🟢" if count > 0 else "⚪"
        draw.text((50 + (slot - 1) * 100, y + 30), f"{emoji} {slot}({count})", fill=BRAND_COLORS["light"], get_font(14))
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], get_font(14, bold=True))
    
    return _to_bytes(img)

def create_map_card(lobby, map_stats):
    """Вето карт"""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], get_font(28, bold=True))
    draw.text((width - 130, 18), "ВЕТО", fill=BRAND_COLORS["gold"], get_font(22, bold=True))
    
    y = 90
    draw.text((30, y), f"Бан {lobby['ban_count']}/4", fill=BRAND_COLORS["accent"], get_font(24, bold=True))
    
    turn = "CT" if lobby["veto_turn"] == "ct" else "T"
    draw.text((width - 150, y), f"ХОД: {turn}", fill=BRAND_COLORS["gold"], get_font(20, bold=True))
    
    y += 50
    draw.text((30, y), "Доступные карты:", fill=BRAND_COLORS["light"], get_font(18))
    y += 35
    
    for i, map_name in enumerate(lobby["map_pool"][:5]):
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 45], 10, color)
        draw.text((50, y + 10), f"❌ {map_name}", fill=BRAND_COLORS["light"], get_font(18))
        y += 50
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], get_font(14, bold=True))
    
    return _to_bytes(img)

def create_match_start_card(match_id, map_name, league, team_ct, team_t, ct_players, t_players):
    """Начало матча"""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], get_font(28, bold=True))
    draw.text((width - 100, 18), f"МАТЧ #{match_id}", fill=BRAND_COLORS["gold"], get_font(20, bold=True))
    
    y = 90
    draw.text((30, y), f"Карта: {map_name}", fill=BRAND_COLORS["accent"], get_font(24, bold=True))
    draw.text((width - 150, y), league.upper(), fill=BRAND_COLORS["gold"], get_font(18, bold=True))
    
    y += 60
    
    # CT
    draw_rounded_rectangle(draw, [30, y, width // 2 - 20, y + 250], 15, (30, 50, 70))
    draw.text((width // 4 - 50, y + 10), "🟦 CT", fill=BRAND_COLORS["info"], get_font(20, bold=True))
    
    ct_y = y + 50
    for i, (uid, p) in enumerate(zip(team_ct[:5], ct_players[:5])):
        if p:
            draw.text((50, ct_y), f"{i+1}. {p[1]}", fill=BRAND_COLORS["light"], get_font(16))
            draw.text((width // 2 - 140, ct_y), f"LVL {p[4]}", fill=BRAND_COLORS["gold"], get_font(12))
        ct_y += 35
    
    # T
    tx = width // 2 + 20
    draw_rounded_rectangle(draw, [tx, y, width - 30, y + 250], 15, (70, 50, 30))
    draw.text((tx + width // 4 - 50, y + 10), "🟧 T", fill=BRAND_COLORS["warning"], get_font(20, bold=True))
    
    t_y = y + 50
    for i, (uid, p) in enumerate(zip(team_t[:5], t_players[:5])):
        if p:
            draw.text((tx + 20, t_y), f"{i+1}. {p[1]}", fill=BRAND_COLORS["light"], get_font(16))
            draw.text((tx + 200, t_y), f"LVL {p[4]}", fill=BRAND_COLORS["gold"], get_font(12))
        t_y += 35
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], get_font(14, bold=True))
    
    return _to_bytes(img)

def create_match_result_card(match_id, map_name, league, score_ct, score_t, winner, ct_players, t_players):
    """Результат матча"""
    width, height = 800, 700
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    winner_color = BRAND_COLORS["primary"] if winner == "ct" else BRAND_COLORS["warning"]
    draw.rectangle([0, 0, width, 60], fill=winner_color)
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], get_font(28, bold=True))
    draw.text((width - 100, 18), f"#{match_id}", fill=BRAND_COLORS["gold"], get_font(20, bold=True))
    
    y = 90
    draw.text((width // 2 - 50, y), f"{score_ct} : {score_t}", fill=winner_color, get_font(48, bold=True))
    y += 60
    draw.text((width // 2 - 100, y), f"ПОБЕДИЛА {'CT' if winner == 'ct' else 'T'}", fill=BRAND_COLORS["gold"], get_font(20, bold=True))
    
    y += 50
    draw.text((30, y), f"Карта: {map_name}", fill=BRAND_COLORS["accent"], get_font(18))
    
    y += 40
    draw.text((30, y), "СТАТИСТИКА ИГРОКОВ:", fill=BRAND_COLORS["light"], get_font(18, bold=True))
    y += 30
    
    headers = ["ИГРОК", "K", "D", "A", "K/D"]
    x_pos = [50, 300, 380, 460, 540]
    for i, h in enumerate(headers):
        draw.text((x_pos[i], y), h, fill=BRAND_COLORS["accent"], get_font(14, bold=True))
    y += 25
    
    all_players = []
    for p, k, d, a in ct_players + t_players:
        if p:
            kd = round(k / d, 2) if d > 0 else k
            all_players.append((p, k, d, a, kd))
    
    for i, (p, k, d, a, kd) in enumerate(all_players[:10]):
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 30], 8, color)
        draw.text((50, y + 5), p[1][:18], fill=BRAND_COLORS["light"], font_get_font(14))
        draw.text((310, y + 5), str(k), fill=BRAND_COLORS["light"], font_get_font(14))
        draw.text((390, y + 5), str(d), fill=BRAND_COLORS["light"], font_get_font(14))
        draw.text((470, y + 5), str(a), fill=BRAND_COLORS["light"], font_get_font(14))
        draw.text((550, y + 5), str(kd), fill=BRAND_COLORS["gold"], font_get_font(14))
        y += 35
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], get_font(14, bold=True))
    
    return _to_bytes(img)

def _to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf