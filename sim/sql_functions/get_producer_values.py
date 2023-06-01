from connections import sim_connect, sim_cursor


async def get_producer_values(producer_id):
    # получаем поставщика ТМЦ по id
    producer_sql = 'SELECT producer FROM producers WHERE id =%s'
    producer_val = (producer_id,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(producer_sql, producer_val)
    producer_result = sim_cursor.fetchone()
    sim_connect.commit()

    producer = producer_result['producer']
    return producer
