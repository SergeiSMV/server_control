import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.history.sim_create_history import sim_create_history

from sim.sim_all_items import f_sim_all_items


@router.route('/sim_item_move')
async def sim_item_move(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_item_move(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_item_move(data):
    item_id = data['itemId']
    new_place = data['storage']
    new_cell = data['cell']
    old_place = data['old_storage']
    old_cell = data['old_cell']
    author = data['author']
    pallet_size = data['pallet_size']
    change = data['change_pallet']

    comment = f'из: {old_place}: {old_cell}\nна: {new_place}: {new_cell}'

    # запись в историю
    await sim_create_history(item_id, 'перемещение', comment, author)

    if change == 'yes':
        final_pallet_size = 'big' if pallet_size == 'standart' else 'standart'
    else:
        final_pallet_size = pallet_size

    # проверяем возможность размещения в указанную ячейку
    examination = await check_ability(data, final_pallet_size)

    if examination == 'allowed':
        # очистка текущей ячейки
        await clear_current_cell_big(data) if pallet_size == 'big' else await clear_current_cell_standart(data)

        # размещение в новую ячейку
        await replace_big_pallet(data, final_pallet_size) if final_pallet_size == 'big' \
            else await replace_standart_pallet(data, final_pallet_size)
        await f_sim_all_items(broadcast=True)

        result = 'done'

    else:
        result = 'невозможно разместить паллет в указанную ячейку'

    return result


# очистка текущей ячейки если большой паллет
async def clear_current_cell_big(data):
    old_place = data['old_storage']
    old_cell = data['old_cell']

    # меняем статус текущей ячейки на empty
    status_current_cell = 'UPDATE places SET status = %s WHERE place = %s AND cell = %s'
    current_cell_change_value = ('empty', old_place, old_cell)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(status_current_cell, current_cell_change_value)
    sim_cursor.fetchall()
    sim_connect.commit()

    # получаем секцию текущей ячейки
    current_cell = 'SELECT section FROM places WHERE place = %s AND cell = %s'
    current_cell_value = (old_place, old_cell)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(current_cell, current_cell_value)
    section = sim_cursor.fetchone()['section']
    sim_connect.commit()

    # получаем все ячейки в секции
    get_section_cells = 'SELECT * FROM places WHERE place = %s AND section = %s'
    section_cells_value = (old_place, section)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(get_section_cells, section_cells_value)
    section_cells = sim_cursor.fetchall()
    sim_connect.commit()

    # индекс текущей ячейки
    current_cell_index = next((index for (index, d) in enumerate(section_cells) if d["cell"] == old_cell), None)
    # длина секции
    section_cells_length = len(section_cells)

    # текущая ячейка последняя в секции
    current_cell_is_last = current_cell_index == section_cells_length - 1
    # индекс занимаемой большим паллетом ячейки
    target_cell_index = current_cell_index - 1 if current_cell_is_last else current_cell_index + 1

    target_cell_id = section_cells[target_cell_index]['id']
    target_cell_status = section_cells[target_cell_index]['status']
    # new_target_cell_status = 'empty' if target_cell_status == 'used' else 'used'

    if section_cells_length > 2:
        new_target_cell_status = 'empty' if target_cell_status == 'used' else 'used'
    else:
        new_target_cell_status = 'empty'

    # обновляем статус занимаемой большим паллетом ячейки
    status_target_cell = 'UPDATE places SET status = %s WHERE id = %s'
    target_cell_change_value = (new_target_cell_status, target_cell_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(status_target_cell, target_cell_change_value)
    sim_cursor.fetchall()
    sim_connect.commit()


# очистка текущей ячейки если стандартный паллет
async def clear_current_cell_standart(data):
    old_place = data['old_storage']
    old_cell = data['old_cell']

    clear_current_cell = 'UPDATE places SET status = %s WHERE place = %s AND cell = %s'
    clear_value = ('empty', old_place, old_cell)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(clear_current_cell, clear_value)
    sim_cursor.fetchall()
    sim_connect.commit()


# размещение большого паллета
async def replace_big_pallet(data, final_pallet_size):
    new_place = data['storage']
    new_cell = data['cell']
    item_id = data['itemId']

    # обновляем статус в размещаемой ячейке
    status_new_cell = 'UPDATE places SET status = %s WHERE place = %s AND cell = %s'
    new_cell_change_value = ('busy', new_place, new_cell)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(status_new_cell, new_cell_change_value)
    sim_cursor.fetchall()
    sim_connect.commit()

    # получаем секцию новой ячейки
    current_cell = 'SELECT section FROM places WHERE place = %s AND cell = %s'
    current_cell_value = (new_place, new_cell)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(current_cell, current_cell_value)
    section = sim_cursor.fetchone()['section']
    sim_connect.commit()

    # получаем все ячейки в секции
    get_section_cells = 'SELECT * FROM places WHERE place = %s AND section = %s'
    section_cells_value = (new_place, section)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(get_section_cells, section_cells_value)
    section_cells = sim_cursor.fetchall()
    sim_connect.commit()

    # индекс текущей ячейки
    current_cell_index = next((index for (index, d) in enumerate(section_cells) if d["cell"] == new_cell), None)
    # длина секции
    section_cells_length = len(section_cells)

    # текущая ячейка последняя в секции
    current_cell_is_last = current_cell_index == section_cells_length - 1
    # индекс занимаемой большим паллетом ячейки
    target_cell_index = current_cell_index - 1 if current_cell_is_last else current_cell_index + 1

    target_cell_id = section_cells[target_cell_index]['id']
    target_cell_status = section_cells[target_cell_index]['status']
    # new_target_cell_status = 'used' if target_cell_status == 'empty' else 'lock'

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

    # обновляем место размещения в общей базе ТМЦ
    update_place = 'UPDATE items SET place = %s, pallet_size = %s WHERE id = %s'
    update_value = (new_cell_id, final_pallet_size, item_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(update_place, update_value)
    sim_cursor.fetchall()
    sim_connect.commit()


# размещение стандартного паллета
async def replace_standart_pallet(data, final_pallet_size):
    new_place = data['storage']
    new_cell = data['cell']
    item_id = data['itemId']

    # получаем id новой ячейки
    current_cell = 'SELECT id FROM places WHERE place = %s AND cell = %s'
    current_cell_value = (new_place, new_cell)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(current_cell, current_cell_value)
    cell_id = sim_cursor.fetchone()['id']
    sim_connect.commit()

    # обновляем место размещения в общей базе ТМЦ
    update_place = 'UPDATE items SET place = %s, pallet_size = %s WHERE id = %s'
    update_value = (cell_id, final_pallet_size, item_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(update_place, update_value)
    sim_cursor.fetchall()
    sim_connect.commit()

    # обновляем статус в размещаемой ячейке
    status_new_cell = 'UPDATE places SET status = %s WHERE id = %s'
    new_cell_change_value = ('busy', cell_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(status_new_cell, new_cell_change_value)
    sim_cursor.fetchall()
    sim_connect.commit()

async def check_ability(data, final_pallet_size):
    new_place = data['storage']
    new_cell = data['cell']

    if final_pallet_size == 'big':
        # получаем секцию новой ячейки
        current_cell = 'SELECT section FROM places WHERE place = %s AND cell = %s'
        current_cell_value = (new_place, new_cell)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(current_cell, current_cell_value)
        section = sim_cursor.fetchone()['section']
        sim_connect.commit()

        # получаем все ячейки в секции
        get_section_cells = 'SELECT * FROM places WHERE place = %s AND section = %s'
        section_cells_value = (new_place, section)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(get_section_cells, section_cells_value)
        section_cells = sim_cursor.fetchall()
        sim_connect.commit()

        # индекс текущей ячейки
        current_cell_index = next((index for (index, d) in enumerate(section_cells) if d["cell"] == new_cell), None)
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

