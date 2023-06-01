from connections import sim_connect, sim_cursor


async def get_unit_id(unit):
    # получаем id единицы измерения
    unit_sql = 'SELECT id FROM units WHERE unit = %s'
    unit_val = (unit,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(unit_sql, unit_val)
    unit_result = sim_cursor.fetchone()
    sim_connect.commit()

    unit_id = unit_result['id']
    return unit_id
