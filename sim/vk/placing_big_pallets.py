from connections import sim_connect, sim_cursor
from datetime import datetime

from sim.sql_functions.get_color_id import get_color_id
from sim.sql_functions.get_nm_item_id import get_nm_item_id
from sim.sql_functions.get_producer_id import get_producer_id
from sim.sql_functions.get_unit_id import get_unit_id
from sim.vk.registrator import registrator


async def placing_big_pallets(data, pallet_height, pallet_count):
    pallet_quantity = data['pallet_quantity']  # количество ТМЦ на паллете
    quantity_move = data['quantity_move']  # количество ТМЦ для размещения
    item_id = data['itemId']

    quantity_residue = int(quantity_move)  # остаток для размещения

    for x in range(int(pallet_count)):
        # ищем ближайшую ячейку со статусом "used"
        cell_used = await search_used_cells(pallet_height)

        # если нет ячеек со статусом "used"
        if cell_used is None:
            # выгружаем все ячейки со статусом "empty"
            cells_empty = await search_empty_cells(pallet_height)

            # если нет ячеек со статусом "empty"
            if not cells_empty:
                break

            # если найдена ячейка со статусом "empty"
            else:
                result = await empty_placing_pallet(data, cells_empty)
                quantity_residue = quantity_residue - int(pallet_quantity) if result == 'done' else None

                # если нет возможности размещения исходя из найденых пустых ячеек прерываем цикл
                if result == 'fail':
                    break
                # иначе продолжаем цикл
                else:
                    continue

        # если найдена ячейка со статусом "used"
        else:
            current_cell_id = cell_used['id']
            section_cells = await get_section_cells(cell_used['section'])

            for c in section_cells:
                if c['status'] == 'empty':
                    await used_placing_pallet(data, c['id'], current_cell_id)
                    quantity_residue = quantity_residue - int(pallet_quantity)
                    break
                else:
                    continue
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


# ищем ближайшую ячейку со статусом used
async def search_used_cells(pallet_height):
    search_cell = 'SELECT * FROM places WHERE own = "sim" AND status = "used" AND height >= %s'
    search_value = (int(pallet_height),)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(search_cell, search_value)
    cell = sim_cursor.fetchone()
    sim_connect.commit()

    return cell


# выгружаем все ячейки со статусом empty
async def search_empty_cells(pallet_height):
    search_cells = 'SELECT * FROM places WHERE own = "sim" AND status = "empty" AND height >= %s'
    search_value = (int(pallet_height),)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(search_cells, search_value)
    cells = sim_cursor.fetchall()
    sim_connect.commit()

    return cells


