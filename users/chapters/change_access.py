import ast
import json
import websockets
from connections import users_connect, users_cursor
from router_init import router
from users.chapters.chapter_access import CLIENTS_ACCESS, get_chapter_access


@router.route('/change_access')
async def change_access(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await sql_change_access(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def sql_change_access(data):
    client_status = data['status']
    client_data = {}
    client_id = data['data'][0]['user_id']
    client_data['user_id'] = client_id

    for update in data['data']:
        string_id = update['id']
        access_value = update['access']
        sql = 'UPDATE page_access SET access = %s WHERE id = %s'
        val = (access_value, string_id)
        users_connect.ping(reconnect=True)
        users_cursor.execute(sql, val)
        users_cursor.fetchall()
        users_connect.commit()

    sql1 = 'UPDATE users SET status = %s WHERE id = %s'
    val1 = (client_status, client_id)
    users_connect.ping(reconnect=True)
    users_cursor.execute(sql1, val1)
    users_cursor.fetchall()
    users_connect.commit()

    if str(client_id) in CLIENTS_SIM:
        client_result = await get_chapter_access(client_data)
        try:
            await CLIENTS_SIM[str(client_id)].send(json.dumps(client_result))
        except websockets.ConnectionClosed:
            pass

    return 'done'
