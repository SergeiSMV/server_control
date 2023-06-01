import ast
import json
from datetime import datetime

import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.history.sim_create_history import sim_create_history
from sim.sim_all_items import f_sim_all_items
from sim.sim_send_qrcode import sql_send_qr
from sim.sql_functions.get_color_id import get_color_id
from sim.sql_functions.get_nm_item_id import get_nm_item_id
from sim.sql_functions.get_place_id import get_place_id
from sim.sql_functions.get_producer_id import get_producer_id
from sim.sql_functions.get_unit_id import get_unit_id
from sim.vk.vk_all_items import f_vk_all_items


@router.route('/add_item')
async def add_item(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_add_item(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_add_item(data):
    category = data['category']
    name = data['name']
    producer = data['producer']
    color = data['color']
    barcode = data['barcode']
    unit = data['unit']
    box_size_string = data['box_size']
    box_quantity_string = data['box_quantity']
    base_box_size = data['base_box_size']
    place = data['place']
    pallet_size = data['pallet_size']
    author = data['author']

    producer_id = await get_producer_id(producer)
    unit_id = await get_unit_id(unit)
    nm_item_id = await get_nm_item_id(category, name, producer_id, unit_id)
    color_id = await get_color_id(color) if color != '' else 0

    # добавляем информацию о таре, если ее нет в базе
    if base_box_size == '0x0x0':
        update_place = 'UPDATE nomenclature SET box_size = %s, box_quantity = %s WHERE id = %s'
        update_value = (box_size_string, box_quantity_string, nm_item_id)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(update_place, update_value)
        sim_cursor.fetchall()
        sim_connect.commit()

    # добавляем штрих код, если его нет в базе
    if not barcode:
        pass
    else:
        barcodes = []
        check_barcode = 'SELECT * FROM barcodes'
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(check_barcode, )
        result = sim_cursor.fetchall()
        sim_connect.commit()

        for b in result:
            barcodes.append(b['barcode'])

        if barcode in barcodes:
            pass
        else:
            add_to_bc = 'INSERT INTO barcodes (barcode, name, color) VALUES (%s, %s, %s)'
            bc_value = (barcode, nm_item_id, color_id)
            sim_connect.ping(reconnect=True)
            sim_cursor.execute(add_to_bc, bc_value)
            sim_cursor.fetchall()
            sim_connect.commit()

    # распределение ТМЦ
    if not place:

        del data['barcode']
        del data['box_size']
        del data['box_quantity']
        del data['base_box_size']
        del data['base_box_quantity']
        del data['place']
        del data['cell']

        add_to_vk = 'INSERT INTO vk_items (data) VALUES (%s)'
        vk_value = (str(data),)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(add_to_vk, vk_value)
        sim_cursor.fetchall()
        sim_connect.commit()
        result = 'done'
        await f_vk_all_items(broadcast=True)

    else:
        # проверяем возможность размещения в указанную ячейку
        examination = await check_ability(data, pallet_size)
        if examination == 'allowed':
            # размещение в новую ячейку
            await place_big_pallet(data) if pallet_size == 'big' else await place_standart_pallet(data)

            # получаем последний добавленный id
            get_id = 'SELECT MAX(id) FROM items'
            sim_connect.ping(reconnect=True)
            sim_cursor.execute(get_id, )
            last_id = sim_cursor.fetchall()
            sim_connect.commit()

            # запись в историю
            comment = f'ручное внесение позиции'
            await sim_create_history(last_id[0]['MAX(id)'], 'поступление', comment, author)

            # отправка QR кода
            data['itemId'] = last_id[0]['MAX(id)']
            qr_data = {'data': data}
            await sql_send_qr(qr_data)

            await f_sim_all_items(broadcast=True)
            result = 'done'
        else:
            result = 'невозможно разместить паллет в указанную ячейку'

    return result

# ручное размещение большого паллета
async def place_big_pallet(data):
    category = data['category']
    name = data['name']
    color = data['color']
    producer = data['producer']
    quantity = data['quantity']
    unit = data['unit']
    place = data['place']
    cell = data['cell']
    string_date = data['fifo']
    fifo = datetime.strptime(string_date, '%d.%m.%Y')
    author = data['author']
    pallet_size = data['pallet_size']

    producer_id = await get_producer_id(producer)
    unit_id = await get_unit_id(unit)
    nm_item_id = await get_nm_item_id(category, name, producer_id, unit_id)
    color_id = await get_color_id(color) if color != '' else 0

    # обновляем статус в размещаемой ячейке
    status_new_cell = 'UPDATE places SET status = %s WHERE place = %s AND cell = %s'
    new_cell_change_value = ('busy', place, cell)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(status_new_cell, new_cell_change_value)
    sim_cursor.fetchall()
    sim_connect.commit()

    # получаем секцию новой ячейки
    current_cell = 'SELECT section FROM places WHERE place = %s AND cell = %s'
    current_cell_value = (place, cell)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(current_cell, current_cell_value)
    section = sim_cursor.fetchone()['section']
    sim_connect.commit()

    # получаем все ячейки в секции
    get_section_cells = 'SELECT * FROM places WHERE place = %s AND section = %s'
    section_cells_value = (place, section)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(get_section_cells, section_cells_value)
    section_cells = sim_cursor.fetchall()
    sim_connect.commit()

    # индекс текущей ячейки
    current_cell_index = next((index for (index, d) in enumerate(section_cells) if d["cell"] == cell), None)
    # длина секции
    section_cells_length = len(section_cells)

    # текущая ячейка последняя в секции
    current_cell_is_last = current_cell_index == section_cells_length - 1
    # индекс занимаемой большим паллетом ячейки
    target_cell_index = current_cell_index - 1 if current_cell_is_last else current_cell_index + 1

    target_cell_id = section_cells[target_cell_index]['id']
    target_cell_status = section_cells[target_cell_index]['status']

    if section_cells_length > 2:
        new_target_cell_status = 'used' if target_cell_status == 'empty' else 'lock'
    else:
        new_target_cell_status = 'lock'

    # обновляем статус занимаемой большим паллетом ячейки
    status_target_cell = 'UPDATE places SET status = %s WHERE id = %s'
    target_cell_change_value = (new_target_cell_status, target_cell_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(status_target_cell, target_cell_change_value)
    sim_cursor.fetchall()
    sim_connect.commit()

    new_cell_id = section_cells[current_cell_index]['id']

    # добавляем паллет в базу СиМ
    add_to_sim = 'INSERT INTO items (place, name, color, quant, fifo, author, status, pallet_size) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
    sim_value = (new_cell_id, nm_item_id, color_id, quantity, fifo, author, 'work', pallet_size)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(add_to_sim, sim_value)
    sim_cursor.fetchall()
    sim_connect.commit()

# ручное размещение стандартного паллета
async def place_standart_pallet(data):
    category = data['category']
    name = data['name']
    color = data['color']
    producer = data['producer']
    quantity = data['quantity']
    unit = data['unit']
    place = data['place']
    cell = data['cell']
    string_date = data['fifo']
    fifo = datetime.strptime(string_date, '%d.%m.%Y')
    author = data['author']
    pallet_size = data['pallet_size']

    producer_id = await get_producer_id(producer)
    unit_id = await get_unit_id(unit)
    nm_item_id = await get_nm_item_id(category, name, producer_id, unit_id)
    color_id = await get_color_id(color) if color != '' else 0

    # обновляем статус в размещаемой ячейке
    status_new_cell = 'UPDATE places SET status = %s WHERE place = %s AND cell = %s'
    new_cell_change_value = ('busy', place, cell)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(status_new_cell, new_cell_change_value)
    sim_cursor.fetchall()
    sim_connect.commit()

    new_cell_id = await get_place_id(place, cell)

    # добавляем паллет в базу СиМ
    add_to_sim = 'INSERT INTO items (place, name, color, quant, fifo, author, status, pallet_size) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
    sim_value = (new_cell_id, nm_item_id, color_id, quantity, fifo, author, 'work', pallet_size)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(add_to_sim, sim_value)
    sim_cursor.fetchall()
    sim_connect.commit()

# проверяем возможность размещения в указанную ячейку
async def check_ability(data, final_pallet_size):
    place = data['place']
    cell = data['cell']

    if final_pallet_size == 'big':
        # получаем секцию новой ячейки
        current_cell = 'SELECT section FROM places WHERE place = %s AND cell = %s'
        current_cell_value = (place, cell)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(current_cell, current_cell_value)
        section = sim_cursor.fetchone()['section']
        sim_connect.commit()

        # получаем все ячейки в секции
        get_section_cells = 'SELECT * FROM places WHERE place = %s AND section = %s'
        section_cells_value = (place, section)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(get_section_cells, section_cells_value)
        section_cells = sim_cursor.fetchall()
        sim_connect.commit()

        # индекс текущей ячейки
        current_cell_index = next((index for (index, d) in enumerate(section_cells) if d["cell"] == cell), None)
        # длина секции
        section_cells_length = len(section_cells)

        # текущая ячейка последняя в секции
        current_cell_is_last = current_cell_index == section_cells_length - 1
        # текущая ячейка первая в секции
        current_cell_is_first = current_cell_index == 0

        if current_cell_is_last:
            target_cell_index = current_cell_index - 1
            target_cell_status = section_cells[target_cell_index]['status']

            result = 'allowed' if target_cell_status == 'empty' or target_cell_status == 'used' else 'forbidden'

        elif current_cell_is_first:
            target_cell_index = current_cell_index + 1
            target_cell_status = section_cells[target_cell_index]['status']

            result = 'allowed' if target_cell_status == 'empty' or 'used' else 'forbidden'

        else:
            result = 'forbidden'

    else:
        result = 'allowed'

    return result