# выгружаем все ячейки в указанной секции
async def get_section_cells(section):
    get_cells = 'SELECT * FROM places WHERE section = %s'
    get_value = (section,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(get_cells, get_value)
    cells = sim_cursor.fetchall()
    sim_connect.commit()

    return cells


# размещаем паллет исходя из статуса ячейки used
async def used_placing_pallet(data, cell_id, current_cell_id):
    category = data['category']
    name = data['name']
    producer = data['producer']
    color = data['color']
    unit = data['unit']
    status = data['status']
    fifo = datetime.strptime(data['fifo'], '%d.%m.%Y')
    author = data['author']
    pallet_quantity = data['pallet_quantity']  # количество ТМЦ на паллете
    pallet_size = data['pallet_size']  # размер паллета

    producer_id = await get_producer_id(producer)
    unit_id = await get_unit_id(unit)
    nm_item_id = await get_nm_item_id(category, name, producer_id, unit_id)
    color_id = await get_color_id(color) if color != '' else 0

    # добавляем паллет в базу СиМ
    add_to_sim = 'INSERT INTO items (place, name, color, quant, fifo, author, status, pallet_size) VALUES (%s, %s, ' \
                 '%s, %s, %s, %s, %s, %s)'
    sim_value = (cell_id, nm_item_id, color_id, pallet_quantity, fifo, author, status, pallet_size)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(add_to_sim, sim_value)
    sim_cursor.fetchall()
    sim_connect.commit()

    # запись в историю + отправка QR кода
    await registrator(data, cell_id)

    # обновляем статус empty ячейки
    busy_cell = 'UPDATE places SET status = "busy" WHERE id = %s'
    update_busy_cell = (cell_id,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(busy_cell, update_busy_cell)
    sim_cursor.fetchall()
    sim_connect.commit()

    # обновляем статус used ячейки
    lock_cell = 'UPDATE places SET status = "lock" WHERE id = %s'
    update_lock_cell = (current_cell_id,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(lock_cell, update_lock_cell)
    sim_cursor.fetchall()
    sim_connect.commit()


# размещаем паллет исходя из статуса ячейки empty
async def empty_placing_pallet(data, cells_empty):
    category = data['category']
    name = data['name']
    producer = data['producer']
    color = data['color']
    unit = data['unit']
    status = data['status']
    fifo = datetime.strptime(data['fifo'], '%d.%m.%Y')
    author = data['author']
    pallet_quantity = data['pallet_quantity']  # количество ТМЦ на паллете
    pallet_size = data['pallet_size']  # размер паллета

    producer_id = await get_producer_id(producer)
    unit_id = await get_unit_id(unit)
    nm_item_id = await get_nm_item_id(category, name, producer_id, unit_id)
    color_id = await get_color_id(color) if color != '' else 0

    result = 'fail'

    for cell in cells_empty:
        current_cell = cell['cell']
        current_cell_id = cell['id']
        section_cells = await get_section_cells(cell['section'])
        current_cell_index = next((index for (index, d) in enumerate(section_cells) if d["cell"] == current_cell), None)
        section_cells_length = len(section_cells)

        current_cell_is_last = current_cell_index == section_cells_length - 1

        # если найденная ячейка оказалась последней в секции
        if current_cell_is_last:
            continue
        # если найденная ячейка оказалась не последней в секции
        else:
            next_cell_index = current_cell_index + 1  # индекс следующей ячейки
            next_cell_is_last = next_cell_index == section_cells_length - 1
            next_cell_status = section_cells[next_cell_index]['status']  # статус следующей ячейки
            next_cell_id = section_cells[next_cell_index]['id']  # id следующей ячейки

            if next_cell_status == 'empty':
                current_cell_new_status = 'used' if next_cell_is_last else 'busy'
                current_cell_new_status = 'lock' if section_cells_length == 2 else current_cell_new_status
                next_cell_new_status = 'busy' if next_cell_is_last else 'used'
                cell_to_base = next_cell_id if next_cell_is_last else cell['id']

                # добавляем паллет в базу СиМ
                add_to_sim = 'INSERT INTO items (place, name, color, quant, fifo, author, status, pallet_size) VALUES ' \
                             '(%s, %s, %s, %s, %s, %s, %s, %s)'
                sim_value = (cell_to_base, nm_item_id, color_id, pallet_quantity, fifo, author, status, pallet_size)
                sim_connect.ping(reconnect=True)
                sim_cursor.execute(add_to_sim, sim_value)
                sim_cursor.fetchall()
                sim_connect.commit()

                # запись в историю + отправка QR кода
                await registrator(data, cell_to_base)

                # обновляем статус ячейки 1
                status_cell_1 = 'UPDATE places SET status = %s WHERE id = %s'
                update_1 = (next_cell_new_status, next_cell_id)
                sim_connect.ping(reconnect=True)
                sim_cursor.execute(status_cell_1, update_1)
                sim_cursor.fetchall()
                sim_connect.commit()

                # обновляем статус ячейки 2
                status_cell_2 = 'UPDATE places SET status = %s WHERE id = %s'
                update_2 = (current_cell_new_status, current_cell_id)
                sim_connect.ping(reconnect=True)
                sim_cursor.execute(status_cell_2, update_2)
                sim_cursor.fetchall()
                sim_connect.commit()
                result = 'done'
                break
            else:
                continue
    return result


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
