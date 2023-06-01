import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.history.sim_create_history import sim_create_history
from sim.item_edit.sim_delete_item import f_sim_delete_item
from sim.orders.sim_all_orders import f_sim_all_orders
from sim.orders.sim_order_items import f_sim_order_items
from sim.orders.sim_uniq_items import f_sim_uniq_items
from sim.sim_all_items import f_sim_all_items
from sim.sql_functions.get_place_values import get_place_values


@router.route('/sim_accept_extradition')
async def sim_accept_extradition(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_accept_extradition(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_accept_extradition(data):
    item_id = data['data']['item_id']
    order_id = data['data']['order_id']
    num = data['data']['num']
    fact_quantity = data['data']['fact_quant']
    unit = data['data']['unit']
    reserve_quantity = data['data']['quantity']
    author = data['author']

    edit_order = 'UPDATE orders SET status = 3 WHERE id = %s'
    order_value = (order_id, )
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(edit_order, order_value)
    sim_connect.commit()

    edit_sim = 'UPDATE items SET quant = quant - %s, reserve = reserve - %s WHERE id = %s'
    sim_value = (fact_quantity, reserve_quantity, item_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(edit_sim, sim_value)
    sim_connect.commit()

    # запись в историю
    comment = f'по заявке {num}, в количестве {fact_quantity}{unit}.\nпринял:'
    await sim_create_history(item_id, 'выдача ТМЦ', comment, author)

    # контроль остатка в базе
    get_remainder = 'SELECT place, quant, pallet_size FROM items WHERE id = %s'
    get_value = (item_id, )
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(get_remainder, get_value)
    remainder = sim_cursor.fetchone()
    sim_connect.commit()

    quantity = remainder['quant']
    pallet_size = remainder['pallet_size']
    place_id = remainder['place']

    # если остаток равен нулю удаляем позицию из базы
    if int(quantity) <= 0:
        place_info = await get_place_values(place_id)
        place = place_info['place']
        cell = place_info['cell']
        delete_item_data = {'itemId': item_id, 'pallet_size': pallet_size, 'place': place, 'cell': cell}
        await f_sim_delete_item(delete_item_data)
        await f_sim_all_items(broadcast=True)
    else:
        await f_sim_all_items(broadcast=True)

    await f_sim_all_orders(broadcast=True)
    await f_sim_order_items(num, broadcast=True)
    await f_sim_uniq_items(broadcast=True)

    return 'done'
