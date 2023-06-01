import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.sql_functions.get_producer_values import get_producer_values


@router.route('/sim_nm_producers')
async def sim_nm_producers(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await _get_producers(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def _get_producers(data):
    category = data['category']
    name = data['name']
    producers = []

    sql = 'SELECT producer FROM nomenclature  WHERE category = %s AND name = %s GROUP BY producer'
    val = (category, name)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, val)
    result = sim_cursor.fetchall()
    sim_connect.commit()

    for n in result:
        producer = await get_producer_values(n['producer'])
        producers.append(producer)

    return producers


