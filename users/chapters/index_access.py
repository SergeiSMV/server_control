import ast
import json
import websockets
from connections import users_connect, users_cursor
from router_init import router


@router.route('/index_access')
async def index_access(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await sql_index_access(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def sql_index_access(data):
    chapters = []
    user_access = []
    user_id = data['user_id']

    sql = 'SELECT * FROM chapters'
    users_connect.ping(reconnect=True)
    users_cursor.execute(sql, )
    all_chapters = users_cursor.fetchall()
    users_connect.commit()

    for ch in all_chapters:
        chapters.append(ch['chapter'])

    sql2 = 'SELECT chapter FROM chapters_access WHERE user_id = %s'
    val2 = (user_id,)
    users_cursor.execute(sql2, val2)
    user_chapters = users_cursor.fetchall()
    users_connect.commit()

    for user_ch in user_chapters:
        user_access.append(user_ch['chapter'])

    # проверяем пустой ли список доступов у пользователя
    if user_access:
        for check in all_chapters:
            ch = check['chapter']
            if ch in user_access:
                continue
            else:
                department = check['department']
                depence = check['depence']
                description = check['description']
                sql_add = 'INSERT INTO chapters_access (user_id, chapter, department, depence, description, access) VALUES (%s, %s, %s, %s, %s, %s)'
                val_add = (user_id, ch, department, depence, description, 0)
                users_connect.ping(reconnect=True)
                users_cursor.execute(sql_add, val_add)
                users_cursor.fetchall()
                users_connect.commit()
                continue
    else:
        for add in all_chapters:
            chapter = add['chapter']
            department = add['department']
            depence = add['depence']
            description = add['description']

            sql3 = 'INSERT INTO chapters_access (user_id, chapter, department, depence, description, access) VALUES (%s, %s, %s, %s, %s, %s)'
            val3 = (user_id, chapter, department, depence, description, 0)
            users_connect.ping(reconnect=True)
            users_cursor.execute(sql3, val3)
            users_cursor.fetchall()
            users_connect.commit()
            continue

    return 'done'
