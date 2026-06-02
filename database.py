import sqlite3
from datetime import datetime, timedelta

DB = 'faceit.db'
CALIB_THRESHOLD = 10

def init_db():
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id              INTEGER PRIMARY KEY,
            username             TEXT,
            game_id              TEXT,
            device               TEXT,
            level                INTEGER DEFAULT 1,
            elo                  INTEGER DEFAULT 1000,
            coins                INTEGER DEFAULT 100,
            wins                 INTEGER DEFAULT 0,
            losses               INTEGER DEFAULT 0,
            kills                INTEGER DEFAULT 0,
            deaths               INTEGER DEFAULT 0,
            assists              INTEGER DEFAULT 0,
            mvp                  INTEGER DEFAULT 0,
            headshots            INTEGER DEFAULT 0,
            avg_damage           REAL    DEFAULT 0,
            kd_ratio             REAL    DEFAULT 0,
            winrate              REAL    DEFAULT 0,
            is_admin             INTEGER DEFAULT 0,
            registered           INTEGER DEFAULT 0,
            qual_league          TEXT    DEFAULT NULL,
            qual_expires         TEXT    DEFAULT NULL,
            is_bot               INTEGER DEFAULT 0,
            badges               TEXT    DEFAULT '',
            warns                INTEGER DEFAULT 0,
            muted_until          TEXT    DEFAULT NULL,
            banned               INTEGER DEFAULT 0,
            calibration_matches  INTEGER DEFAULT 0,
            warn_reasons         TEXT    DEFAULT NULL,
            warn_by              TEXT    DEFAULT NULL,
            mute_reason          TEXT    DEFAULT NULL,
            mute_by              TEXT    DEFAULT NULL,
            ban_until            TEXT    DEFAULT NULL,
            ban_reason           TEXT    DEFAULT NULL,
            ban_by               TEXT    DEFAULT NULL,
            ban_type             TEXT    DEFAULT NULL
        )
    ''')

    for col, dfn in [
        ("is_bot",             "INTEGER DEFAULT 0"),
        ("badges",             "TEXT DEFAULT ''"),
        ("warns",              "INTEGER DEFAULT 0"),
        ("muted_until",        "TEXT DEFAULT NULL"),
        ("banned",             "INTEGER DEFAULT 0"),
        ("calibration_matches","INTEGER DEFAULT 0"),
        ("warn_reasons",       "TEXT DEFAULT NULL"),
        ("warn_by",            "TEXT DEFAULT NULL"),
        ("mute_reason",        "TEXT DEFAULT NULL"),
        ("mute_by",            "TEXT DEFAULT NULL"),
        ("ban_until",          "TEXT DEFAULT NULL"),
        ("ban_reason",         "TEXT DEFAULT NULL"),
        ("ban_by",             "TEXT DEFAULT NULL"),
        ("ban_type",           "TEXT DEFAULT NULL"),
    ]:
        try:
            cur.execute(f"ALTER TABLE players ADD COLUMN {col} {dfn}")
        except Exception:
            pass

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
    for col, dfn in [("item_id","TEXT DEFAULT NULL"),("activated","INTEGER DEFAULT 0")]:
        try:
            cur.execute(f"ALTER TABLE inventory ADD COLUMN {col} {dfn}")
        except Exception:
            pass

    cur.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            match_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            lobby_key  TEXT,
            map_name   TEXT,
            team_ct    TEXT,
            team_t     TEXT,
            league     TEXT,
            winner     TEXT    DEFAULT NULL,
            status     TEXT    DEFAULT 'active',
            score_ct   INTEGER DEFAULT 0,
            score_t    INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')
    for col, dfn in [("score_ct","INTEGER DEFAULT 0"),("score_t","INTEGER DEFAULT 0")]:
        try:
            cur.execute(f"ALTER TABLE matches ADD COLUMN {col} {dfn}")
        except Exception:
            pass

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
            impact    REAL    DEFAULT 0,
            kd        REAL    DEFAULT 0
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS league_stats (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  INTEGER,
            league   TEXT,
            wins     INTEGER DEFAULT 0,
            losses   INTEGER DEFAULT 0,
            kills    INTEGER DEFAULT 0,
            deaths   INTEGER DEFAULT 0,
            assists  INTEGER DEFAULT 0,
            elo      INTEGER DEFAULT 1000,
            UNIQUE(user_id, league)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS map_stats (
            map_name      TEXT PRIMARY KEY,
            times_played  INTEGER DEFAULT 0,
            times_picked  INTEGER DEFAULT 0,
            ct_wins       INTEGER DEFAULT 0,
            t_wins        INTEGER DEFAULT 0
        )
    ''')

    from config import MAPS
    for m in MAPS:
        cur.execute("INSERT OR IGNORE INTO map_stats (map_name) VALUES (?)", (m,))

    cur.execute('''
        INSERT OR IGNORE INTO players
            (user_id, username, game_id, device, registered, is_admin, coins, calibration_matches, elo, level)
        VALUES (8521250777,'Admin','8521250777','MOBILE',1,1,9999,10,1000,1)
    ''')
    cur.execute("UPDATE players SET is_admin=1 WHERE user_id=8521250777")
    conn.commit(); conn.close()


