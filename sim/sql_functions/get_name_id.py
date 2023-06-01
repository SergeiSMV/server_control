from connections import sim_connect, sim_cursor


async def get_name_id(category, name, producer):
    # получаем id ТМЦ по категории, наименованию и поставщику
    name_sql = 'SELECT id FROM nomenclature WHERE category = %s AND name = %s AND producer = %s'
    name_val = (category, name, producer)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(name_sql, name_val)
    name_result = sim_cursor.fetchone()
    sim_connect.commit()

    name_id = name_result['id']
    return name_id
