import sqlite3
from datetime import datetime, timedelta
from config import CALIB_THRESHOLD

DB = 'walker_faceit.db'

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Таблица игроков
    cur.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id              INTEGER PRIMARY KEY,
            username             TEXT,
            game_id              TEXT,
            device               TEXT DEFAULT 'MOBILE',
            level                INTEGER DEFAULT 1,
            elo                  INTEGER DEFAULT 1000,
            coins                INTEGER DEFAULT 0,
            wins                 INTEGER DEFAULT 0,
            losses               INTEGER DEFAULT 0,
            kills                INTEGER DEFAULT 0,
            deaths               INTEGER DEFAULT 0,
            assists              INTEGER DEFAULT 0,
            mvp                  INTEGER DEFAULT 0,
            headshots            INTEGER DEFAULT 0,
            is_admin             INTEGER DEFAULT 0,
            registered           INTEGER DEFAULT 0,
            is_bot               INTEGER DEFAULT 0,
            badges               TEXT    DEFAULT '',
            warns                INTEGER DEFAULT 0,
            muted_until          TEXT    DEFAULT NULL,
            banned               INTEGER DEFAULT 0,
            calibration_matches  INTEGER DEFAULT 0,
            total_calib_elo      INTEGER DEFAULT 1000,
            warn_reasons         TEXT    DEFAULT NULL,
            warn_by              TEXT    DEFAULT NULL,
            mute_reason          TEXT    DEFAULT NULL,
            mute_by              TEXT    DEFAULT NULL,
            ban_until            TEXT    DEFAULT NULL,
            ban_reason           TEXT    DEFAULT NULL,
            ban_by               TEXT    DEFAULT NULL,
            ban_type             TEXT    DEFAULT NULL,
            qual_league          TEXT    DEFAULT NULL,
            qual_expires         TEXT    DEFAULT NULL
        )
    ''')

    # Добавление недостающих колонок
    for col, dfn in [
        ("is_bot", "INTEGER DEFAULT 0"),
        ("badges", "TEXT DEFAULT ''"),
        ("warns", "INTEGER DEFAULT 0"),
        ("muted_until", "TEXT DEFAULT NULL"),
        ("banned", "INTEGER DEFAULT 0"),
        ("calibration_matches", "INTEGER DEFAULT 0"),
        ("total_calib_elo", "INTEGER DEFAULT 1000"),
        ("warn_reasons", "TEXT DEFAULT NULL"),
        ("warn_by", "TEXT DEFAULT NULL"),
        ("mute_reason", "TEXT DEFAULT NULL"),
        ("mute_by", "TEXT DEFAULT NULL"),
        ("ban_until", "TEXT DEFAULT NULL"),
        ("ban_reason", "TEXT DEFAULT NULL"),
        ("ban_by", "TEXT DEFAULT NULL"),
        ("ban_type", "TEXT DEFAULT NULL"),
        ("qual_league", "TEXT DEFAULT NULL"),
        ("qual_expires", "TEXT DEFAULT NULL"),
    ]:
        try:
            cur.execute(f"ALTER TABLE players ADD COLUMN {col} {dfn}")
        except:
            pass

    # Таблица матчей
    cur.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            match_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            lobby_id   INTEGER,
            map_name   TEXT,
            team_ct    TEXT,
            team_t     TEXT,
            league     TEXT,
            winner     TEXT    DEFAULT NULL,
            status     TEXT    DEFAULT 'pending',
            score_ct   INTEGER DEFAULT 0,
            score_t    INTEGER DEFAULT 0,
            created_at TEXT,
            registered_at TEXT DEFAULT NULL,
            chat_id    INTEGER DEFAULT NULL,
            message_id INTEGER DEFAULT NULL
        )
    ''')

    # Таблица статистики игроков в матчах
    cur.execute('''
        CREATE TABLE IF NOT EXISTS match_player_stats (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id  INTEGER,
            user_id   INTEGER,
            side      TEXT,
            kills     INTEGER DEFAULT 0,
            deaths    INTEGER DEFAULT 0,
            assists   INTEGER DEFAULT 0,
            rating    REAL    DEFAULT 0,
            kd        REAL    DEFAULT 0
        )
    ''')

    # Таблица статистики по картам
    cur.execute('''
        CREATE TABLE IF NOT EXISTS map_stats (
            user_id      INTEGER,
            map_name     TEXT,
            wins         INTEGER DEFAULT 0,
            losses       INTEGER DEFAULT 0,
            kills        INTEGER DEFAULT 0,
            deaths       INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, map_name)
        )
    ''')

    # Таблица инвентаря
    cur.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            item_name  TEXT,
            item_type  TEXT,
            item_id    TEXT,
            active     INTEGER DEFAULT 1,
            activated  INTEGER DEFAULT 0,
            expires_at TEXT
        )
    ''')
    for col, dfn in [("item_id", "TEXT DEFAULT NULL"), ("activated", "INTEGER DEFAULT 0")]:
        try:
            cur.execute(f"ALTER TABLE inventory ADD COLUMN {col} {dfn}")
        except:
            pass

    # Таблица жалоб
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER,
            match_id      INTEGER,
            reason        TEXT,
            status        TEXT DEFAULT 'open',
            created_at    TEXT,
            resolved_by   INTEGER DEFAULT NULL,
            resolved_at   TEXT DEFAULT NULL,
            admin_comment TEXT DEFAULT NULL
        )
    ''')

    # Таблица пати
    cur.execute('''
        CREATE TABLE IF NOT EXISTS parties (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            leader_id  INTEGER,
            code       TEXT UNIQUE,
            created_at TEXT,
            status     TEXT DEFAULT 'waiting'
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS party_members (
            party_id   INTEGER,
            user_id    INTEGER,
            joined_at  TEXT,
            PRIMARY KEY (party_id, user_id)
        )
    ''')

    # Добавляем карты в map_stats для существующих игроков (будет заполняться при первом матче)
    from config import MAPS
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════
# ОСНОВНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════

