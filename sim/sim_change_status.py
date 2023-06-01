import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.history.sim_create_history import sim_create_history

from sim.sim_all_items import f_sim_all_items


@router.route('/sim_change_status')
async def sim_change_status(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_change_status(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_change_status(data):
    item_id = data['itemId']
    author = data['author']
    status = data['status']
    comment = data['comment']
    action = f'движение приостановлено' if status == 'stop' else 'движение возобновлено'

    # запись в историю
    await sim_create_history(item_id, action, comment, author)

    sql = 'UPDATE items SET status = %s WHERE id = %s'
    val = (status, item_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, val)
    sim_cursor.fetchall()
    sim_connect.commit()

    await f_sim_all_items(broadcast=True)
    return 'done'
