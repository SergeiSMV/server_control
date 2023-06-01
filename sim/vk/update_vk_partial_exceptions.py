
from connections import sim_connect, sim_cursor
from sim.vk.vk_all_items import f_vk_all_items


# создание новой позиции со статусом и документом + обновление основной позиции
# при частичном прохождении входного контроля (в списке исключения)
# при наличии ТМЦ в списке исключения


async def update_vk_partial_exceptions(data):
    item_id = data['itemId']
    document = data['document']
    status = data['status']
    quantity_move = data['quantity_move']
    quantity = data['quantity']

    new_data = data
    del new_data['document']
    del new_data['status']
    del new_data['quantity_move']
    del new_data['itemId']

    # обновляем текущую позицию в базе ВК, корретируем количество, без документа и статуса
    new_data['quantity'] = int(quantity) - int(quantity_move)
    update_place = 'UPDATE vk_items SET data = %s WHERE id = %s'
    update_value = (str(new_data), item_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(update_place, update_value)
    sim_cursor.fetchall()
    sim_connect.commit()

    new_data['quantity'] = quantity_move
    # создаем новую позицию в базе ВК, указываем документ, статус
    add_to_vk = 'INSERT INTO vk_items (data, document, status) VALUES (%s, %s, %s)'
    vk_value = (str(new_data), document, status)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(add_to_vk, vk_value)
    sim_cursor.fetchall()
    sim_connect.commit()

    await f_vk_all_items(broadcast=True)