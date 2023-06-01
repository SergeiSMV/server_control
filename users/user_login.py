import ast
import json
import websockets
from connections import users_connect, users_cursor
from router_init import router


@router.route('/login')
async def user_login(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await sql_login(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def sql_login(data):
    log = data['login']
    password = data['password']
    sql = 'SELECT count(*) FROM users WHERE login = %s AND password = %s'
    val = (log, password)
    users_connect.ping(reconnect=True)
    users_cursor.execute(sql, val)
    result = users_cursor.fetchall()
    users_connect.commit()
    return result[0]['count(*)']
