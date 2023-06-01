import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor


@router.route('/sim_base_item_quantity')
async def sim_base_item_quantity(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_base_item_quantity(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_base_item_quantity(data):
    item_id = data['itemId']

    sql = 'SELECT quant FROM items WHERE id = %s'
    val = (item_id,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, val)
    result = sim_cursor.fetchone()
    sim_connect.commit()

    quantity = result['quant']

    return quantity
