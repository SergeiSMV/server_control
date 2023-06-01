import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.sim_all_items import f_sim_all_items


@router.route('/sim_delete_item')
async def sim_delete_item(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_delete_item(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_delete_item(data):
    item_id = data['itemId']
    pallet_size = data['pallet_size']

    await clear_cell_standart(data) if pallet_size == 'standart' else await clear_cell_big(data)

    sql = 'DELETE FROM items WHERE id = %s'
    val = (item_id,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, val)
    sim_cursor.fetchall()
    sim_connect.commit()

    sql = 'DELETE FROM history WHERE item_id = %s'
    val = (item_id,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, val)
    sim_cursor.fetchall()
    sim_connect.commit()

    await f_sim_all_items(broadcast=True)
    return 'done'


async def clear_cell_standart(data):
    place = data['place']
    cell = data['cell']

    # меняем статус ячейки на empty
    status_cell = 'UPDATE places SET status = %s WHERE place = %s AND cell = %s'
    status_value = ('empty', place, cell)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(status_cell, status_value)
    sim_cursor.fetchall()
    sim_connect.commit()


async def clear_cell_big(data):
    place = data['place']
    cell = data['cell']

    # меняем статус текущей ячейки на empty
    status_current_cell = 'UPDATE places SET status = %s WHERE place = %s AND cell = %s'
    current_cell_change_value = ('empty', place, cell)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(status_current_cell, current_cell_change_value)
    sim_cursor.fetchall()
    sim_connect.commit()

    # получаем секцию текущей ячейки
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
