from connections import sim_connect, sim_cursor


async def get_place_id(place, cell):
    # получаем id места и ячейку хранения по id
    place_sql = 'SELECT id FROM places WHERE place = %s AND cell = %s'
    place_val = (place, cell)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(place_sql, place_val)
    place_result = sim_cursor.fetchone()
    sim_connect.commit()

    place_id = place_result['id']
    return place_id
