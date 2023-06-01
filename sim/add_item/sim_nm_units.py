import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.sql_functions.get_producer_id import get_producer_id
from sim.sql_functions.get_unit_values import get_unit_values


@router.route('/sim_nm_units')
async def sim_nm_units(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await _get_units(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def _get_units(data):
    category = data['category']
    name = data['name']
    producer = data['producer']
    producer_id = await get_producer_id(producer)
    units = []

    sql = 'SELECT unit FROM nomenclature  WHERE category = %s AND name = %s AND producer = %s GROUP BY unit'
    val = (category, name, producer_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, val)
    result = sim_cursor.fetchall()
    sim_connect.commit()

    for n in result:
        unit = await get_unit_values(n['unit'])
        units.append(unit)

    return units
