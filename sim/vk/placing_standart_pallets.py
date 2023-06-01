from connections import sim_connect, sim_cursor
from sim.sql_functions.get_color_id import get_color_id
from sim.sql_functions.get_nm_item_id import get_nm_item_id
from sim.sql_functions.get_producer_id import get_producer_id
from sim.sql_functions.get_unit_id import get_unit_id
from datetime import datetime

from sim.vk.registrator import registrator


async def placing_standart_pallets(data, pallet_height, pallet_count):
    pallet_quantity = data['pallet_quantity']  # количество ТМЦ на паллете
    quantity_move = data['quantity_move']  # количество ТМЦ для размещения
    item_id = data['itemId']
    document = data['document']
    status = data['status']
    category = data['category']
    name = data['name']
    producer = data['producer']
    color = data['color']
    unit = data['unit']
    fifo = datetime.strptime(data['fifo'], '%d.%m.%Y')
    author = data['author']
    pallet_size = data['pallet_size']  # размер паллета

    quantity_residue = int(quantity_move)  # остаток для размещения
    pallet_residue = int(quantity_residue) / int(pallet_quantity)

    producer_id = await get_producer_id(producer)
    unit_id = await get_unit_id(unit)
    nm_item_id = await get_nm_item_id(category, name, producer_id, unit_id)
    color_id = await get_color_id(color) if color != '' else 0

    for x in range(int(pallet_count)):

        # ищем первую ячейку со статусом "empty"
        search_cell = 'SELECT * FROM places WHERE own = "sim" AND status = "empty" AND height >= %s'
        search_value = (int(pallet_height),)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(search_cell, search_value)
        cell = sim_cursor.fetchone()
        sim_connect.commit()

        if cell is None:
            new_data = data
            del new_data['document']
            del new_data['status']
            del new_data['quantity_move']
            del new_data['itemId']

            for z in range(int(pallet_residue)):

                new_data['quantity'] = pallet_quantity
                # создаем новую позицию в базе ВК, указываем документ, статус
                add_to_vk = 'INSERT INTO vk_items (data, document, status) VALUES (%s, %s, %s)'
                vk_value = (str(new_data), document, status)
                sim_connect.ping(reconnect=True)
                sim_cursor.execute(add_to_vk, vk_value)
                sim_cursor.fetchall()
                sim_connect.commit()

                quantity_residue = quantity_residue - int(pallet_quantity)
            break
        else:
            # добавляем паллет в базу СиМ
            add_to_sim = 'INSERT INTO items (place, name, color, quant, fifo, author, status, pallet_size) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
            sim_value = (cell['id'], nm_item_id, color_id, pallet_quantity, fifo, author, status, pallet_size)
            sim_connect.ping(reconnect=True)
            sim_cursor.execute(add_to_sim, sim_value)
            sim_cursor.fetchall()
            sim_connect.commit()

            # запись в историю + отправка QR кода
            await registrator(data, cell['id'])

            # обновляем статус empty ячейки
            busy_cell = 'UPDATE places SET status = "busy" WHERE id = %s'
            update_busy_cell = (cell['id'],)
            sim_connect.ping(reconnect=True)
            sim_cursor.execute(busy_cell, update_busy_cell)
            sim_cursor.fetchall()
            sim_connect.commit()

            quantity_residue = quantity_residue - int(pallet_quantity)

            continue

    # если остаток для размещения = 0 удаляем основную позицию из склада ВК
    if quantity_residue == 0:
        sql = 'DELETE FROM vk_items WHERE id = %s'
        sql_value = (item_id,)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(sql, sql_value)
        sim_cursor.fetchall()
        sim_connect.commit()
    # иначе создаем новые позиции для ручного размещения
    else:
        data['itemId'] = item_id
        await no_places(data, quantity_residue)


# нет ячеек доступных для размещения
async def no_places(data, quantity_residue):

    item_id = data['itemId']
    document = data['document']
    status = data['status']
    pallet_quantity = data['pallet_quantity']  # количество ТМЦ на паллете

    pallet_residue = int(quantity_residue) / int(pallet_quantity)
    residue = int(quantity_residue)

    create_data = data
    del create_data['document']
    del create_data['status']
    del create_data['quantity_move']
    del create_data['itemId']
    del create_data['exceptions']
    del create_data['place']
    del create_data['cell']

    for x in range(int(pallet_residue)):

        create_data['quantity'] = pallet_quantity
        # создаем новую позицию в базе ВК, указываем документ, статус
        add_to_vk = 'INSERT INTO vk_items (data, document, status) VALUES (%s, %s, %s)'
        vk_value = (str(create_data), document, status)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(add_to_vk, vk_value)
        sim_cursor.fetchall()
        sim_connect.commit()

        residue = residue - int(pallet_quantity)

    if residue == 0:
        sql = 'DELETE FROM vk_items WHERE id = %s'
        sql_value = (item_id,)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(sql, sql_value)
        sim_cursor.fetchall()
        sim_connect.commit()
    else:
        new_data = data
        del new_data['document']
        del new_data['status']
        del new_data['quantity_move']
        del new_data['itemId']

        new_data['quantity'] = residue
        # обновляем текущую позицию в базе ВК, корретируем количество, без документа и статуса
        update_place = 'UPDATE vk_items SET data = %s WHERE id = %s'
        update_value = (str(new_data), item_id)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(update_place, update_value)
        sim_cursor.fetchall()
        sim_connect.commit()




