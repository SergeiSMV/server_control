import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor


@router.route('/sim_get_history')
async def sim_get_history(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_get_history(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_get_history(data):
    item_id = data['itemId']
    history_list = []

    sql = 'SELECT * FROM history WHERE item_id = %s'
    val = (item_id,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, val)
    result = sim_cursor.fetchall()
    sim_connect.commit()

    for h in result:
        row_id = h['id']
        action = h['action']
        comment = h['comment']
        date = h['date'].strftime('%d.%m.%Y')
        author = h['author']

        history_map = {'id': row_id, 'action': action, 'comment': comment, 'date': date, 'author': author}
        history_list.append(history_map)

    return history_list
