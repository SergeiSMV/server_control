import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor


@router.route('/sim_nm_categories')
async def sim_nm_categories(ws, path):
    try:
        try:
            result = await _get_categories()
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def _get_categories():
    categories = []

    sql = 'SELECT category FROM nomenclature GROUP BY category'
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, )
    result = sim_cursor.fetchall()
    sim_connect.commit()

    for c in result:
        categories.append(c['category'])

    return categories
