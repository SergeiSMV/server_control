import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.sql_functions.get_producer_id import get_producer_id


@router.route('/sim_nm_boxsize')
async def sim_nm_boxsize(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await _get_boxsize(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def _get_boxsize(data):
    category = data['category']
    name = data['name']
    producer = data['producer']
    producer_id = await get_producer_id(producer)

    sql = 'SELECT * FROM nomenclature  WHERE category = %s AND name = %s AND producer = %s'
    val = (category, name, producer_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, val)
    boxsize = sim_cursor.fetchone()
    sim_connect.commit()

    return boxsize
