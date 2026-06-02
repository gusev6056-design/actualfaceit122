# Токен бота (замени на свой)
TOKEN = "8914521673:AAHaGCPmSq5PF6nu9xlEWm2DQe_-qPXx5QI"

# ID администратора (создателя бота)
ADMIN_ID = 8521250777

# Настройки логов (опционально)
LOG_CHANNEL_ID = None
LOG_THREAD_ID = None

# Список карт
MAPS = ["Breeze", "Rust", "Province", "Sakura", "Sandstone"]

# Время на принятие матча (секунд)
ACCEPT_TIMEOUT = 60

# Порог калибровки (матчей)
CALIB_THRESHOLD = 10

# Настройки ELO
ELO_WIN = 17
ELO_LOSS_HIGH = 15      # при ≥11 киллов
ELO_LOSS_LOW = 25       # при ≤10 киллов
KILLS_THRESHOLD = 11    # порог для хайтаб/лоутаб

# Настройки монет
COINS_WIN_MIN = 10
COINS_WIN_MAX = 20
COINS_LOSS_MIN = 5
COINS_LOSS_MAX = 6

# Настройки калибровки
CALIB_WIN_BONUS = 7     # скрытый бонус за победу в калибровке

# Бейджи
BADGES = {
    "admin": ("⚙️ Администратор", (100, 50, 180)),
    "lowtab": ("📉 Лоутаб", (45, 200, 95)),
    "hightab": ("📈 Хайтаб", (255, 100, 50)),
    "premium": ("⭐ PREMIUM", (180, 130, 0)),
    "veteran": ("🎖 Ветеран", (100, 100, 200)),
}

# Типы предметов в магазине
ITEM_TYPES = {
    "premium": "premium",
    "fpl_quals": "qual",
    "x2_coins": "x2coins",
    "unwarn": "unwarn",
    "nick_change": "nick_change",
    "reset_stats": "reset",
    "ak47": "skin",
    "m4a4": "skin",
    "awp": "skin",
    "knife": "skin",
}

# Магазин
SHOP_ITEMS = {
    "skins": [
        {"id": "ak47", "name": "AK-47 | Vulcan", "price": 500, "item_type": "skin"},
        {"id": "m4a4", "name": "M4A4 | Howl", "price": 800, "item_type": "skin"},
        {"id": "awp", "name": "AWP | Dragon Lore", "price": 1200, "item_type": "skin"},
        {"id": "knife", "name": "Нож | Fade", "price": 1500, "item_type": "skin"},
    ],
    "decor": [
        {"id": "frame_gold", "name": "Рамка Золото", "price": 350, "item_type": "decor"},
        {"id": "sticker_flite", "name": "Стикер Flite", "price": 50, "item_type": "decor"},
    ],
    "goods": [
        {"id": "premium", "name": "⭐ PREMIUM статус", "price": 600, "item_type": "premium"},
        {"id": "fpl_quals", "name": "FPL Quals (30д)", "price": 1000, "item_type": "qual", "days": 30},
        {"id": "x2_coins", "name": "x2 Монеты (7д)", "price": 300, "item_type": "x2coins", "days": 7},
        {"id": "unwarn", "name": "Снять Warn", "price": 500, "item_type": "unwarn"},
        {"id": "nick_change", "name": "Смена ника", "price": 300, "item_type": "nick_change"},
    ],
}

# Типы магазина
ONE_TIME_TYPES = {"unwarn", "nick_change"}
ACTIVATABLE_TYPES = {"premium", "qual", "x2coins", "skin", "decor", "unwarn", "nick_change"}

# Лиги
LEAGUES = ["Default", "Quals", "FPL"]