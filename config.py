TOKEN = "8914521673:AAHaGCPmSq5PF6nu9xlEWm2DQe_-qPXx5QI"
BOT_TOKEN = TOKEN

ADMIN_ID = 8521250777

LOG_CHANNEL_ID = None
LOG_THREAD_ID = None

MAPS = ["Breeze", "Rust", "Province", "Sakura", "Sandstone"]

ACCEPT_TIMEOUT = 60

BADGES = {
    "admin": ("⚙️ Администратор", (100, 50, 180)),
    "lowtab": ("✓ Лоутаб", (45, 200, 95)),
    "wheelchair": ("♿ Инвалид", (120, 120, 120)),
    "premium": ("⭐ PREMIUM", (180, 130, 0)),
}

ITEM_TYPES = {
    "premium": "premium",
    "fpl_quals": "qual",
    "test_quals": "qual",
    "fpl_plus": "qual",
    "x2_coins": "x2coins",
    "unwarn": "unwarn",
    "nick_change": "nick_change",
    "reset_stats": "reset",
    "ak47": "skin",
    "m4a4": "skin",
    "awp": "skin",
    "knife": "skin",
    "glock": "skin",
    "deagle": "skin",
    "frame_fire": "decor",
    "frame_gold": "decor",
    "sticker_flite": "decor",
    "anim_win": "decor",
    "frame_prem": "decor",
    "sticker_gg": "decor",
}

ONE_TIME_TYPES = {"unwarn", "nick_change"}

ACTIVATABLE_TYPES = {"premium", "qual", "x2coins", "x2_coins", "skin", "decor", "unwarn", "nick_change"}

SHOP_ITEMS = {
    "skins": [
        {"id": "ak47", "name": "AK-47 | Vulcan", "price": 500, "item_type": "skin", "icon": "⭐", "glow": True},
        {"id": "m4a4", "name": "M4A4 | Howl", "price": 800, "item_type": "skin", "icon": "⭐", "glow": True},
        {"id": "awp", "name": "AWP | Dragon Lore", "price": 1200, "item_type": "skin", "icon": "⭐", "glow": True},
        {"id": "knife", "name": "Нож | Fade", "price": 1500, "item_type": "skin", "icon": "✦", "glow": True},
        {"id": "glock", "name": "Glock | Aqua Fade", "price": 300, "item_type": "skin", "icon": "✦", "glow": False},
        {"id": "deagle", "name": "Desert Eagle | Blaze", "price": 400, "item_type": "skin", "icon": "⭐", "glow": False},
    ],
    "decor": [
        {"id": "frame_fire", "name": "Рамка Огонь", "price": 200, "item_type": "decor", "icon": "F", "glow": True},
        {"id": "frame_gold", "name": "Рамка Золото", "price": 350, "item_type": "decor", "icon": "⭐", "glow": True},
        {"id": "sticker_flite", "name": "Стикер Flite", "price": 50, "item_type": "decor", "icon": "F", "glow": False},
        {"id": "anim_win", "name": "Анимация Победа", "price": 150, "item_type": "decor", "icon": "✦", "glow": False},
        {"id": "frame_prem", "name": "Рамка PREMIUM", "price": 500, "item_type": "decor", "icon": "⭐", "glow": True},
        {"id": "sticker_gg", "name": "Стикер GG", "price": 30, "item_type": "decor", "icon": "✦", "glow": False},
    ],
    "goods": [
        {"id": "premium", "name": "⭐ PREMIUM статус", "price": 600, "item_type": "premium", "icon": "⭐", "glow": True},
        {"id": "fpl_quals", "name": "FPL Quals (30д)", "price": 1000, "item_type": "qual", "icon": "✦", "glow": True, "days": 30},
        {"id": "x2_coins", "name": "x2 Монеты (7д)", "price": 300, "item_type": "x2coins", "icon": "F", "glow": True, "days": 7},
        {"id": "unwarn", "name": "Снять Warn (1 раз)", "price": 500, "item_type": "unwarn", "icon": "⊘", "glow": False},
        {"id": "nick_change", "name": "Смена ника (1 раз)", "price": 300, "item_type": "nick_change", "icon": "✏", "glow": False},
        {"id": "fpl_plus", "name": "FPL Quals+", "price": 1500, "item_type": "qual", "icon": "✦", "glow": True, "days": 60},
    ],
}