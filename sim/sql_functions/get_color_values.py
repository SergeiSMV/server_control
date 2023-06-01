from connections import sim_connect, sim_cursor


async def get_color_values(color_id):
    # получаем цвет ТМЦ по id
    color_sql = 'SELECT color FROM colors WHERE id =%s'
    color_val = (color_id,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(color_sql, color_val)
    color_result = sim_cursor.fetchone()
    sim_connect.commit()

    color = color_result['color']
    return color
