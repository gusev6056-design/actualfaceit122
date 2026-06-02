from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime

BRAND_COLORS = {
    "primary": (0, 200, 100),
    "dark": (15, 20, 28),
    "card": (25, 30, 40),
    "light": (240, 245, 250),
    "gold": (255, 200, 0),
    "accent": (255, 100, 50),
    "danger": (255, 60, 60),
    "info": (50, 150, 255),
    "warning": (255, 150, 50),
}

def get_font(size, bold=False):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\Arial.ttf",
    ]
    try:
        return ImageFont.truetype(font_paths[0], size)
    except:
        try:
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
    width, height = 800, 450
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    
    draw.text((40, 90), player[1], fill=BRAND_COLORS["gold"], font=get_font(32, bold=True))
    draw.text((40, 140), f"LVL {stats['level']} | ELO: {stats['elo']}", fill=BRAND_COLORS["light"], font=get_font(20))
    draw.text((40, 180), f"💰 Монеты: {stats['coins']}", fill=BRAND_COLORS["gold"], font=get_font(18))
    
    draw_rounded_rectangle(draw, [30, 230, width - 30, 370], 15, BRAND_COLORS["card"])
    draw.text((50, 250), f"Убийства: {stats['kills']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((50, 280), f"Смерти: {stats['deaths']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((50, 310), f"Ассисты: {stats['assists']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((50, 340), f"K/D: {stats['kd']}", fill=BRAND_COLORS["light"], font=get_font(16))
    
    draw.text((300, 250), f"Победы: {stats['wins']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((300, 280), f"Поражения: {stats['losses']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((300, 310), f"Винрейт: {stats['winrate']}%", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((300, 340), f"MVP: {stats['mvp']}", fill=BRAND_COLORS["light"], font=get_font(16))
    
    draw.text((550, 250), f"ХС: {stats['headshots']}%", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((550, 280), f"Лига: {league_name}", fill=BRAND_COLORS["accent"], font=get_font(16))
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_top_card(players):
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    
    y = 100
    for i, (name, gid, elo, wins, losses, kills, deaths) in enumerate(players[:10], 1):
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 45], 10, color)
        
        if i == 1:
            draw.text((55, y + 12), "1", fill=BRAND_COLORS["gold"], font=get_font(18, bold=True))
        else:
            draw.text((58, y + 12), str(i), fill=BRAND_COLORS["light"], font=get_font(16))
        
        draw.text((100, y + 12), name[:18], fill=BRAND_COLORS["light"], font=get_font(16))
        draw.text((400, y + 12), str(elo), fill=BRAND_COLORS["accent"], font=get_font(16, bold=True))
        
        games = wins + losses
        winrate = round(wins / games * 100, 1) if games > 0 else 0
        draw.text((520, y + 12), f"{wins}/{losses} ({winrate}%)", fill=BRAND_COLORS["light"], font=get_font(14))
        
        kd = round(kills / deaths, 2) if deaths > 0 else kills
        draw.text((670, y + 12), str(kd), fill=BRAND_COLORS["gold"], font=get_font(16))
        
        y += 55
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 120, height - 20), "ACTUAL FACEIT · BEST PLAYERS", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_shop_card(category, items, coins):
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    draw.text((width - 120, 45), f"{coins} coins", fill=BRAND_COLORS["gold"], font=get_font(16, bold=True))
    
    y = 90
    category_names = {"skins": "SKINS", "decor": "DECOR", "goods": "GOODS"}
    draw.text((width // 2 - 50, y), category_names.get(category, "ITEMS"), fill=BRAND_COLORS["accent"], font=get_font(28, bold=True))
    
    y += 60
    
    for i, item in enumerate(items[:8]):
        color = (35, 40, 50) if i % 2 == 0 else (30, 35, 45)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 55], 10, color)
        
        draw.text((100, y + 15), item["name"][:28], fill=BRAND_COLORS["light"], font=get_font(18))
        draw.text((width - 120, y + 15), f"{item['price']} coins", fill=BRAND_COLORS["gold"], font=get_font(16, bold=True))
        
        if item.get("days"):
            draw.text((width - 200, y + 15), f"{item['days']}d", fill=BRAND_COLORS["info"], font=get_font(14))
        
        y += 65
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_inventory_card(player, inventory):
    width, height = 800, 500
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    
    draw.text((40, 85), player[1], fill=BRAND_COLORS["gold"], font=get_font(24, bold=True))
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
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_lobby_card(league, lobbies):
    width, height = 800, 400
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    
    y = 90
    league_name = "QUALS" if league == "quals" else "DEFAULT"
    draw.text((width // 2 - 60, y), f"{league_name} LOBBIES", fill=BRAND_COLORS["accent"], font=get_font(24, bold=True))
    
    y += 60
    draw.text((50, y), "MOBILE", fill=BRAND_COLORS["info"], font=get_font(20, bold=True))
    for slot in range(1, 6):
        lob = next((l for l in lobbies if l["slot"] == slot and l["device"] == "MOBILE"), None)
        count = lob["count"] if lob else 0
        emoji = "🟢" if count > 0 else "⚪"
        draw.text((50 + (slot - 1) * 100, y + 35), f"{emoji} {slot}({count})", fill=BRAND_COLORS["light"], font=get_font(16))
    
    y += 80
    draw.text((50, y), "PC", fill=BRAND_COLORS["info"], font=get_font(20, bold=True))
    for slot in range(1, 6):
        lob = next((l for l in lobbies if l["slot"] == slot and l["device"] == "PC"), None)
        count = lob["count"] if lob else 0
        emoji = "🟢" if count > 0 else "⚪"
        draw.text((50 + (slot - 1) * 100, y + 35), f"{emoji} {slot}({count})", fill=BRAND_COLORS["light"], font=get_font(16))
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_map_card(lobby, map_stats):
    width, height = 800, 500
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    
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
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_match_start_card(match_id, map_name, league, team_ct, team_t, ct_players, t_players):
    width, height = 800, 500
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    
    y = 90
    draw.text((30, y), f"Map: {map_name}", fill=BRAND_COLORS["accent"], font=get_font(24, bold=True))
    draw.text((width - 150, y), f"Match #{match_id}", fill=BRAND_COLORS["gold"], font=get_font(18, bold=True))
    
    y += 70
    draw.text((width // 2 - 60, y), f"TEAM CT vs TEAM T", fill=BRAND_COLORS["light"], font=get_font(20, bold=True))
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def create_match_result_card(match_id, map_name, league, score_ct, score_t, winner, ct_players, t_players):
    width, height = 800, 500
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    winner_color = BRAND_COLORS["primary"] if winner == "ct" else BRAND_COLORS["warning"]
    draw.rectangle([0, 0, width, 60], fill=winner_color)
    draw.text((30, 15), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    
    y = 90
    draw.text((width // 2 - 50, y), f"{score_ct} : {score_t}", fill=winner_color, font=get_font(48, bold=True))
    y += 60
    winner_text = "CT WON" if winner == "ct" else "T WON"
    draw.text((width // 2 - 70, y), winner_text, fill=BRAND_COLORS["gold"], font=get_font(24, bold=True))
    
    draw.rectangle([0, height - 25, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width // 2 - 100, height - 20), "ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=get_font(14, bold=True))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf