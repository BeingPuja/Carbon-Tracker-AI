from backend.database import get_conn


def create_user(username, password):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
    finally:
        conn.close()


def find_user(username):
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user


def add_or_update_entry(user_id, date, data):
    conn = get_conn()
    cursor = conn.cursor()
    # delete if exists for today
    cursor.execute("DELETE FROM entries WHERE user_id=? AND date=?", (user_id, date))
   
    # Explicitly convert to float and use a default of 0 to prevent database errors
    distance = float(data.get('distance', 0) or 0)
    kwh = float(data.get('kwh', 0) or 0)
    meals = float(data.get('meals', 0) or 0)
   
    # Get the other values
    mode = data.get('mode')
    diet = data.get('diet')
    transport_em = data.get('transport_em')
    energy_em = data.get('energy_em')
    diet_em = data.get('diet_em')
    total = data.get('total')


    cursor.execute("""
        INSERT INTO entries (user_id, date, distance, mode, kwh, meals, diet,
                             transport_em, energy_em, diet_em, total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        date,
        distance,
        mode,
        kwh,
        meals,
        diet,
        transport_em,
        energy_em,
        diet_em,
        total
    ))
    conn.commit()
    conn.close()


def get_entries(user_id):
    conn = get_conn()
    entries = conn.execute("SELECT * FROM entries WHERE user_id=? ORDER BY date ASC", (user_id,)).fetchall()
    conn.close()
    return [dict(row) for row in entries]


def get_entries_since_date(user_id, date_str):
    conn = get_conn()
    entries = conn.execute("SELECT * FROM entries WHERE user_id=? AND date>=? ORDER BY date ASC", (user_id, date_str)).fetchall()
    conn.close()
    return [dict(row) for row in entries]