# ── Getters ────────────────────────────────────────────────

def get_player(user_id):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute("SELECT * FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone(); conn.close(); return row

def get_player_by_username(username):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute("SELECT * FROM players WHERE username=? LIMIT 1", (username,))
    row = cur.fetchone(); conn.close(); return row

def is_calibrated(player):
    if player is None: return False
    return (player[26] if len(player) > 26 else 0) >= CALIB_THRESHOLD

def calib_count(player):
    if player is None: return 0
    return player[26] if len(player) > 26 else 0


# ── Registration ───────────────────────────────────────────

def register_player(user_id, username, game_id, device):
    conn = sqlite3.connect(DB)
    conn.execute('''INSERT OR REPLACE INTO players
        (user_id, username, game_id, device, registered, coins, calibration_matches, elo, level)
        VALUES(?,?,?,?,1,100,0,1000,1)''', (user_id, username, game_id, device))
    conn.commit(); conn.close()

def register_bot(user_id, username, game_id, device):
    conn = sqlite3.connect(DB)
    conn.execute('''INSERT OR REPLACE INTO players
        (user_id, username, game_id, device, registered, is_bot, coins, calibration_matches, elo, level)
        VALUES(?,?,?,?,1,1,0,10,1000,1)''', (user_id, username, game_id, device))
    conn.commit(); conn.close()

def set_username(user_id, username):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET username=? WHERE user_id=?", (username, user_id))
    conn.commit(); conn.close()

def set_game_id(user_id, game_id):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET game_id=? WHERE user_id=?", (game_id, user_id))
    conn.commit(); conn.close()


# ── Admin ──────────────────────────────────────────────────

def set_admin(user_id, value=1):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET is_admin=? WHERE user_id=?", (value, user_id))
    conn.commit(); conn.close()

def get_all_admins():
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute("SELECT user_id FROM players WHERE is_admin=1")
    rows = cur.fetchall(); conn.close()
    return [r[0] for r in rows]


# ── Badges ─────────────────────────────────────────────────

def add_badge(user_id, badge):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute("SELECT badges FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row: conn.close(); return
    badges = [b for b in (row[0] or '').split(',') if b]
    if badge not in badges: badges.append(badge)
    cur.execute("UPDATE players SET badges=? WHERE user_id=?", (','.join(badges), user_id))
    conn.commit(); conn.close()

def remove_badge(user_id, badge):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute("SELECT badges FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row: conn.close(); return
    badges = [b for b in (row[0] or '').split(',') if b and b != badge]
    cur.execute("UPDATE players SET badges=? WHERE user_id=?", (','.join(badges), user_id))
    conn.commit(); conn.close()


# ── Coins ──────────────────────────────────────────────────

def add_coins(user_id, amount):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET coins=coins+? WHERE user_id=?", (amount, user_id))
    conn.commit(); conn.close()

def remove_coins(user_id, amount):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET coins=MAX(0,coins-?) WHERE user_id=?", (amount, user_id))
    conn.commit(); conn.close()

def set_coins(user_id, amount):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET coins=? WHERE user_id=?", (amount, user_id))
    conn.commit(); conn.close()


# ── ELO / Level ────────────────────────────────────────────

def set_elo(user_id, amount):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET elo=? WHERE user_id=?", (amount, user_id))
    conn.commit(); conn.close()

def add_elo(user_id, amount):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET elo=MAX(0,elo+?) WHERE user_id=?", (amount, user_id))
    conn.commit(); conn.close()

def elo_to_level(elo):
    if   elo <  200: return 1
    elif elo <  400: return 2
    elif elo <  600: return 3
    elif elo <  900: return 4
    elif elo < 1100: return 5
    elif elo < 1400: return 6
    elif elo < 1600: return 7
    elif elo < 1800: return 8
    elif elo < 2000: return 9
    else:            return 10

def set_level(user_id, level):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET level=? WHERE user_id=?", (level, user_id))
    conn.commit(); conn.close()


# ── Stats ──────────────────────────────────────────────────

def set_player_stats(user_id, kills=None, deaths=None, assists=None,
                     wins=None, losses=None, mvp=None, headshots=None):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    fields, vals = [], []
    for name, val in [("kills",kills),("deaths",deaths),("assists",assists),
                      ("wins",wins),("losses",losses),("mvp",mvp),("headshots",headshots)]:
        if val is not None:
            fields.append(f"{name}=?"); vals.append(val)
    if fields:
        vals.append(user_id)
        cur.execute(f"UPDATE players SET {','.join(fields)} WHERE user_id=?", vals)
    conn.commit(); conn.close()

def update_stats(user_id, kills, deaths, assists, headshots, avg_damage, win, league=None):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute("SELECT calibration_matches, elo FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    calib   = row[0] if row else 0
    cur_elo = row[1] if row else 1000

    elo_delta = (40 if calib < CALIB_THRESHOLD else 25) if win else (-30 if calib < CALIB_THRESHOLD else -25)
    if calib < CALIB_THRESHOLD: calib += 1
    new_elo = max(100, cur_elo + elo_delta)

    new_level = elo_to_level(new_elo)
    conn.execute('''UPDATE players SET
        kills=kills+?, deaths=deaths+?, assists=assists+?, headshots=headshots+?,
        wins=wins+?, losses=losses+?, elo=?, level=?, calibration_matches=?
        WHERE user_id=?''',
        (kills, deaths, assists, headshots,
         1 if win else 0, 0 if win else 1,
         new_elo, new_level, calib, user_id))

    if league:
        conn.execute('''INSERT OR IGNORE INTO league_stats(user_id,league) VALUES(?,?)''',
                     (user_id, league))
        conn.execute('''UPDATE league_stats SET
            kills=kills+?, deaths=deaths+?, assists=assists+?,
            wins=wins+?, losses=losses+?, elo=?
            WHERE user_id=? AND league=?''',
            (kills, deaths, assists,
             1 if win else 0, 0 if win else 1,
             new_elo, user_id, league))
    conn.commit(); conn.close()
    return calib, new_elo

def get_league_stats(user_id, league):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute("SELECT * FROM league_stats WHERE user_id=? AND league=?", (user_id, league))
    row = cur.fetchone(); conn.close(); return row

def reset_player_stats(user_id):
    conn = sqlite3.connect(DB)
    conn.execute('''UPDATE players SET kills=0,deaths=0,assists=0,mvp=0,headshots=0,
        avg_damage=0,wins=0,losses=0,kd_ratio=0,winrate=0,elo=1000,calibration_matches=0,level=1
        WHERE user_id=?''', (user_id,))
    conn.execute("DELETE FROM league_stats WHERE user_id=?", (user_id,))
    conn.commit(); conn.close()


# ── Quals ──────────────────────────────────────────────────

def grant_qual(user_id, league_name, days=30):
    conn = sqlite3.connect(DB)
    expires = (datetime.now() + timedelta(days=days)).isoformat()
    conn.execute("UPDATE players SET qual_league=?,qual_expires=? WHERE user_id=?",
                 (league_name, expires, user_id))
    conn.commit(); conn.close()


# ── Inventory ──────────────────────────────────────────────

def get_inventory(user_id):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute(
        "SELECT id,item_name,item_type,item_id,activated,expires_at "
        "FROM inventory WHERE user_id=? AND active=1",
        (user_id,)
    )
    rows = cur.fetchall(); conn.close(); return rows

def get_inventory_item(inv_id):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute("SELECT * FROM inventory WHERE id=?", (inv_id,))
    row = cur.fetchone(); conn.close(); return row

def add_inventory_item(user_id, item_name, item_type, days=None, item_id=None, activated=0):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    expires = (datetime.now() + timedelta(days=days)).isoformat() if days else None
    cur.execute(
        "INSERT INTO inventory(user_id,item_name,item_type,item_id,active,activated,expires_at) "
        "VALUES(?,?,?,?,1,?,?)",
        (user_id, item_name, item_type, item_id, activated, expires)
    )
    row_id = cur.lastrowid; conn.commit(); conn.close(); return row_id

def remove_inventory_item(inv_id):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM inventory WHERE id=?", (inv_id,))
    conn.commit(); conn.close()

def deactivate_inventory_item(inv_id):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE inventory SET active=0 WHERE id=?", (inv_id,))
    conn.commit(); conn.close()

def activate_inventory_item(inv_id):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE inventory SET activated=1 WHERE id=?", (inv_id,))
    conn.commit(); conn.close()

def has_active_item_type(user_id, item_type):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute(
        "SELECT id FROM inventory WHERE user_id=? AND item_type=? AND active=1 AND activated=1 LIMIT 1",
        (user_id, item_type)
    )
    row = cur.fetchone(); conn.close(); return row is not None

def cleanup_expired_items():
    conn = sqlite3.connect(DB)
    now  = datetime.now().isoformat()
    conn.execute("DELETE FROM inventory WHERE expires_at IS NOT NULL AND expires_at < ? AND active=1", (now,))
    conn.commit(); conn.close()


# ── Top ────────────────────────────────────────────────────

def get_top_players(limit=10):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute('''SELECT username,game_id,elo,wins,losses,kills,deaths
        FROM players WHERE registered=1 AND is_bot=0 AND calibration_matches>=10
        ORDER BY elo DESC LIMIT ?''', (limit,))
    rows = cur.fetchall(); conn.close(); return rows


# ── Matches ────────────────────────────────────────────────

def save_match(lobby_key, map_name, team_ct, team_t, league):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute('''INSERT INTO matches(lobby_key,map_name,team_ct,team_t,league,status,created_at)
        VALUES(?,?,?,?,?,'active',?)''',
        (lobby_key, map_name,
         ','.join(map(str, team_ct)),
         ','.join(map(str, team_t)),
         league, datetime.now().isoformat()))
    mid = cur.lastrowid
    cur.execute("UPDATE map_stats SET times_played=times_played+1,times_picked=times_picked+1 "
                "WHERE map_name=?", (map_name,))
    conn.commit(); conn.close(); return mid

def finalize_match(match_id, status='cancelled'):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE matches SET status=? WHERE match_id=?", (status, match_id))
    conn.commit(); conn.close()

def finalize_match_with_winner(match_id, winner_side, map_name, score_ct=0, score_t=0):
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute("UPDATE matches SET winner=?,status='done',score_ct=?,score_t=? WHERE match_id=?",
                (winner_side, score_ct, score_t, match_id))
    if map_name and winner_side in ("ct","t"):
        field = "ct_wins" if winner_side=="ct" else "t_wins"
        cur.execute(f"UPDATE map_stats SET {field}={field}+1 WHERE map_name=?", (map_name,))
    conn.commit(); conn.close()

def save_match_player_stats(match_id, user_id, side, kills, deaths, assists, rating, impact, kd):
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO match_player_stats(match_id,user_id,side,kills,deaths,assists,rating,impact,kd) "
        "VALUES(?,?,?,?,?,?,?,?,?)",
        (match_id, user_id, side, kills, deaths, assists, rating, impact, kd)
    )
    conn.commit(); conn.close()


# ── Map stats ──────────────────────────────────────────────

def get_map_stats():
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute("SELECT map_name,times_played,times_picked,ct_wins,t_wins FROM map_stats")
    rows = cur.fetchall(); conn.close()
    total = sum(r[1] for r in rows) or 1
    result = {}
    for mn, played, picked, ct_w, t_w in rows:
        total_m = ct_w + t_w or 1
        result[mn] = {"times_played":played,
                      "pick_pct":round(picked/total*100,1),
                      "ct_wr":round(ct_w/total_m*100,1),
                      "t_wr":round(t_w/total_m*100,1)}
    return result


# ── Расширенная система наказаний ──────────────────────────────────────

def add_warn(user_id, reason=None, admin_id=None):
    """Добавить варн с причиной и кто выдал"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    cur.execute("SELECT warns, warn_reasons, warn_by FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    
    current_warns = row[0] if row else 0
    current_reasons = row[1] if row and row[1] else ""
    current_by = row[2] if row and row[2] else ""
    
    new_warns = current_warns + 1
    
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    new_reason_entry = f"[{timestamp}] {reason if reason else 'Не принял матч'}"
    new_by_entry = f"[{timestamp}] {admin_id if admin_id else 'Система'}"
    
    updated_reasons = f"{current_reasons}\n{new_reason_entry}" if current_reasons else new_reason_entry
    updated_by = f"{current_by}\n{new_by_entry}" if current_by else new_by_entry
    
    cur.execute("""
        UPDATE players SET 
            warns=?, 
            warn_reasons=?, 
            warn_by=?
        WHERE user_id=?
    """, (new_warns, updated_reasons, updated_by, user_id))
    
    conn.commit()
    conn.close()
    return new_warns

def remove_warn(user_id):
    """Снять один варн"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE players SET warns=MAX(0,warns-1) WHERE user_id=?", (user_id,))
    cur.execute("SELECT warns FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.commit()
    conn.close()
    return row[0] if row else 0

def clear_warns(user_id):
    """Очистить все варны"""
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET warns=0, warn_reasons=NULL, warn_by=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_warns_full(user_id):
    """Получить полную информацию о варнах"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT warns, warn_reasons, warn_by FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"count": row[0] or 0, "reasons": row[1], "by": row[2]}
    return {"count": 0, "reasons": None, "by": None}

def mute_player(user_id, hours=2, reason=None, admin_id=None):
    """Замутить игрока"""
    conn = sqlite3.connect(DB)
    until = (datetime.now() + timedelta(hours=hours)).isoformat()
    conn.execute("""
        UPDATE players SET 
            muted_until=?, 
            mute_reason=?, 
            mute_by=?
        WHERE user_id=?
    """, (until, reason, admin_id, user_id))
    conn.commit()
    conn.close()
    return until

def unmute_player(user_id):
    """Снять мут"""
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE players SET muted_until=NULL, mute_reason=NULL, mute_by=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_muted_full(user_id):
    """Проверить, замучен ли игрок, с деталями"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT muted_until, mute_reason, mute_by FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row or not row[0]:
        return False, None, None, None
    until = datetime.fromisoformat(row[0])
    if datetime.now() >= until:
        unmute_player(user_id)
        return False, None, None, None
    return True, row[0], row[1], row[2]

def ban_player(user_id, days=None, reason=None, admin_id=None):
    """Забанить игрока (навсегда или на days дней)"""
    conn = sqlite3.connect(DB)
    
    if days:
        until = (datetime.now() + timedelta(days=days)).isoformat()
        ban_type = "temporary"
    else:
        until = None
        ban_type = "permanent"
    
    conn.execute("""
        UPDATE players SET 
            banned=1, 
            ban_until=?, 
            ban_reason=?, 
            ban_by=?, 
            ban_type=?
        WHERE user_id=?
    """, (until, reason, admin_id, ban_type, user_id))
    conn.commit()
    conn.close()

def unban_player(user_id):
    """Разбанить игрока"""
    conn = sqlite3.connect(DB)
    conn.execute("""
        UPDATE players SET 
            banned=0, 
            ban_until=NULL, 
            ban_reason=NULL, 
            ban_by=NULL, 
            ban_type=NULL
        WHERE user_id=?
    """, (user_id,))
    conn.commit()
    conn.close()

def is_banned_full(user_id):
    """Проверить, забанен ли игрок, с деталями"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT banned, ban_until, ban_reason, ban_by, ban_type FROM players WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    
    if not row or not row[0]:
        return False, None, None, None, None
    
    if row[1]:
        ban_until = datetime.fromisoformat(row[1])
        if datetime.now() >= ban_until:
            unban_player(user_id)
            return False, None, None, None, None
    
    return True, row[1], row[2], row[3], row[4]


# ── Совместимость со старыми функциями ─────────────────────────────────

def get_warns(user_id):
    """Старая функция для совместимости"""
    return get_warns_full(user_id)["count"]

def is_muted(user_id):
    """Старая функция для совместимости"""
    muted, until, reason, by = is_muted_full(user_id)
    return muted, until

def is_banned(user_id):
    """Старая функция для совместимости"""
    banned, until, reason, by, ban_type = is_banned_full(user_id)
    return banned