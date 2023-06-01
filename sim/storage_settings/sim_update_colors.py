import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.sql_functions.get_producer_id import get_producer_id
from sim.sql_functions.get_unit_id import get_unit_id


@router.route('/sim_update_colors')
async def sim_update_colors(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_update_colors(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_update_colors(data):
    item_id = data['id']
    color = data['color']

    updt = 'UPDATE colors SET color = %s WHERE id = %s'
    updtValue = (color, item_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(updt, updtValue)
    sim_connect.commit()

    return 'done'
