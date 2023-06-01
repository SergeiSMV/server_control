import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor


@router.route('/sim_get_producers')
async def sim_get_producers(ws, path):
    try:
        try:
            result = await f_sim_get_producers()
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_get_producers():
    producers = []

    sql = 'SELECT * FROM producers'
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, )
    result = sim_cursor.fetchall()
    sim_connect.commit()

    for p in result:
        producers.append(p['producer'])

    return producers
