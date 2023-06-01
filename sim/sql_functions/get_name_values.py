from connections import sim_connect, sim_cursor


async def get_name_values(name_id):
    # получаем категорию и наименование по id
    name_sql = 'SELECT category, name FROM nomenclature WHERE id =%s'
    name_val = (name_id,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(name_sql, name_val)
    name_result = sim_cursor.fetchone()
    sim_connect.commit()

    result = {'category': name_result['category'], 'name': name_result['name']}
    return result