def get_player(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_player_by_username(username):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE username=? LIMIT 1", (username,))
    row = cur.fetchone()
    conn.close()
    return row
    
def register_player(user_id, username, game_id, device="MOBILE"):
    conn = sqlite3.connect(DB)
    conn.execute('''INSERT OR REPLACE INTO players
        (user_id, username, game_id, device, registered, coins, calibration_matches, total_calib_elo, elo, level)
        VALUES(?,?,?,?,1,0,0,1000,1000,1)''', (user_id, username, game_id, device))
    conn.commit()
    conn.close()

def register_bot(user_id, username, game_id, device="PC"):
    conn = sqlite3.connect(DB)
    conn.execute('''INSERT OR REPLACE INTO players
        (user_id, username, game_id, device, registered, is_bot, coins, calibration_matches, elo, level)
        VALUES(?,?,?,?,1,1,0,10,1000,1)''', (user_id, username, game_id, device))
    conn.commit()
    conn.close()

def set_username(user_id, username):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET username=? WHERE user_id=?", (username, user_id))
    conn.commit()
    conn.close()

def set_game_id(user_id, game_id):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET game_id=? WHERE user_id=?", (game_id, user_id))
    conn.commit()
    conn.close()

def is_calibrated(player):
    if not player:
        return False
    return player[26] >= CALIB_THRESHOLD if len(player) > 26 else False

def calib_count(player):
    if not player:
        return 0
    return player[26] if len(player) > 26 else 0

def add_coins(user_id, amount):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET coins=coins+? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def remove_coins(user_id, amount):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET coins=MAX(0,coins-?) WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def set_coins(user_id, amount):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET coins=? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def set_elo(user_id, elo, level=None):
    conn = sqlite3.connect(DB)
    if level is None:
        from config import elo_to_level
        level = elo_to_level(elo)
    conn.execute("UPDATE players SET elo=?, level=? WHERE user_id=?", (elo, level, user_id))
    conn.commit()
    conn.close()

def elo_to_level(elo):
    if elo < 200: return 1
    elif elo < 400: return 2
    elif elo < 600: return 3
    elif elo < 900: return 4
    elif elo < 1100: return 5
    elif elo < 1400: return 6
    elif elo < 1600: return 7
    elif elo < 1800: return 8
    elif elo < 2000: return 9
    else: return 10
    # ═══════════════════════════════════════════════════════════════════
# АДМИНСКИЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════

def set_admin(user_id, value=1):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET is_admin=? WHERE user_id=?", (value, user_id))
    conn.commit()
    conn.close()

def get_all_admins():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM players WHERE is_admin=1")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_admin_name(admin_id):
    if not admin_id:
        return "Система"
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT username FROM players WHERE user_id=?", (admin_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else str(admin_id)


# ═══════════════════════════════════════════════════════════════════
# БЕЙДЖИ
# ═══════════════════════════════════════════════════════════════════

def add_badge(user_id, badge):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT badges FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return
    badges = [b for b in (row[0] or '').split(',') if b]
    if badge not in badges:
        badges.append(badge)
    cur.execute("UPDATE players SET badges=? WHERE user_id=?", (','.join(badges), user_id))
    conn.commit()
    conn.close()

def remove_badge(user_id, badge):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT badges FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return
    badges = [b for b in (row[0] or '').split(',') if b and b != badge]
    cur.execute("UPDATE players SET badges=? WHERE user_id=?", (','.join(badges), user_id))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════
# СТАТИСТИКА
# ═══════════════════════════════════════════════════════════════════

def update_player_stats(user_id, kills, deaths, assists, headshots, win, map_name=None):
    """Обновляет общую статистику игрока и статистику по картам"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Общая статистика
    cur.execute('''UPDATE players SET
        kills=kills+?, deaths=deaths+?, assists=assists+?, headshots=headshots+?,
        wins=wins+?, losses=losses+?
        WHERE user_id=?''',
        (kills, deaths, assists, headshots, 1 if win else 0, 0 if win else 1, user_id))
    
    # Статистика по картам
    if map_name:
        cur.execute('''INSERT INTO map_stats (user_id, map_name, wins, losses, kills, deaths)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(user_id, map_name) DO UPDATE SET
            wins=wins+?, losses=losses+?, kills=kills+?, deaths=deaths+?''',
            (user_id, map_name, 1 if win else 0, 0 if win else 1, kills, deaths,
             1 if win else 0, 0 if win else 1, kills, deaths))
    
    conn.commit()
    conn.close()

def get_player_stats(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT kills, deaths, assists, wins, losses, elo, level, coins, headshots FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        kills, deaths, assists, wins, losses, elo, level, coins, headshots = row
        games = wins + losses
        kd = round(kills / deaths, 2) if deaths > 0 else kills
        winrate = round(wins / games * 100, 1) if games > 0 else 0
        hs_pct = round(headshots / kills * 100, 1) if kills > 0 else 0
        return {"kills": kills, "deaths": deaths, "assists": assists,
                "wins": wins, "losses": losses, "games": games,
                "kd": kd, "winrate": winrate, "elo": elo, "level": level,
                "coins": coins, "headshots": hs_pct}
    return None

def get_map_stats_for_player(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT map_name, wins, losses, kills, deaths FROM map_stats WHERE user_id=?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    result = {}
    for map_name, wins, losses, kills, deaths in rows:
        games = wins + losses
        winrate = round(wins / games * 100, 1) if games > 0 else 0
        kd = round(kills / deaths, 2) if deaths > 0 else kills
        result[map_name] = {"wins": wins, "losses": losses, "winrate": winrate, "kd": kd, "kills": kills, "deaths": deaths}
    return result

def get_top_players(limit=10):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('''SELECT username, elo, wins, losses, kills, deaths
        FROM players WHERE registered=1 AND is_bot=0
        ORDER BY elo DESC LIMIT ?''', (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# ═══════════════════════════════════════════════════════════════════
# МАТЧИ
# ═══════════════════════════════════════════════════════════════════

def save_match(lobby_id, map_name, team_ct, team_t, league, chat_id=None, message_id=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('''INSERT INTO matches(lobby_id, map_name, team_ct, team_t, league, status, created_at, chat_id, message_id)
        VALUES(?,?,?,?,?,?,?,?,?)''',
        (lobby_id, map_name, ','.join(map(str, team_ct)), ','.join(map(str, team_t)),
         league, 'pending', datetime.now().isoformat(), chat_id, message_id))
    mid = cur.lastrowid
    conn.commit()
    conn.close()
    return mid

def get_match(match_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM matches WHERE match_id=?", (match_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_match_registration(match_id, chat_id, message_id):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE matches SET chat_id=?, message_id=?, status='registration' WHERE match_id=?", (chat_id, message_id, match_id))
    conn.commit()
    conn.close()

def finalize_match(match_id, winner, score_ct, score_t):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE matches SET winner=?, status='completed', score_ct=?, score_t=?, registered_at=? WHERE match_id=?",
                 (winner, score_ct, score_t, datetime.now().isoformat(), match_id))
    conn.commit()
    conn.close()

def save_match_stats(match_id, user_id, side, kills, deaths, assists, kd, rating):
    conn = sqlite3.connect(DB)
    conn.execute('''INSERT INTO match_player_stats(match_id, user_id, side, kills, deaths, assists, rating, kd)
        VALUES(?,?,?,?,?,?,?,?)''', (match_id, user_id, side, kills, deaths, assists, rating, kd))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════
# СИСТЕМА НАКАЗАНИЙ
# ═══════════════════════════════════════════════════════════════════

def add_warn(user_id, reason=None, admin_id=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT warns, warn_reasons, warn_by FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    current_warns = row[0] if row else 0
    current_reasons = row[1] if row and row[1] else ""
    current_by = row[2] if row and row[2] else ""
    new_warns = current_warns + 1
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    admin_name = get_admin_name(admin_id) if admin_id else "Система"
    new_reason_entry = f"[{timestamp}] {reason if reason else 'Нарушение'}"
    new_by_entry = f"[{timestamp}] {admin_name}"
    updated_reasons = f"{current_reasons}\n{new_reason_entry}" if current_reasons else new_reason_entry
    updated_by = f"{current_by}\n{new_by_entry}" if current_by else new_by_entry
    cur.execute("UPDATE players SET warns=?, warn_reasons=?, warn_by=? WHERE user_id=?", (new_warns, updated_reasons, updated_by, user_id))
    conn.commit()
    conn.close()
    return new_warns

def remove_warn(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE players SET warns=MAX(0,warns-1) WHERE user_id=?", (user_id,))
    cur.execute("SELECT warns FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.commit()
    conn.close()
    return row[0] if row else 0

def clear_warns(user_id):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET warns=0, warn_reasons=NULL, warn_by=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_warns(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT warns, warn_reasons, warn_by FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"count": row[0] or 0, "reasons": row[1], "by": row[2]}
    return {"count": 0, "reasons": None, "by": None}

def mute_player(user_id, hours=2, reason=None, admin_id=None):
    conn = sqlite3.connect(DB)
    until = (datetime.now() + timedelta(hours=hours)).isoformat()
    admin_name = get_admin_name(admin_id) if admin_id else "Система"
    conn.execute("UPDATE players SET muted_until=?, mute_reason=?, mute_by=? WHERE user_id=?", (until, reason, admin_name, user_id))
    conn.commit()
    conn.close()
    return until

def unmute_player(user_id):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET muted_until=NULL, mute_reason=NULL, mute_by=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_muted(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT muted_until, mute_reason, mute_by FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row or not row[0]:
        return False, None
    try:
        until = datetime.fromisoformat(row[0])
        if datetime.now() >= until:
            unmute_player(user_id)
            return False, None
    except:
        pass
    return True, row[0]

def ban_player(user_id, days=None, reason=None, admin_id=None):
    conn = sqlite3.connect(DB)
    admin_name = get_admin_name(admin_id) if admin_id else "Система"
    if days and days > 0:
        until = (datetime.now() + timedelta(days=days)).isoformat()
        ban_type = "temporary"
    else:
        until = None
        ban_type = "permanent"
    conn.execute("UPDATE players SET banned=1, ban_until=?, ban_reason=?, ban_by=?, ban_type=? WHERE user_id=?", 
                 (until, f"{reason} (выдал: {admin_name})", admin_name, ban_type, user_id))
    conn.commit()
    conn.close()

def unban_player(user_id):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET banned=0, ban_until=NULL, ban_reason=NULL, ban_by=NULL, ban_type=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT banned, ban_until, ban_reason, ban_by, ban_type FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row or not row[0]:
        return False
    if row[1]:
        try:
            ban_until = datetime.fromisoformat(row[1])
            if datetime.now() >= ban_until:
                unban_player(user_id)
                return False
        except:
            pass
    return True


# ═══════════════════════════════════════════════════════════════════
# КВАЛИФИКАЦИЯ (FPL QUALS)
# ═══════════════════════════════════════════════════════════════════

def grant_qual(user_id, league_name, days=30):
    conn = sqlite3.connect(DB)
    expires = (datetime.now() + timedelta(days=days)).isoformat()
    conn.execute("UPDATE players SET qual_league=?, qual_expires=? WHERE user_id=?",
                 (league_name, expires, user_id))
    conn.commit()
    conn.close()

def has_qual(user_id, league_name):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT qual_expires FROM players WHERE user_id=? AND qual_league=?", (user_id, league_name))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return datetime.fromisoformat(row[0]) > datetime.now()
        except:
            return False
    return False


# ═══════════════════════════════════════════════════════════════════
# ИНВЕНТАРЬ
# ═══════════════════════════════════════════════════════════════════

def get_inventory(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, item_name, item_type, item_id, activated, expires_at FROM inventory WHERE user_id=? AND active=1", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_inventory_item(inv_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory WHERE id=?", (inv_id,))
    row = cur.fetchone()
    conn.close()
    return row

def add_inventory_item(user_id, item_name, item_type, days=None, item_id=None, activated=0):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    expires = (datetime.now() + timedelta(days=days)).isoformat() if days else None
    cur.execute("INSERT INTO inventory(user_id, item_name, item_type, item_id, active, activated, expires_at) VALUES(?,?,?,?,1,?,?)",
                (user_id, item_name, item_type, item_id, activated, expires))
    row_id = cur.lastrowid
    conn.commit()
    conn.close()
    return row_id

def remove_inventory_item(inv_id):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM inventory WHERE id=?", (inv_id,))
    conn.commit()
    conn.close()

def activate_inventory_item(inv_id):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE inventory SET activated=1 WHERE id=?", (inv_id,))
    conn.commit()
    conn.close()

def has_active_item(user_id, item_type):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id FROM inventory WHERE user_id=? AND item_type=? AND active=1 AND activated=1 LIMIT 1", (user_id, item_type))
    row = cur.fetchone()
    conn.close()
    return row is not None


# ═══════════════════════════════════════════════════════════════════
# ТИКЕТЫ (ЖАЛОБЫ)
# ═══════════════════════════════════════════════════════════════════

def create_ticket(user_id, match_id, reason):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    created_at = datetime.now().isoformat()
    cur.execute("INSERT INTO tickets(user_id, match_id, reason, status, created_at) VALUES(?,?,?,?,?)",
                (user_id, match_id, reason, 'open', created_at))
    ticket_id = cur.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

def get_tickets(status=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM tickets WHERE status=? ORDER BY created_at DESC", (status,))
    else:
        cur.execute("SELECT * FROM tickets ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_ticket(ticket_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,))
    row = cur.fetchone()
    conn.close()
    return row

def resolve_ticket(ticket_id, admin_id, comment):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    resolved_at = datetime.now().isoformat()
    cur.execute("UPDATE tickets SET status='resolved', resolved_by=?, resolved_at=?, admin_comment=? WHERE id=?",
                (admin_id, resolved_at, comment, ticket_id))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════
# ПАТИ
# ═══════════════════════════════════════════════════════════════════

def create_party(leader_id, code):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    created_at = datetime.now().isoformat()
    cur.execute("INSERT INTO parties(leader_id, code, created_at) VALUES(?,?,?)", (leader_id, code, created_at))
    party_id = cur.lastrowid
    cur.execute("INSERT INTO party_members(party_id, user_id, joined_at) VALUES(?,?,?)", (party_id, leader_id, created_at))
    conn.commit()
    conn.close()
    return party_id

def get_party_by_code(code):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, leader_id FROM parties WHERE code=? AND status='waiting'", (code,))
    row = cur.fetchone()
    conn.close()
    return row

def get_party_members(party_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM party_members WHERE party_id=?", (party_id,))
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_to_party(party_id, user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO party_members(party_id, user_id, joined_at) VALUES(?,?,?)", 
                (party_id, user_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def remove_from_party(party_id, user_id):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM party_members WHERE party_id=? AND user_id=?", (party_id, user_id))
    conn.commit()
    conn.close()

def close_party(party_id):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE parties SET status='closed' WHERE id=?", (party_id,))
    conn.commit()
    conn.close()

def get_user_party(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT party_id FROM party_members WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None