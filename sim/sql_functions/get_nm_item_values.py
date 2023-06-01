from connections import sim_connect, sim_cursor
from sim.sql_functions.get_producer_values import get_producer_values
from sim.sql_functions.get_unit_values import get_unit_values


async def get_nm_item_values(item_id):
    # получаем категорию, наименование, поставщика и единицу измерения по id
    name_sql = 'SELECT category, name, producer, unit FROM nomenclature WHERE id =%s'
    name_val = (item_id,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(name_sql, name_val)
    name_result = sim_cursor.fetchone()
    sim_connect.commit()

    result = {
        'category': name_result['category'],
        'name': name_result['name'],
        'producer': await get_producer_values(name_result['producer']),
        'unit': await get_unit_values(name_result['unit'])
    }
    return result
