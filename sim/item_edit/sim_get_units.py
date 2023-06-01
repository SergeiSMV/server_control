import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor


@router.route('/sim_get_units')
async def sim_get_units(ws, path):
    try:
        try:
            result = await f_sim_get_units()
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_get_units():
    units = []

    sql = 'SELECT * FROM units'
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, )
    result = sim_cursor.fetchall()
    sim_connect.commit()

    for u in result:
        units.append(u['unit'])

    return units
