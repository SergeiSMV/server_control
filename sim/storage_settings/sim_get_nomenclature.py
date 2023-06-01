import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.sql_functions.get_producer_values import get_producer_values
from sim.sql_functions.get_unit_values import get_unit_values


@router.route('/sim_get_nomenclature')
async def sim_get_nomenclature(ws, path):
    try:
        try:
            result = await f_sim_get_nomenclature()
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_get_nomenclature():
    nomenclature = []

    sql = 'SELECT * FROM nomenclature'
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, )
    result = sim_cursor.fetchall()
    sim_connect.commit()

    for n in result:
        producer_id = n['producer']
        unit_id = n['unit']
        producer = await get_producer_values(producer_id)
        unit = await get_unit_values(unit_id)
        n['producer'] = producer
        n['unit'] = unit
        nomenclature.append(n)

    return nomenclature
