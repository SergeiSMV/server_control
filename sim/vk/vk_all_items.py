import ast
import json
import websockets
from connections import sim_connect, sim_cursor
from router_init import router

CLIENTS_SIM = {}


@router.route('/vk_all_items')
async def vk_all_items(ws, path):
    global CLIENTS_SIM
    user_id = 0
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                user_id = client_data['user_id']
                CLIENTS_SIM[user_id] = ws
                result = await f_vk_all_items()
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                await delClient(user_id)
                break
    except websockets.ConnectionClosedError:
        await delClient(user_id)


async def f_vk_all_items(broadcast=False):
    allVkItemsList = []

    sql = 'SELECT * FROM vk_items'
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, )
    result = sim_cursor.fetchall()
    sim_connect.commit()

    for items in result:
        item_data = ast.literal_eval(items['data'])
        item_data['itemId'] = items['id']
        item_data['document'] = items['document']
        item_data['status'] = items['status']
        allVkItemsList.append(item_data)

    if broadcast:
        for ws in CLIENTS_SIM:
            await CLIENTS_SIM[ws].send(json.dumps(allVkItemsList))
    else:
        return allVkItemsList


async def delClient(user_id):
    try:
        del CLIENTS_SIM[user_id]
    except KeyError:
        pass
