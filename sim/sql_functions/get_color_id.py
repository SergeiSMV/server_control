from connections import sim_connect, sim_cursor


async def get_color_id(color):
    # получаем id цвета, если значение не пустое
    color_sql = 'SELECT id FROM colors WHERE color = %s'
    color_val = (color,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(color_sql, color_val)
    color_result = sim_cursor.fetchone()
    sim_connect.commit()

    color_id = color_result['id']
    return color_id
