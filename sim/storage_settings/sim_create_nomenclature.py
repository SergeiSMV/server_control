import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.sql_functions.get_producer_id import get_producer_id
from sim.sql_functions.get_unit_id import get_unit_id


@router.route('/sim_create_nomenclature')
async def sim_create_nomenclature(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_create_nomenclature(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_create_nomenclature(data):
    category = data['category']
    name = data['name']
    producer = data['producer']
    producer_id = await get_producer_id(producer)
    unit = data['unit']
    unit_id = await get_unit_id(unit)

    box_size = data['box_size']
    box_quantity = data['box_quant']

    add_nomenclature = 'INSERT INTO nomenclature (' \
                       'category, name, producer, unit, box_size, box_quantity' \
                       ') VALUES (%s, %s, %s, %s, %s, %s)'
    nomenclature_value = (category, name, producer_id, unit_id, box_size, box_quantity)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(add_nomenclature, nomenclature_value)
    sim_cursor.fetchall()
    sim_connect.commit()

    return 'done'
