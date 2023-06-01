import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.sql_functions.get_producer_id import get_producer_id
from sim.sql_functions.get_unit_id import get_unit_id


@router.route('/sim_create_colors')
async def sim_create_colors(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_create_colors(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_create_colors(data):
    color = data['color']

    add_nomenclature = 'INSERT INTO colors (color) VALUES (%s)'
    nomenclature_value = (color, )
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(add_nomenclature, nomenclature_value)
    sim_cursor.fetchall()
    sim_connect.commit()

    return 'done'
