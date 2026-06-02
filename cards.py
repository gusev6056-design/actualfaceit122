from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import random

BRAND_COLORS = {
    "primary": (0, 200, 100),
    "secondary": (30, 40, 50),
    "dark": (15, 20, 28),
    "card": (25, 30, 40),
    "light": (240, 245, 250),
    "gold": (255, 200, 0),
    "danger": (255, 60, 60),
    "warning": (255, 150, 50),
    "info": (50, 150, 255),
    "accent": (255, 100, 50),
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

def create_profile_card(player, stats, badges, league_name):
    width, height = 800, 500
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 100, 18), "PROFILE", fill=BRAND_COLORS["gold"], font=get_font(20, bold=True))
    
    # Информация об игроке
    draw.text((40, 90), f"#{player[0]}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((40, 120), player[1], fill=BRAND_COLORS["gold"], font=get_font(32, bold=True))
    
    # Бейджи
    badge_x = 40
    for badge in badges[:3]:
        badge_colors = {
            "admin": BRAND_COLORS["danger"],
            "premium": BRAND_COLORS["gold"],
            "lowtab": BRAND_COLORS["info"],
            "wheelchair": (120, 120, 120)
        }
        color = badge_colors.get(badge, BRAND_COLORS["accent"])
        draw_rounded_rectangle(draw, [badge_x, 165, badge_x + 70, 190], 10, color)
        draw.text((badge_x + 12, 172), badge[:6], fill=BRAND_COLORS["light"], font=get_font(14))
        badge_x += 80
    
    # Устройство
    draw.text((40, 210), f"Device: {player[3] or 'MOBILE'}", fill=BRAND_COLORS["light"], font=get_font(16))
    
    # Основные показатели
    draw.text((40, 250), f"Level: {stats['level']}", fill=BRAND_COOLORS["accent"], font=get_font(24, bold=True))
    draw.text((200, 250), f"ELO: {stats['elo']}", fill=BRAND_COLORS["gold"], font=get_font(24, bold=True))
    draw.text((400, 250), f"Coins: {stats['coins']}", fill=BRAND_COLORS["light"], font=get_font(20))
    
    # Статистика
    draw_rounded_rectangle(draw, [30, 300, width - 30, 420], 15, BRAND_COLORS["card"])
    
    draw.text((50, 320), f"Kills: {stats['kills']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((50, 350), f"Deaths: {stats['deaths']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((50, 380), f"Assists: {stats['assists']}", fill=BRAND_COLORS["light"], font=get_font(16))
    
    draw.text((300, 320), f"Wins: {stats['wins']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((300, 350), f"Losses: {stats['losses']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((300, 380), f"K/D: {stats['kd']}", fill=BRAND_COLORS["light"], font=get_font(16))
    
    draw.text((550, 320), f"Winrate: {stats['winrate']}%", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((550, 350), f"MVP: {stats['mvp']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((550, 380), f"Headshots: {stats['headshots']}%", fill=BRAND_COLORS["light"], font=get_font(16))
    
    # Нижняя полоса
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    return _to_bytes(img)

def create_top_card(players):
    width, height = 800, 700
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 150, 18), "TOP PLAYERS", fill=BRAND_COLORS["gold"], font=get_font(20, bold=True))
    
    # Заголовки
    headers = ["#", "PLAYER", "ELO", "W/L", "K/D"]
    x_pos = [50, 120, 400, 520, 650]
    y = 100
    for i, h in enumerate(headers):
        draw.text((x_pos[i], y), h, fill=BRAND_COLORS["accent"], font=get_font(16, bold=True))
    
    y += 35
    
    for i, (name, gid, elo, wins, losses, kills, deaths) in enumerate(players[:10], 1):
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 45], 10, color)
        
        if i == 1:
            draw.text((55, y + 12), "1", fill=BRAND_COLORS["gold"], font=get_font(18, bold=True))
        else:
            draw.text((58, y + 12), str(i), fill=BRAND_COLORS["light"], font=get_font(16))
        
        draw.text((120, y + 12), name[:18], fill=BRAND_COLORS["light"], font=get_font(16))
        draw.text((410, y + 12), str(elo), fill=BRAND_COLORS["accent"], font=get_font(16, bold=True))
        
        games = wins + losses
        winrate = round(wins / games * 100, 1) if games > 0 else 0
        draw.text((520, y + 12), f"{wins}/{losses} ({winrate}%)", fill=BRAND_COLORS["light"], font=get_font(14))
        
        kd = round(kills / deaths, 2) if deaths > 0 else kills
        draw.text((660, y + 12), str(kd), fill=BRAND_COLORS["gold"], font=get_font(16))
        
        y += 50
    
    # Нижняя полоса
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 120, height - 20), "ACTUAL FACEIT · BEST PLAYERS", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    return _to_bytes(img)

def create_shop_card(category, items, coins):
    width, height = 800, 700
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 130, 18), "SHOP", fill=BRAND_COLORS["gold"], font=get_font(22, bold=True))
    draw.text((width - 120, 45), f"{coins} coins", fill=BRAND_COLORS["gold"], font=get_font(14, bold=True))
    
    y = 90
    category_names = {"skins": "SKINS", "decor": "DECOR", "goods": "GOODS"}
    draw.text((width // 2 - 50, y), category_names.get(category, "ITEMS"), fill=BRAND_COLORS["accent"], font=get_font(28, bold=True))
    
    y += 60
    
    for i, item in enumerate(items[:8]):
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 55], 10, color)
        
        draw.text((50, y + 15), item.get("icon", "⭐"), fill=BRAND_COLORS["gold"], font=get_font(24))
        draw.text((100, y + 15), item["name"][:28], fill=BRAND_COLORS["light"], font=get_font(18))
        draw.text((width - 120, y + 15), f"{item['price']} coins", fill=BRAND_COLORS["gold"], font=get_font(16, bold=True))
        
        if item.get("days"):
            draw.text((width - 200, y + 15), f"{item['days']}d", fill=BRAND_COLORS["info"], font=get_font(14))
        
        y += 65
    
    # Нижняя полоса
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    return _to_bytes(img)

