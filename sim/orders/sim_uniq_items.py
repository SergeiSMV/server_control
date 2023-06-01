import ast
import json
import websockets
from connections import sim_connect, sim_cursor
from router_init import router
from sim.sql_functions.get_color_values import get_color_values
from sim.sql_functions.get_name_values import get_name_values
from sim.sql_functions.get_producer_values import get_producer_values
from sim.sql_functions.get_unit_values import get_unit_values

CLIENTS_SIM = {}


@router.route('/sim_uniq_items')
async def sim_uniq_items(ws, path):
    global CLIENTS_SIM
    user_id = 0
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                user_id = client_data['user_id']
                CLIENTS_SIM[user_id] = ws
                result = await f_sim_uniq_items()
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                await del_client(user_id)
                break
    except websockets.ConnectionClosedError:
        await del_client(user_id)


async def f_sim_uniq_items(broadcast=False):
    uniq_sim_items = []

    sql = 'SELECT name, color, SUM(quant - reserve) AS quant FROM items WHERE status = %s' \
          'GROUP BY name, color'
    val = ('work',)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, val)
    result = sim_cursor.fetchall()
    sim_connect.commit()

    for items in result:
        item_id = items['name']

        nomenclature = 'SELECT * FROM nomenclature WHERE id =%s'
        nomenclature_val = (item_id,)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(nomenclature, nomenclature_val)
        item_info = sim_cursor.fetchone()
        sim_connect.commit()

        category = item_info['category']
        name = item_info['name']
        color = '' if items['color'] == 0 else await get_color_values(items['color'])
        producer = await get_producer_values(item_info['producer'])
        quantity = int(items['quant'])
        unit = await get_unit_values(item_info['unit'])

        items_map = {
            'category': category,
            'name': name,
            'color': color,
            'producer': producer,
            'quantity': quantity,
            'unit': unit,
        }
        if quantity <= 0:
            continue
        else:
            uniq_sim_items.append(items_map)

    if broadcast:
        for ws in CLIENTS_SIM:
            await CLIENTS_SIM[ws].send(json.dumps(uniq_sim_items))
    else:
        return uniq_sim_items


async def del_client(user_id):
    try:
        del CLIENTS_SIM[user_id]
    except KeyError:
        pass
