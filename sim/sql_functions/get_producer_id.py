from connections import sim_connect, sim_cursor


async def get_producer_id(producer):
    # получаем id поставщика ТМЦ
    producer_sql = 'SELECT id FROM producers WHERE producer = %s'
    producer_val = (producer,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(producer_sql, producer_val)
    producer_result = sim_cursor.fetchone()
    sim_connect.commit()

    producer_id = producer_result['id']
    return producer_id