def create_inventory_card(player, inventory):
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 150, 18), "INVENTORY", fill=BRAND_COLORS["gold"], font=get_font(20, bold=True))
    
    draw.text((40, 85), f"{player[1]}", fill=BRAND_COLORS["gold"], font=get_font(24, bold=True))
    draw.text((40, 120), "Your items:", fill=BRAND_COLORS["light"], font=get_font(16))
    
    y = 160
    
    if not inventory:
        draw.text((width // 2 - 80, height // 2), "No items", fill=BRAND_COLORS["light"], font=get_font(20))
    else:
        for i, (inv_id, item_name, item_type, item_id, activated, expires) in enumerate(inventory[:8]):
            color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
            draw_rounded_rectangle(draw, [30, y, width - 30, y + 50], 10, color)
            
            status_icon = "✅" if activated else "⚡"
            status_color = BRAND_COLORS["primary"] if activated else BRAND_COLORS["warning"]
            draw.text((50, y + 12), status_icon, fill=status_color, font=get_font(24))
            
            draw.text((100, y + 12), item_name[:30], fill=BRAND_COLORS["light"], font=get_font(16))
            
            if expires:
                try:
                    exp_date = datetime.fromisoformat(expires)
                    days_left = (exp_date - datetime.now()).days
                    if days_left > 0 and activated:
                        draw.text((width - 100, y + 12), f"{days_left}d", fill=BRAND_COLORS["gold"], font=get_font(16))
                except:
                    pass
            
            y += 55
    
    # Нижняя полоса
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    return _to_bytes(img)

def create_lobby_card(league, lobbies):
    width, height = 800, 500
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 120, 18), "LOBBIES", fill=BRAND_COLORS["gold"], font=get_font(22, bold=True))
    
    y = 90
    league_name = "QUALS" if league == "quals" else "DEFAULT"
    draw.text((width // 2 - 60, y), f"{league_name} LEAGUE", fill=BRAND_COLORS["accent"], font=get_font(24, bold=True))
    
    y += 60
    
    # MOBILE
    draw.text((50, y), "MOBILE", fill=BRAND_COLORS["info"], font=get_font(20, bold=True))
    for slot in range(1, 6):
        lob = next((l for l in lobbies if l["slot"] == slot and l["device"] == "MOBILE"), None)
        count = lob["count"] if lob else 0
        emoji = "🟢" if count > 0 else "⚪"
        draw.text((50 + (slot - 1) * 100, y + 35), f"{emoji} {slot}({count})", fill=BRAND_COLORS["light"], font=get_font(16))
    
    y += 80
    
    # PC
    draw.text((50, y), "PC", fill=BRAND_COLORS["info"], font=get_font(20, bold=True))
    for slot in range(1, 6):
        lob = next((l for l in lobbies if l["slot"] == slot and l["device"] == "PC"), None)
        count = lob["count"] if lob else 0
        emoji = "🟢" if count > 0 else "⚪"
        draw.text((50 + (slot - 1) * 100, y + 35), f"{emoji} {slot}({count})", fill=BRAND_COLORS["light"], font=get_font(16))
    
    # Нижняя полоса
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    return _to_bytes(img)

def create_map_card(lobby, map_stats):
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 100, 18), "VETO", fill=BRAND_COLORS["gold"], font=get_font(22, bold=True))
    
    y = 90
    draw.text((30, y), f"Ban {lobby['ban_count']}/4", fill=BRAND_COLORS["accent"], font=get_font(24, bold=True))
    
    turn = "CT" if lobby["veto_turn"] == "ct" else "T"
    draw.text((width - 150, y), f"Turn: {turn}", fill=BRAND_COLORS["gold"], font=get_font(20, bold=True))
    
    y += 60
    draw.text((30, y), "Available maps:", fill=BRAND_COLORS["light"], font=get_font(18))
    y += 40
    
    for i, map_name in enumerate(lobby["map_pool"][:5]):
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 45], 10, color)
        draw.text((50, y + 10), f"{map_name}", fill=BRAND_COLORS["light"], font=get_font(18))
        y += 50
    
    # Нижняя полоса
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    return _to_bytes(img)

