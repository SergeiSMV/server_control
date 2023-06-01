import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor


@router.route('/sim_nm_names')
async def sim_nm_names(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await _get_names(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def _get_names(data):
    category = data['category']
    names = []

    sql = 'SELECT name FROM nomenclature  WHERE category = %s GROUP BY name'
    val = (category,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, val)
    result = sim_cursor.fetchall()
    sim_connect.commit()

    for n in result:
        names.append(n['name'])

    return names


