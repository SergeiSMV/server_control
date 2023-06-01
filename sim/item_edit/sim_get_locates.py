import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor


@router.route('/sim_get_locates')
async def sim_get_locates(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_get_locates(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_get_locates(data):
    placeList = []
    data = {}

    sql = 'SELECT place FROM places GROUP BY place'
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, )
    places = sim_cursor.fetchall()
    sim_connect.commit()

    for pl in places:
        name = pl['place']
        placeList.append(name)
    data['locate'] = placeList

    for cl in placeList:
        sql2 = 'SELECT cell FROM places WHERE place = %s AND status = "empty"'
        val2 = (cl,)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(sql2, val2)
        result = sim_cursor.fetchall()
        sim_connect.commit()
        data[f'{cl}'] = []
        for cell in result:
            data[f'{cl}'].append(cell['cell'])

    return data
