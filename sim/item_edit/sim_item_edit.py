import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.history.sim_create_history import sim_create_history
from sim.sim_all_items import f_sim_all_items
from sim.sql_functions.get_color_id import get_color_id
from sim.sql_functions.get_nm_item_id import get_nm_item_id
from sim.sql_functions.get_producer_id import get_producer_id
from sim.sql_functions.get_unit_id import get_unit_id


@router.route('/sim_item_edit')
async def sim_item_edit(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_item_edit(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_item_edit(data):
    item_id = data['itemId']
    default = data['default']
    category = data['category']
    name = data['name']
    color = data['color']
    producer = data['producer']
    quantity = data['quantity']
    unit = data['unit']
    author = data['author']

    comment = f"до: {default['category']} {default['name']} {default['color']}, {default['producer']}, " \
              f"{default['quantity']} {default['unit']}\n" \
              f"после: {category} {name} {color}, {producer}, {quantity} {unit}"
    # запись в историю
    await sim_create_history(item_id, 'редактирование', comment, author)

    producer_id = await get_producer_id(producer)
    unit_id = await get_unit_id(unit)
    name_id = await get_nm_item_id(category, name, producer_id, unit_id)
    color_id = 0 if color == '' else await get_color_id(color)

    sql = 'UPDATE items SET name = %s, color = %s, quant = %s  WHERE id = %s'
    val = (name_id, color_id, quantity, item_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, val)
    sim_cursor.fetchall()
    sim_connect.commit()

    await f_sim_all_items(broadcast=True)
    return 'done'
