from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import random

# Цвета бренда Actual Faceit
BRAND_COLORS = {
    "primary": (45, 200, 95),      # Зеленый
    "secondary": (30, 150, 70),    # Темно-зеленый
    "accent": (255, 100, 50),      # Оранжевый
    "dark": (20, 25, 35),          # Темный фон
    "light": (240, 245, 250),      # Светлый текст
    "gold": (255, 215, 0),         # Золотой
    "danger": (255, 50, 50),       # Красный
    "warning": (255, 150, 50),     # Оранжевый
    "info": (50, 150, 255),        # Синий
}

def get_font(size, bold=False):
    """Получить шрифт (попытка загрузить разные варианты)"""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\Arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica-Bold.ttc",
        "C:\\Windows\\Fonts\\Arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
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

def draw_rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    """Нарисовать скругленный прямоугольник"""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=fill)
    draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=fill)

def create_profile_card(player, stats, badges, league_name):
    """Создать карточку профиля"""
    width, height = 800, 500
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Верхняя полоса с брендом
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    title_font = get_font(28, bold=True)
    draw.text((30, 15), "🔥 ACTUAL FACEIT", fill=BRAND_COLORS["light"], font=title_font)
    draw.text((width - 200, 20), f"LVL {stats['level']}", fill=BRAND_COLORS["gold"], font=get_font(24, bold=True))
    
    # Аватар (круг)
    avatar_size = 120
    avatar_x, avatar_y = 50, 100
    draw.ellipse([avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size], 
                 fill=BRAND_COLORS["secondary"])
    draw.text((avatar_x + 40, avatar_y + 40), "👤", fill=BRAND_COLORS["light"], font=get_font(50))
    
    # Информация об игроке
    name = player[1][:20]
    draw.text((200, 110), name, fill=BRAND_COLORS["light"], font=get_font(32, bold=True))
    
    # ELO и монеты
    draw.text((200, 160), f"🏆 ELO: {stats['elo']}", fill=BRAND_COLORS["accent"], font=get_font(20))
    draw.text((200, 195), f"💰 Монеты: {stats['coins']}", fill=BRAND_COLORS["gold"], font=get_font(20))
    
    # Бейджи
    badge_y = 240
    badge_x = 200
    for i, badge in enumerate(badges[:4]):
        badge_colors = {
            "admin": BRAND_COLORS["danger"],
            "premium": BRAND_COLORS["gold"],
            "lowtab": BRAND_COLORS["info"],
            "wheelchair": (120, 120, 120)
        }
        color = badge_colors.get(badge, BRAND_COLORS["accent"])
        draw_rounded_rectangle(draw, [badge_x + i * 90, badge_y, badge_x + i * 90 + 80, badge_y + 30], 15, color)
        draw.text((badge_x + i * 90 + 15, badge_y + 5), badge[:8], fill=BRAND_COLORS["light"], font=get_font(14))
    
    # Статистика
    stats_y = 300
    stat_box_height = 160
    draw_rounded_rectangle(draw, [30, stats_y, width - 30, stats_y + stat_box_height], 15, (30, 35, 45))
    
    # Разделители
    draw.line([width//3 + 20, stats_y + 20, width//3 + 20, stats_y + stat_box_height - 20], 
              fill=(50, 55, 65), width=2)
    draw.line([width*2//3 + 10, stats_y + 20, width*2//3 + 10, stats_y + stat_box_height - 20], 
              fill=(50, 55, 65), width=2)
    
    # Левая колонка
    draw.text((60, stats_y + 30), f"🎯 K/D: {stats['kd']}", fill=BRAND_COLORS["light"], font=get_font(18))
    draw.text((60, stats_y + 65), f"💀 Убийства: {stats['kills']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((60, stats_y + 100), f"⚰️ Смерти: {stats['deaths']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((60, stats_y + 135), f"🤝 Ассисты: {stats['assists']}", fill=BRAND_COLORS["light"], font=get_font(16))
    
    # Центральная колонка
    cx = width//3 + 40
    draw.text((cx, stats_y + 30), f"🏆 Винрейт: {stats['winrate']}%", fill=BRAND_COLORS["light"], font=get_font(18))
    draw.text((cx, stats_y + 65), f"✅ Побед: {stats['wins']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((cx, stats_y + 100), f"❌ Поражений: {stats['losses']}", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((cx, stats_y + 135), f"🎮 Игр: {stats['games']}", fill=BRAND_COLORS["light"], font=get_font(16))
    
    # Правая колонка
    rx = width*2//3 + 30
    draw.text((rx, stats_y + 30), f"⭐ MVP: {stats['mvp']}", fill=BRAND_COLORS["light"], font=get_font(18))
    draw.text((rx, stats_y + 65), f"🎯 ХС: {stats['headshots']}%", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((rx, stats_y + 100), f"📊 Лига: {league_name}", fill=BRAND_COLORS["accent"], font=get_font(16))
    draw.text((rx, stats_y + 135), f"🆔 ID: {player[0]}", fill=BRAND_COLORS["light"], font=get_font(12))
    
    # Нижняя полоса
    draw.rectangle([0, height - 30, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width//2 - 100, height - 25), "actualfaceit.com", fill=BRAND_COLORS["light"], font=get_font(14))
    
    return _to_bytes(img)

def create_map_card(lobby, map_stats):
    """Создать карточку вето карт"""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "🗺 ACTUAL FACEIT | ВЕТО КАРТ", fill=BRAND_COLORS["light"], font=get_font(26, bold=True))
    
    turn_emoji = "🟦" if lobby["veto_turn"] == "ct" else "🟧"
    turn_text = f"{turn_emoji} Ход: {'CT' if lobby['veto_turn'] == 'ct' else 'T'}"
    draw.text((width - 250, 20), turn_text, fill=BRAND_COLORS["gold"], font=get_font(20, bold=True))
    
    y = 80
    draw.text((30, y), f"🎮 Бан {lobby['ban_count']}/4", fill=BRAND_COLORS["accent"], font=get_font(24, bold=True))
    
    y += 50
    # Доступные карты
    draw.text((30, y), "📋 Доступные карты:", fill=BRAND_COLORS["light"], font=get_font(20))
    y += 35
    
    for i, map_name in enumerate(lobby["map_pool"]):
        stats = map_stats.get(map_name, {})
        pick_pct = stats.get("pick_pct", 0)
        ct_wr = stats.get("ct_wr", 50)
        t_wr = stats.get("t_wr", 50)
        
        color = BRAND_COLORS["secondary"] if i % 2 == 0 else (40, 45, 55)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 55], 10, color)
        
        draw.text((50, y + 15), f"❌ {map_name}", fill=BRAND_COLORS["light"], font=get_font(20))
        draw.text((250, y + 15), f"🎯 Выбор: {pick_pct}%", fill=BRAND_COLORS["info"], font=get_font(16))
        draw.text((450, y + 15), f"🟦 CT: {ct_wr}%", fill=BRAND_COLORS["info"], font=get_font(16))
        draw.text((580, y + 15), f"🟧 T: {t_wr}%", fill=BRAND_COLORS["info"], font=get_font(16))
        y += 65
    
    # Забаненные карты
    if lobby["bans"]:
        y += 10
        draw.text((30, y), "🚫 Забаненные карты:", fill=BRAND_COLORS["danger"], font=get_font(18))
        y += 30
        for ban in lobby["bans"][-4:]:
            ban_emoji = "🟦" if ban["by"] == "ct" else "🟧"
            draw.text((50, y), f"{ban_emoji} {ban['map']}", fill=(150, 150, 150), font=get_font(16))
            y += 25
    
    # Нижняя полоса
    draw.rectangle([0, height - 30, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width//2 - 100, height - 25), "actualfaceit.com", fill=BRAND_COLORS["light"], font=get_font(14))
    
    return _to_bytes(img)

def create_top_card(players):
    """Создать карточку топ игроков"""
    width, height = 800, 700
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 70], fill=BRAND_COLORS["primary"])
    draw.text((width//2 - 120, 20), "🏆 ACTUAL FACEIT | ТОП ИГРОКОВ", fill=BRAND_COLORS["light"], font=get_font(28, bold=True))
    
    y = 90
    # Заголовки таблицы
    draw_rounded_rectangle(draw, [30, y, width - 30, y + 40], 10, BRAND_COLORS["secondary"])
    draw.text((50, y + 10), "#", fill=BRAND_COLORS["light"], font=get_font(18, bold=True))
    draw.text((100, y + 10), "ИГРОК", fill=BRAND_COLORS["light"], font=get_font(18, bold=True))
    draw.text((400, y + 10), "ELO", fill=BRAND_COLORS["light"], font=get_font(18, bold=True))
    draw.text((500, y + 10), "W/L", fill=BRAND_COLORS["light"], font=get_font(18, bold=True))
    draw.text((620, y + 10), "K/D", fill=BRAND_COLORS["light"], font=get_font(18, bold=True))
    
    y += 55
    
    for i, (name, gid, elo, wins, losses, kills, deaths) in enumerate(players[:10], 1):
        color = (40, 45, 55) if i % 2 == 0 else (50, 55, 65)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 45], 8, color)
        
        # Медаль для топ-3
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = str(i)
        
        draw.text((50, y + 10), medal, fill=BRAND_COLORS["gold"], font=get_font(18, bold=True))
        draw.text((100, y + 10), name[:18], fill=BRAND_COLORS["light"], font=get_font(18))
        draw.text((420, y + 10), str(elo), fill=BRAND_COLORS["accent"], font=get_font(18, bold=True))
        
        games = wins + losses
        wr = round(wins/games*100, 1) if games > 0 else 0
        draw.text((500, y + 10), f"{wins}/{losses} ({wr}%)", fill=BRAND_COLORS["light"], font=get_font(16))
        
        kd = round(kills/deaths, 2) if deaths > 0 else kills
        draw.text((630, y + 10), str(kd), fill=BRAND_COLORS["info"], font=get_font(16))
        
        y += 55
        if y > height - 60:
            break
    
    # Нижняя полоса
    draw.rectangle([0, height - 30, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width//2 - 100, height - 25), "actualfaceit.com", fill=BRAND_COLORS["light"], font=get_font(14))
    
    return _to_bytes(img)

def create_shop_card(category, items, coins):
    """Создать карточку магазина"""
    width, height = 800, 700
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "🛒 ACTUAL FACEIT | МАГАЗИН", fill=BRAND_COLORS["light"], font=get_font(26, bold=True))
    draw.text((width - 200, 15), f"💰 {coins}", fill=BRAND_COLORS["gold"], font=get_font(24, bold=True))
    
    # Категория
    y = 80
    category_names = {"skins": "🎨 СКИНЫ", "decor": "🎭 ДЕКОР", "goods": "🛍 ТОВАРЫ"}
    draw.text((width//2 - 100, y), category_names.get(category, "ТОВАРЫ"), fill=BRAND_COLORS["accent"], font=get_font(28, bold=True))
    
    y += 60
    for i, item in enumerate(items):
        color = (40, 45, 55) if i % 2 == 0 else (50, 55, 65)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 65], 10, color)
        
        # Иконка
        glow = "✨" if item.get("glow") else "  "
        draw.text((50, y + 15), f"{glow} {item['icon']}", fill=BRAND_COLORS["gold"] if item.get("glow") else BRAND_COLORS["light"], font=get_font(28))
        
        # Название
        draw.text((100, y + 15), item['name'][:30], fill=BRAND_COLORS["light"], font=get_font(18))
        
        # Цена
        price_color = BRAND_COLORS["gold"] if item['price'] <= 500 else BRAND_COLORS["warning"]
        draw.text((width - 120, y + 20), f"{item['price']} 💰", fill=price_color, font=get_font(20, bold=True))
        
        y += 75
        if y > height - 80:
            break
    
    # Нижняя полоса
    draw.rectangle([0, height - 30, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width//2 - 100, height - 25), "actualfaceit.com", fill=BRAND_COLORS["light"], font=get_font(14))
    
    return _to_bytes(img)

def create_inventory_card(player, inventory):
    """Создать карточку инвентаря"""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "🎒 ACTUAL FACEIT | ИНВЕНТАРЬ", fill=BRAND_COLORS["light"], font=get_font(26, bold=True))
    draw.text((width - 200, 15), player[1][:15], fill=BRAND_COLORS["gold"], font=get_font(20))
    
    y = 90
    if not inventory:
        draw.text((width//2 - 150, height//2), "📦 Инвентарь пуст", fill=BRAND_COLORS["light"], font=get_font(24))
    else:
        for i, (inv_id, item_name, item_type, item_id, activated, expires) in enumerate(inventory):
            color = (40, 45, 55) if i % 2 == 0 else (50, 55, 65)
            draw_rounded_rectangle(draw, [30, y, width - 30, y + 55], 10, color)
            
            status_emoji = "✅" if activated else "⚡"
            status_color = BRAND_COLORS["primary"] if activated else BRAND_COLORS["warning"]
            draw.text((50, y + 12), status_emoji, fill=status_color, font=get_font(28))
            
            draw.text((100, y + 15), item_name[:30], fill=BRAND_COLORS["light"], font=get_font(18))
            
            if expires:
                try:
                    exp_date = datetime.fromisoformat(expires)
                    days_left = (exp_date - datetime.now()).days
                    if days_left > 0:
                        draw.text((width - 120, y + 15), f"{days_left}д", fill=BRAND_COLORS["warning"], font=get_font(16))
                    else:
                        draw.text((width - 120, y + 15), "Истек", fill=BRAND_COLORS["danger"], font=get_font(16))
                except:
                    pass
            
            y += 65
            if y > height - 80:
                break
    
    # Нижняя полоса
    draw.rectangle([0, height - 30, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width//2 - 100, height - 25), "actualfaceit.com", fill=BRAND_COLORS["light"], font=get_font(14))
    
    return _to_bytes(img)

def create_lobby_card(league, lobbies):
    """Создать карточку лобби"""
    width, height = 800, 500
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    league_name = "⭐ QUALS" if league == "quals" else "🎮 DEFAULT"
    draw.text((30, 15), f"🎮 ACTUAL FACEIT | {league_name}", fill=BRAND_COLORS["light"], font=get_font(26, bold=True))
    
    y = 90
    draw.text((30, y), "🔍 Доступные лобби:", fill=BRAND_COLORS["accent"], font=get_font(24, bold=True))
    y += 50
    
    # Таблица лобби
    headers = ["DEVICE", "1", "2", "3", "4", "5"]
    col_widths = [100, 80, 80, 80, 80, 80]
    x = 50
    
    for i, header in enumerate(headers):
        draw.text((x + col_widths[i]//2 - 20, y), header, fill=BRAND_COLORS["light"], font=get_font(16, bold=True))
        x += col_widths[i]
    
    y += 35
    
    for dv in ("MOBILE", "PC"):
        x = 50
        draw.text((x + 30, y), dv, fill=BRAND_COLORS["accent"], font=get_font(18, bold=True))
        x += col_widths[0]
        
        for slot in range(1, 6):
            lob = next((l for l in lobbies if l["slot"] == slot and l["device"] == dv), None)
            if lob:
                count = lob["count"]
                status = lob["status"]
                if status == "waiting":
                    color = BRAND_COLORS["primary"] if count > 0 else (80, 80, 80)
                else:
                    color = BRAND_COLORS["danger"]
                emoji = "🟢" if count > 0 else "⚪"
                if status != "waiting":
                    emoji = "🔴"
                
                draw.text((x + 30, y), f"{emoji} {count}/10", fill=color, font=get_font(16))
            else:
                draw.text((x + 30, y), "⚪ 0/10", fill=(80, 80, 80), font=get_font(16))
            x += col_widths[1]
        y += 50
    
    # Легенда
    y += 30
    draw.text((30, y), "📖 Легенда:", fill=BRAND_COLORS["light"], font=get_font(16))
    draw.text((150, y), "🟢 - есть игроки", fill=BRAND_COLORS["primary"], font=get_font(14))
    draw.text((320, y), "⚪ - пусто", fill=(150, 150, 150), font=get_font(14))
    draw.text((480, y), "🔴 - в игре", fill=BRAND_COLORS["danger"], font=get_font(14))
    
    # Нижняя полоса
    draw.rectangle([0, height - 30, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width//2 - 100, height - 25), "actualfaceit.com", fill=BRAND_COLORS["light"], font=get_font(14))
    
    return _to_bytes(img)

def create_match_start_card(match_id, map_name, league, team_ct, team_t, ct_players, t_players):
    """Создать карточку начала матча"""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    draw.rectangle([0, 0, width, 60], fill=BRAND_COLORS["primary"])
    draw.text((30, 15), "⚔️ ACTUAL FACEIT | МАТЧ", fill=BRAND_COLORS["light"], font=get_font(26, bold=True))
    draw.text((width - 150, 20), f"#{match_id}", fill=BRAND_COLORS["gold"], font=get_font(24, bold=True))
    
    # Информация о матче
    y = 90
    draw.text((30, y), f"🗺 Карта: {map_name}", fill=BRAND_COLORS["accent"], font=get_font(24, bold=True))
    draw.text((width - 200, y), f"🏆 {league.upper()}", fill=BRAND_COLORS["gold"], font=get_font(20, bold=True))
    
    y += 60
    # Команды
    # CT
    draw_rounded_rectangle(draw, [30, y, width//2 - 20, y + 250], 15, (30, 50, 70))
    draw.text((width//4 - 40, y + 10), "🟦 КОМАНДА CT", fill=BRAND_COLORS["info"], font=get_font(20, bold=True))
    
    ct_y = y + 60
    for i, (uid, p) in enumerate(zip(team_ct, ct_players)):
        if p:
            draw.text((50, ct_y), f"{i+1}. {p[1]}", fill=BRAND_COLORS["light"], font=get_font(16))
            draw.text((width//2 - 120, ct_y), f"LVL {p[4]} | {p[5]} ELO", fill=BRAND_COLORS["gold"], font=get_font(12))
        ct_y += 35
    
    # T
    tx = width//2 + 20
    draw_rounded_rectangle(draw, [tx, y, width - 30, y + 250], 15, (70, 50, 30))
    draw.text((tx + width//4 - 40, y + 10), "🟧 КОМАНДА T", fill=BRAND_COLORS["warning"], font=get_font(20, bold=True))
    
    t_y = y + 60
    for i, (uid, p) in enumerate(zip(team_t, t_players)):
        if p:
            draw.text((tx + 20, t_y), f"{i+1}. {p[1]}", fill=BRAND_COLORS["light"], font=get_font(16))
            draw.text((tx + 250, t_y), f"LVL {p[4]} | {p[5]} ELO", fill=BRAND_COLORS["gold"], font=get_font(12))
        t_y += 35
    
    y += 280
    draw.text((width//2 - 150, y), "⏳ После матча нажмите «Отправить результат»", fill=BRAND_COLORS["light"], font=get_font(16))
    
    # Нижняя полоса
    draw.rectangle([0, height - 30, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width//2 - 100, height - 25), "actualfaceit.com", fill=BRAND_COLORS["light"], font=get_font(14))
    
    return _to_bytes(img)

def create_match_result_card(match_id, map_name, league, score_ct, score_t, winner, ct_players, t_players):
    """Создать карточку результата матча"""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), BRAND_COLORS["dark"])
    draw = ImageDraw.Draw(img)
    
    # Шапка
    winner_color = BRAND_COLORS["primary"] if winner == "ct" else BRAND_COLORS["warning"]
    draw.rectangle([0, 0, width, 60], fill=winner_color)
    draw.text((30, 15), "🏆 ACTUAL FACEIT | РЕЗУЛЬТАТ", fill=BRAND_COLORS["light"], font=get_font(26, bold=True))
    draw.text((width - 150, 20), f"#{match_id}", fill=BRAND_COLORS["gold"], font=get_font(24, bold=True))
    
    # Счёт
    y = 90
    score_text = f"{score_ct} : {score_t}"
    winner_text = "🏆 ПОБЕДИЛА CT" if winner == "ct" else "🏆 ПОБЕДИЛА T"
    draw.text((width//2 - 60, y), score_text, fill=winner_color, font=get_font(48, bold=True))
    draw.text((width//2 - 100, y + 60), winner_text, fill=BRAND_COLORS["gold"], font=get_font(20, bold=True))
    
    y += 120
    draw.text((30, y), f"🗺 {map_name}", fill=BRAND_COLORS["accent"], font=get_font(20))
    
    y += 40
    # Статистика игроков
    draw.text((30, y), "📊 СТАТИСТИКА ИГРОКОВ:", fill=BRAND_COLORS["light"], font=get_font(18, bold=True))
    y += 35
    
    # Заголовки
    draw.text((50, y), "ИГРОК", fill=BRAND_COLORS["accent"], font=get_font(14, bold=True))
    draw.text((400, y), "K/D/A", fill=BRAND_COLORS["accent"], font=get_font(14, bold=True))
    draw.text((550, y), "Рейтинг", fill=BRAND_COLORS["accent"], font=get_font(14, bold=True))
    y += 25
    
    all_players = []
    for p, k, d, a in ct_players + t_players:
        if p:
            kd = round(k/d, 2) if d > 0 else k
            rating = round(kd * 0.85 + a * 0.02, 2)
            all_players.append((p, k, d, a, kd, rating))
    
    all_players.sort(key=lambda x: x[5], reverse=True)
    
    for i, (p, k, d, a, kd, rating) in enumerate(all_players[:10]):
        color = (40, 45, 55) if i % 2 == 0 else (50, 55, 65)
        draw_rounded_rectangle(draw, [30, y, width - 30, y + 30], 8, color)
        
        draw.text((50, y + 5), p[1][:18], fill=BRAND_COLORS["light"], font=get_font(14))
        draw.text((400, y + 5), f"{k}/{d}/{a}", fill=BRAND_COLORS["info"], font=get_font(14))
        draw.text((550, y + 5), str(rating), fill=BRAND_COLORS["gold"], font=get_font(14))
        y += 35
    
    # Нижняя полоса
    draw.rectangle([0, height - 30, width, height], fill=BRAND_COLORS["primary"])
    draw.text((width//2 - 100, height - 25), "actualfaceit.com", fill=BRAND_COLORS["light"], font=get_font(14))
    
    return _to_bytes(img)

def _to_bytes(img):
    """Конвертировать PIL Image в bytes для отправки в Telegram"""
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf