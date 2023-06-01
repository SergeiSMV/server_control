import json
import websockets
from connections import users_connect, users_cursor
from router_init import router


@router.route('/get_all_users')
async def get_all_users(ws, path):
    try:
        try:
            result = await f_get_all_users()
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_get_all_users():
    all_users = []

    get_users = 'SELECT * FROM users'
    users_cursor.execute(get_users, )
    users_data = users_cursor.fetchall()
    users_connect.commit()

    for u in users_data:
        user_id = u['id']
        id_position = u['position']
        id_department = u['department']

        sql_position = 'SELECT position FROM positions WHERE id = %s AND department = %s'
        val_position = (id_position, id_department)
        users_cursor.execute(sql_position, val_position)
        user_position = users_cursor.fetchone()
        users_connect.commit()

        sql_department = 'SELECT description FROM chapters WHERE id = %s'
        val_department = (id_department,)
        users_cursor.execute(sql_department, val_department)
        user_department = users_cursor.fetchone()
        users_connect.commit()

        u['position'] = user_position['position']
        u['department'] = user_department['description']

        all_users.append(u)

    return all_users
