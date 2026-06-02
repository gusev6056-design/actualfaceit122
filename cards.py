from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime

BRAND_COLORS = {
    "primary": (0, 200, 100),
    "secondary": (30, 40, 50),
    "dark": (15, 20, 28),
    "card": (25, 30, 40),
    "light": (240, 245, 250),
    "gold": (255, 200, 0),
    "silver": (192, 192, 192),
    "bronze": (205, 127, 50),
    "danger": (255, 60, 60),
    "warning": (255, 150, 50),
    "info": (50, 150, 255),
    "accent": (255, 100, 50),
    "ct": (50, 100, 200),
    "t": (200, 100, 50),
}

# Ранги по ELO
RANKS = {
    1: ("IRON 1", (80, 80, 80)),
    2: ("IRON 2", (90, 90, 90)),
    3: ("BRONZE 1", (205, 127, 50)),
    4: ("BRONZE 2", (205, 127, 50)),
    5: ("SILVER 1", (192, 192, 192)),
    6: ("SILVER 2", (192, 192, 192)),
    7: ("GOLD 1", (255, 215, 0)),
    8: ("GOLD 2", (255, 215, 0)),
    9: ("PLATINUM", (0, 200, 100)),
    10: ("DIAMOND", (0, 150, 255)),
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
            if bold:
                return ImageFont.truetype(bold_paths[1], size)
            return ImageFont.truetype(font_paths[1], size)
        except:
            return ImageFont.load_default()

def draw_rounded_rectangle(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=fill)
    draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=fill)

def get_rank_color(level):
    return RANKS.get(level, ("UNKNOWN", (150, 150, 150)))[1]

def get_rank_name(level):
    return RANKS.get(level, ("UNKNOWN", (150, 150, 150)))[0]

