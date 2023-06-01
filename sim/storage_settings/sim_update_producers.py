import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.sql_functions.get_producer_id import get_producer_id
from sim.sql_functions.get_unit_id import get_unit_id


@router.route('/sim_update_producers')
async def sim_update_producers(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_update_producers(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_update_producers(data):
    item_id = data['id']
    producer = data['producer']

    updt = 'UPDATE producers SET producer = %s WHERE id = %s'
    updt_value = (producer, item_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(updt, updt_value)
    sim_connect.commit()

    return 'done'
