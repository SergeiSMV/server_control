from connections import sim_connect, sim_cursor


async def get_unit_values(unit_id):
    # получаем единицу измерения ТМЦ по id
    unit_sql = 'SELECT unit FROM units WHERE id =%s'
    unit_val = (unit_id,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(unit_sql, unit_val)
    unit_result = sim_cursor.fetchone()
    sim_connect.commit()

    unit = unit_result['unit']
    return unit
