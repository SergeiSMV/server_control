import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.orders.sim_all_orders import f_sim_all_orders
from sim.orders.sim_order_items import f_sim_order_items


@router.route('/sim_item_extradition')
async def sim_item_extradition(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_item_extradition(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_item_extradition(data):
    order_id = data['order_id']
    fact_quantity = data['factQuantity']
    num = data['num']

    sql = 'UPDATE orders SET fact_quant = %s, status = %s WHERE id = %s'
    val = (fact_quantity, 2, order_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, val)
    sim_connect.commit()

    await f_sim_all_orders(broadcast=True)
    await f_sim_order_items(num, broadcast=True)

    return 'done'
