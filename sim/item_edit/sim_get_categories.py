import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor


@router.route('/sim_get_categories')
async def sim_get_categories(ws, path):
    try:
        try:
            result = await f_sim_get_categories()
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_get_categories():
    categories = []

    sql = 'SELECT category FROM nomenclature GROUP BY category'
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, )
    result = sim_cursor.fetchall()
    sim_connect.commit()

    for c in result:
        categories.append(c['category'])

    return categories
