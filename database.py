def _timeout_warn(key, uid):
    lob = active_lobbies.get(key)
    if not lob or lob["status"] != "accept": return
    if uid in lob["ready"]: return
    _leave_lobby(uid, key)
    
    warns = add_warn(uid, reason="Не принял матч", admin_id=None)
    name = _pname(uid)
    
    try:
        bot.send_message(uid, 
            f"⚠️ <b>Варн!</b> Не принял матч.\n"
            f"Варнов: {warns}/3\n"
            f"Причина: Не принял матч в течение {ACCEPT_TIMEOUT} секунд",
            parse_mode="HTML")
    except:
        pass
    
    send_log(f"⚠️ {name} не принял матч. Варнов: {warns}")
    
    # При 3 варнах - мут на 2 часа
    if warns >= 3:
        clear_warns(uid)
        until = mute_player(uid, hours=2, reason="3 варна (не принятие матчей)", admin_id=None)
        try:
            bot.send_message(uid, 
                f"🔇 <b>Мут 2 часа!</b>\n"
                f"Причина: Накоплено 3 варна за не принятие матчей\n"
                f"До: {until[:16]}\n"
                f"Обратись к администратору для снятия",
                parse_mode="HTML")
        except:
            pass
        send_log(f"🔇 {name} мут 2ч за 3 варна")
    
    if len(lob["players"]) < 10 and lob["status"] == "accept":
        lob["status"] = "waiting"
        _bcast(lob, "❌ Игрок не принял. Набор возобновлён...")