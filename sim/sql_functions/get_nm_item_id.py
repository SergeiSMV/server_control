from connections import sim_connect, sim_cursor


async def get_nm_item_id(category, name, producer, unit):
    # получаем id ТМЦ из номенклатуры
    name_sql = 'SELECT id FROM nomenclature WHERE category = %s AND name = %s AND producer = %s AND unit = %s'
    name_val = (category, name, producer, unit)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(name_sql, name_val)
    name_result = sim_cursor.fetchone()
    sim_connect.commit()

    nm_item_id = name_result['id']
    return nm_item_id
