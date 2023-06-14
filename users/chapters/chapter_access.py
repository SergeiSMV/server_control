import ast
import json
import websockets
from connections import users_connect, users_cursor
from router_init import router

CLIENTS_ACCESS = {}


@router.route('/chapter_access')
async def chapter_access(ws, path):
    global CLIENTS_SIM
    user_id = 0
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                user_id = client_data['user_id']
                CLIENTS_ACCESS[user_id] = ws
                result = await get_chapter_access(client_data)
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                await del_client(user_id)
                break
    except websockets.ConnectionClosedError:
        await del_client(user_id)


async def get_chapter_access(data):
    chapters_list = []
    user_id = int(data['user_id'])

    sql = 'SELECT * FROM chapters_access WHERE user_id = %s AND access = 1'
    val = (user_id,)
    users_connect.ping(reconnect=True)
    users_cursor.execute(sql, val)
    result = users_cursor.fetchall()
    users_connect.commit()

    for pages in result:
        chapter = pages['chapter']
        department = pages['department']
        depence = pages['depence']
        description = pages['description']
        items_map = {
            'chapter': chapter,
            'department': department,
            'depence': depence,
            'description': description
        }
        chapters_list.append(items_map)

    return chapters_list


async def del_client(user_id):
    try:
        del CLIENTS_ACCESS[user_id]
    except KeyError:
        pass
