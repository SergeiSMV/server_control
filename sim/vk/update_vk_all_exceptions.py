
from connections import sim_connect, sim_cursor
from sim.vk.vk_all_items import f_vk_all_items

# обновление документа и статуса в основной позиции ВК
# при полном прохождении входного контроля или отбраковки
# при наличии ТМЦ в списке исключения


async def update_vk_all_exceptions(data):

    item_id = data['itemId']
    document = data['document']
    status = data['status']

    update_place = 'UPDATE vk_items SET document = %s, status = %s  WHERE id = %s'
    update_value = (document, status, item_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(update_place, update_value)
    sim_cursor.fetchall()
    sim_connect.commit()

    await f_vk_all_items(broadcast=True)