def create_profile_card(player, stats, badges, map_stats):
    """Профиль как в Walker Faceit"""
    width, height = 800, 900
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка с градиентом
    draw.rectangle([0, 0, width, 80], fill=BRAND_COLORS["primary"])
    draw.text((30, 25), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 150, 28), "PROFILE", fill=BRAND_COLORS["gold"], font=get_font(20, bold=True))
    
    # Информация об игроке
    rank_color = get_rank_color(stats["level"])
    rank_name = get_rank_name(stats["level"])
    
    draw.text((40, 110), player[1], fill=BRAND_COLORS["gold"], font=get_font(32, bold=True))
    draw.text((40, 155), f"ID: {player[0]}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((40, 180), f"Game ID: {player[2]}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((40, 205), f"Device: {player[3] or 'MOBILE'}", fill=BRAND_COLORS["light"], font=get_font(16))
    
    # Ранг и ELO
    draw_rounded_rectangle(draw, [40, 235, 200, 285], 15, rank_color)
    draw.text((120 - 30, 248), rank_name, fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    draw.text((120 - 20, 268), f"{stats['elo']} ELO", fill=BRAND_COLORS["light"], font=get_font(12))
    
    # Бейджи
    badge_x = 220
    for badge in badges[:3]:
        badge_colors = {
            "admin": BRAND_COLORS["danger"],
            "premium": BRAND_COLORS["gold"],
            "lowtab": BRAND_COLORS["info"],
            "hightab": BRAND_COLORS["warning"],
            "veteran": (100, 100, 200)
        }
        color = badge_colors.get(badge, BRAND_COLORS["accent"])
        draw_rounded_rectangle(draw, [badge_x, 245, badge_x + 80, 275], 10, color)
        draw.text((badge_x + 15, 255), badge[:8], fill=BRAND_COLORS["light"], font=get_font(12))
        badge_x += 90
    
    # Статистика
    draw_rounded_rectangle(draw, [30, 310, width - 30, 430], 15, BRAND_COLORS["card"])
    draw.text((50, 330), "СТАТИСТИКА", fill=BRAND_COLORS["accent"], font=get_font(18, bold=True))
    
    draw.text((60, 365), f"Убийства: {stats['kills']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((60, 395), f"Смерти: {stats['deaths']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((60, 425), f"Ассисты: {stats['assists']}", fill=BRAND_COLORS["light"], font=get_font(16))
    
    draw.text((300, 365), f"Победы: {stats['wins']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((300, 395), f"Поражения: {stats['losses']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((300, 425), f"Матчей: {stats['games']}", fill=BRAND_COLORS["light"], font=get_font(16))
    
    draw.text((540, 365), f"K/D: {stats['kd']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((540, 395), f"Винрейт: {stats['winrate']}%", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((540, 425), f"ХС: {stats['headshots']}%", fill=BRAND_COLORS["light"], font=get_font(16))
    
    # Статистика по картам
    draw_rounded_rectangle(draw, [30, 450, width - 30, 650], 15, BRAND_COLORS["card"])
    draw.text((50, 470), "СТАТИСТИКА ПО КАРТАМ", fill=BRAND_COLORS["accent"], font=get_font(18, bold=True))
    
    y = 510
    for map_name, data in list(map_stats.items())[:5]:
        winrate_color = BRAND_COLORS["primary"] if data["winrate"] >= 50 else BRAND_COLORS["danger"]
        draw.text((50, y), map_name, fill=BRAND_COLORS["gold"], font=get_font(16, bold=True))
        draw.text((200, y), f"W: {data['wins']}", fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((280, y), f"L: {data['losses']}", fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((360, y), f"WR: {data['winrate']}%", fill=winrate_color, font=get_font(14))
        draw.text((480, y), f"K/D: {data['kd']}", fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((600, y), f"K: {data['kills']}", fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((680, y), f"D: {data['deaths']}", fill=BRAND_COLORS["light"], font=get_font(14))
        y += 35
    
    # Нижняя полоса
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_lobby_card(lobby_id, players, league, player_count):
    """Карточка лобби (как в Walker Faceit)"""
    width, height = 800, 500
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    
    # Информация о лобби
    y = 90
    draw.text((30, y), f"Лобби #{lobby_id} ({league})", fill=BRAND_COLORS["accent"], font=get_font(24, bold=True))
    draw.text((width - 200, y), f"Игроков: {player_count}/10", fill=BRAND_COLORS["gold"], font=get_font(18, bold=True))
    
    y += 50
    draw.text((30, y), "Игроки в лобби:", fill=BRAND_COLORS["light"], font=get_font(18))
    y += 35
    
    for i, (uid, name, calib_text) in enumerate(players, 1):
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 40], 10, color)
        draw.text((50, y + 10), f"{i}. {name}", fill=BRAND_COLORS["light"], font=get_font(16))
        draw.text((width - 150, y + 10), calib_text, fill=BRAND_COLORS["gold"], font=get_font(14))
        y += 45
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_lobbies_list_card(lobbies_data, league):
    """Список всех лобби (как в Walker Faceit)"""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 150, 18), f"{league.upper()} LOBBIES", fill=BRAND_COLORS["gold"], font_get_font(20, bold=True))
    
    y = 90
    draw.text((30, y), "Лобби 5v5", fill=BRAND_COLORS["accent"], font_get_font(22, bold=True))
    
    y += 50
    # Mobile и PC ряды
    draw.text((50, y), "Mobile", fill=BRAND_COLORS["info"], font_get_font(18, bold=True))
    draw.text((450, y), "PC", fill=BRAND_COLORS["info"], font_get_font(18, bold=True))
    y += 35
    
    for i in range(1, 11):
        mobile_count = lobbies_data.get(f"mobile_{i}", 0)
        pc_count = lobbies_data.get(f"pc_{i}", 0)
        
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 35], 10, color)
        
        draw.text((50, y + 8), f"Лобби #{i}", fill=BRAND_COLORS["gold"], font_get_font(14, bold=True))
        draw.text((150, y + 8), f"({mobile_count}/10)", fill=BRAND_COLORS["light"], font_get_font(14))
        draw.text((500, y + 8), f"({pc_count}/10)", fill=BRAND_COLORS["light"], font_get_font(14))
        
        y += 40
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font_get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_top_card(players):
    """Топ игроков"""
    width, height = 800, 700
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font_get_font(28, bold=True))
    draw.text((width - 120, 18), "TOP PLAYERS", fill=BRAND_COLORS["gold"], font_get_font(20, bold=True))
    
    y = 100
    headers = ["#", "PLAYER", "ELO", "W/L", "K/D"]
    x_pos = [50, 120, 400, 520, 650]
    for i, h in enumerate(headers):
        draw.text((x_pos[i], y), h, fill=BRAND_COLORS["accent"], font_get_font(16, bold=True))
    
    y += 40
    
    for i, (name, elo, wins, losses, kills, deaths) in enumerate(players[:10], 1):
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 45], 10, color)
        
        if i == 1:
            draw.text((55, y + 12), "🥇", fill=BRAND_COLORS["gold"], font_get_font(18))
        elif i == 2:
            draw.text((55, y + 12), "🥈", fill=BRAND_COLORS["silver"], font_get_font(18))
        elif i == 3:
            draw.text((55, y + 12), "🥉", fill=BRAND_COLORS["bronze"], font_get_font(18))
        else:
            draw.text((58, y + 12), str(i), fill=BRAND_COLORS["light"], font_get_font(16))
        
        draw.text((120, y + 12), name[:18], fill=BRAND_COLORS["light"], font_get_font(16))
        draw.text((410, y + 12), str(elo), fill=BRAND_COLORS["accent"], font_get_font(16, bold=True))
        
        games = wins + losses
        winrate = round(wins / games * 100, 1) if games > 0 else 0
        draw.text((520, y + 12), f"{wins}/{losses} ({winrate}%)", fill=BRAND_COLORS["light"], font_get_font(14))
        
        kd = round(kills / deaths, 2) if deaths > 0 else kills
        draw.text((660, y + 12), str(kd), fill=BRAND_COLORS["gold"], font_get_font(16))
        
        y += 50
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 120, height - 20), "ACTUAL FACEIT · BEST PLAYERS", fill=BRAND_COLORS["light"], font_get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_shop_card(category, items, coins):
    """Магазин"""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font_get_font(28, bold=True))
    draw.text((width - 120, 18), "SHOP", fill=BRAND_COLORS["gold"], font_get_font(22, bold=True))
    draw.text((width - 120, 45), f"{coins} WC", fill=BRAND_COLORS["gold"], font_get_font(14, bold=True))
    
    y = 90
    category_names = {"skins": "СКИНЫ", "decor": "ДЕКОР", "goods": "ТОВАРЫ"}
    draw.text((width // 2 - 60, y), category_names.get(category, "ITEMS"), fill=BRAND_COLORS["accent"], font_get_font(26, bold=True))
    
    y += 60
    
    for i, item in enumerate(items[:8]):
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 55], 10, color)
        
        draw.text((100, y + 15), item["name"][:28], fill=BRAND_COLORS["light"], font_get_font(18))
        draw.text((width - 120, y + 15), f"{item['price']} WC", fill=BRAND_COLORS["gold"], font_get_font(16, bold=True))
        
        if item.get("days"):
            draw.text((width - 200, y + 15), f"{item['days']}д", fill=BRAND_COLORS["info"], font_get_font(14))
        
        y += 65
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font_get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_inventory_card(player, inventory):
    """Инвентарь"""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font_get_font(28, bold=True))
    draw.text((width - 140, 18), "INVENTORY", fill=BRAND_COLORS["gold"], font_get_font(20, bold=True))
    
    draw.text((40, 85), player[1], fill=BRAND_COLORS["gold"], font_get_font(24, bold=True))
    draw.text((40, 120), "Ваши предметы:", fill=BRAND_COLORS["light"], font_get_font(16))
    
    y = 160
    
    if not inventory:
        draw.text((width // 2 - 80, height // 2), "Нет предметов", fill=BRAND_COLORS["light"], font_get_font(20))
    else:
        for i, (inv_id, item_name, item_type, item_id, activated, expires) in enumerate(inventory[:8]):
            color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
            draw_rounded_rectangle(draw, [30, y, width - 30, y + 50], 10, color)
            
            status_icon = "✅" if activated else "⚡"
            status_color = BRAND_COLORS["primary"] if activated else BRAND_COLORS["warning"]
            draw.text((50, y + 12), status_icon, fill=status_color, font_get_font(24))
            draw.text((100, y + 12), item_name[:30], fill=BRAND_COLORS["light"], font_get_font(16))
            
            if expires and activated:
                try:
                    exp_date = datetime.fromisoformat(expires)
                    days_left = (exp_date - datetime.now()).days
                    if days_left > 0:
                        draw.text((width - 100, y + 12), f"{days_left}д", fill=BRAND_COLORS["gold"], font_get_font(16))
                except:
                    pass
            
            y += 55
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font_get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_match_registration_card(match_id, map_name, league, team_ct, team_t, ct_players, t_players):
    """Карточка для регистрации матча (как в Walker Faceit)"""
    width, height = 800, 700
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font_get_font(28, bold=True))
    draw.text((width - 150, 18), "REGISTRATION", fill=BRAND_COLORS["gold"], font_get_font(18, bold=True))
    
    y = 90
    draw.text((width // 2 - 80, y), f"МАТЧ #{match_id} НА РЕГИСТРАЦИЮ", fill=BRAND_COLORS["gold"], font_get_font(22, bold=True))
    
    y += 45
    draw.text((width // 2 - 50, y), f"Лига: {league}", fill=BRAND_COLORS["accent"], font_get_font(18))
    draw.text((width // 2 - 50, y + 25), f"Карта: {map_name}", fill=BRAND_COLORS["light"], font_get_font(16))
    
    y += 70
    
    # Команда CT
    draw_rounded_rectangle(draw, [30, y, width // 2 - 20, y + 280], 15, (30, 50, 70))
    draw.text((width // 4 - 40, y + 15), "☑️ КОМАНДА CT", fill=BRAND_COLORS["info"], font_get_font(18, bold=True))
    
    ct_y = y + 55
    for i, (uid, p) in enumerate(zip(team_ct, ct_players)):
        if p:
            draw.text((50, ct_y), f"{i+1}. {p[1]}", fill=BRAND_COLORS["light"], font_get_font(15))
            draw.text((width // 2 - 160, ct_y), f"ID: {uid}", fill=BRAND_COLORS["gold"], font_get_font(12))
            draw.text((width // 2 - 160, ct_y + 18), f"{p[5]} ELO", fill=BRAND_COLORS["info"], font_get_font(12))
        ct_y += 50
    
    # Команда T
    tx = width // 2 + 20
    draw_rounded_rectangle(draw, [tx, y, width - 30, y + 280], 15, (70, 50, 30))
    draw.text((tx + width // 4 - 40, y + 15), "☑️ КОМАНДА T", fill=BRAND_COLORS["warning"], font_get_font(18, bold=True))
    
    t_y = y + 55
    for i, (uid, p) in enumerate(zip(team_t, t_players)):
        if p:
            draw.text((tx + 20, t_y), f"{i+1}. {p[1]}", fill=BRAND_COLORS["light"], font_get_font(15))
            draw.text((tx + 200, t_y), f"ID: {uid}", fill=BRAND_COLORS["gold"], font_get_font(12))
            draw.text((tx + 200, t_y + 18), f"{p[5]} ELO", fill=BRAND_COLORS["info"], font_get_font(12))
        t_y += 50
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font_get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_veto_card(map_name, pick_rate, ct_wr, t_wr):
    """Карточка для вето"""
    width, height = 400, 200
    img = Image.new('RGB', (width, height), BRAND_COLORS["card"])
    draw = ImageDraw.Draw(img)
    
    draw_rounded_rectangle(draw, [0, 0, width, height], 15, BRAND_COLORS["card"])
    draw.text((20, 20), map_name, fill=BRAND_COLORS["gold"], font_get_font(18, bold=True))
    draw.text((20, 55), f"Выбор: {pick_rate}%", fill=BRAND_COLORS["light"], font_get_font(14))
    draw.text((20, 80), f"CT Winrate: {ct_wr}%", fill=BRAND_COLORS["info"], font_get_font(14))
    draw.text((20, 105), f"T Winrate: {t_wr}%", fill=BRAND_COLORS["warning"], font_get_font(14))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_party_card(party_code, members, leader_name):
    """Карточка пати"""
    width, height = 800, 400
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font_get_font(28, bold=True))
    draw.text((width - 120, 18), "PARTY", fill=BRAND_COLORS["gold"], font_get_font(20, bold=True))
    
    draw.text((40, 90), f"Код пати: <code>{party_code}</code>", fill=BRAND_COLORS["accent"], font_get_font(20), parse_mode="HTML")
    draw.text((40, 125), f"Лидер: {leader_name}", fill=BRAND_COLORS["gold"], font_get_font(16))
    
    y = 170
    draw.text((40, y), "Участники:", fill=BRAND_COLORS["light"], font_get_font(18))
    y += 35
    
    for i, name in enumerate(members, 1):
        draw.text((60, y), f"{i}. {name}", fill=BRAND_COLORS["light"], font_get_font(16))
        y += 30
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font_get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf