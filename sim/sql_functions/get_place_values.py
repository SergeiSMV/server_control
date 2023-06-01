
from connections import sim_connect, sim_cursor


async def get_place_values(place_id):
    # получаем место и ячейку хранения по id
    place_sql = 'SELECT place, cell FROM places WHERE id =%s'
    place_val = (place_id,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(place_sql, place_val)
    place_result = sim_cursor.fetchone()
    sim_connect.commit()

    result = {'place': place_result['place'], 'cell': place_result['cell']}
    return result
