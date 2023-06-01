import ast
import json
import websockets
from connections import users_connect, users_cursor
from router_init import router

@router.route('/user_info')
async def user_info(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await sql_user_info(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass

async def sql_user_info(data):
    login = data['login']
    password = data['password']

    sql = 'SELECT * FROM users WHERE login = %s AND password = %s'
    val = (login, password)
    users_cursor.execute(sql, val)
    user_data = users_cursor.fetchall()
    users_connect.commit()

    id_position = user_data[0]['position']
    id_department = user_data[0]['department']

    sql_position = 'SELECT position FROM positions WHERE id = %s AND department = %s'
    val_position = (id_position, id_department)
    users_cursor.execute(sql_position, val_position)
    user_position = users_cursor.fetchone()
    users_connect.commit()

    sql_department = 'SELECT description FROM chapters WHERE id = %s'
    val_department = (id_department, )
    users_cursor.execute(sql_department, val_department)
    user_department = users_cursor.fetchone()
    users_connect.commit()

    user_data[0]['department'] = user_department['description']
    user_data[0]['position'] = user_position['position']

    return user_data[0]