def create_match_start_card(match_id, map_name, league, team_ct, team_t, ct_players, t_players):
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 100, 18), f"MATCH #{match_id}", fill=BRAND_COLORS["gold"], font=get_font(18, bold=True))
    
    y = 90
    draw.text((30, y), f"Map: {map_name}", fill=BRAND_COLORS["accent"], font=get_font(24, bold=True))
    draw.text((width - 150, y), league.upper(), fill=BRAND_COLORS["gold"], font=get_font(18, bold=True))
    
    y += 70
    
    # CT team
    draw_rounded_rectangle(draw, [30, y, width // 2 - 20, y + 260], 15, (30, 50, 70))
    draw.text((width // 4 - 40, y + 15), "TEAM CT", fill=BRAND_COLORS["info"], font=get_font(20, bold=True))
    
    ct_y = y + 60
    for i, (uid, p) in enumerate(zip(team_ct[:5], ct_players[:5])):
        if p:
            draw.text((50, ct_y), f"{i+1}. {p[1]}", fill=BRAND_COLORS["light"], font=get_font(16))
            draw.text((width // 2 - 140, ct_y), f"LVL {p[4]}", fill=BRAND_COLORS["gold"], font=get_font(12))
        ct_y += 35
    
    # T team
    tx = width // 2 + 20
    draw_rounded_rectangle(draw, [tx, y, width - 30, y + 260], 15, (70, 50, 30))
    draw.text((tx + width // 4 - 40, y + 15), "TEAM T", fill=BRAND_COLORS["warning"], font=get_font(20, bold=True))
    
    t_y = y + 60
    for i, (uid, p) in enumerate(zip(team_t[:5], t_players[:5])):
        if p:
            draw.text((tx + 20, t_y), f"{i+1}. {p[1]}", fill=BRAND_COLORS["light"], font=get_font(16))
            draw.text((tx + 200, t_y), f"LVL {p[4]}", fill=BRAND_COLORS["gold"], font=get_font(12))
        t_y += 35
    
    # Нижняя полоса
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    return _to_bytes(img)

def create_match_result_card(match_id, map_name, league, score_ct, score_t, winner, ct_players, t_players):
    width, height = 800, 700
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка (цвет победителя)
    winner_color = BRAND_COLORS["primary"] if winner == "ct" else BRAND_COLORS["warning"]
    draw.rectangle([0, 0, width, 60], fill=winner_color)
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 100, 18), f"#{match_id}", fill=BRAND_COLORS["gold"], font=get_font(18, bold=True))
    
    y = 90
    draw.text((width // 2 - 60, y), f"{score_ct} : {score_t}", fill=winner_color, font=get_font(48, bold=True))
    y += 60
    winner_text = "CT WON" if winner == "ct" else "T WON"
    draw.text((width // 2 - 70, y), winner_text, fill=BRAND_COLORS["gold"], font=get_font(24, bold=True))
    
    y += 50
    draw.text((30, y), f"Map: {map_name}", fill=BRAND_COLORS["accent"], font=get_font(18))
    
    y += 40
    draw.text((30, y), "PLAYER STATS:", fill=BRAND_COLORS["light"], font=get_font(18, bold=True))
    y += 35
    
    # Заголовки таблицы
    headers = ["PLAYER", "K", "D", "A", "K/D"]
    x_pos = [50, 350, 430, 510, 590]
    for i, h in enumerate(headers):
        draw.text((x_pos[i], y), h, fill=BRAND_COLORS["accent"], font=get_font(14, bold=True))
    y += 25
    
    all_players = []
    for p, k, d, a in ct_players + t_players:
        if p:
            kd = round(k / d, 2) if d > 0 else k
            all_players.append((p, k, d, a, kd))
    
    for i, (p, k, d, a, kd) in enumerate(all_players[:10]):
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 32], 8, color)
        draw.text((50, y + 6), p[1][:18], fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((360, y + 6), str(k), fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((440, y + 6), str(d), fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((520, y + 6), str(a), fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((600, y + 6), str(kd), fill=BRAND_COLORS["gold"], font=get_font(14))
        y += 36
    
    # Нижняя полоса
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    return _to_bytes(img)

def _to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf