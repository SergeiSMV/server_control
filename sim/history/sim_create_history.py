from datetime import date
from connections import sim_connect, sim_cursor


async def sim_create_history(item_id, action, comment, author):
    action_date = date.today().strftime('%Y-%m-%d')

    # добавляем данные в базу заявок
    sql = 'INSERT INTO history (item_id, action, comment, date, author) VALUES (%s, %s, %s, %s, %s)'
    val = (item_id, action, comment, action_date, author)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, val)
    sim_cursor.fetchall()
    sim_connect.commit()
