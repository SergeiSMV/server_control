import ast
import json
import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.sql_functions.get_producer_id import get_producer_id
from sim.sql_functions.get_unit_id import get_unit_id


@router.route('/sim_update_nomenclature')
async def sim_update_nomenclature(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_update_nomenclature(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_update_nomenclature(data):
    item_id = data['id']
    category = data['category']
    name = data['name']
    producer = data['producer']
    producer_id = await get_producer_id(producer)
    box_size = data['box_size']
    box_quantity = data['box_quantity']
    unit = data['unit']
    unit_id = await get_unit_id(unit)

    updt = 'UPDATE nomenclature SET category = %s, name = %s, producer = %s, unit = %s, box_size = %s, box_quantity = %s WHERE id = %s'
    updt_value = (category, name, producer_id, unit_id, box_size, box_quantity, item_id)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(updt, updt_value)
    sim_connect.commit()

    return 'done'
