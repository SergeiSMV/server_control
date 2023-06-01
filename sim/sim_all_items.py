import ast
import json
import websockets
from connections import sim_connect, sim_cursor
from router_init import router
import os

from sim.sql_functions.get_color_values import get_color_values
from sim.sql_functions.get_nm_item_values import get_nm_item_values
from sim.sql_functions.get_place_values import get_place_values

CLIENTS_SIM = {}


@router.route('/sim_all_items')
async def sim_all_items(ws, path):
    global CLIENTS_SIM
    user_id = 0
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                user_id = client_data['user_id']
                CLIENTS_SIM[user_id] = ws
                result = await f_sim_all_items()
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                await delClient(user_id)
                break
    except websockets.ConnectionClosedError:
        await delClient(user_id)


async def f_sim_all_items(broadcast=False):
    allSimItemsList = []

    sql = 'SELECT * FROM items'
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, )
    result = sim_cursor.fetchall()
    sim_connect.commit()

    for items in result:

        place_values = await get_place_values(items['place'])
        name_values = await get_nm_item_values(items['name'])

        itemId = items['id']
        place = place_values['place']
        cell = place_values['cell']
        category = name_values['category']
        name = name_values['name']
        color = '' if items['color'] == 0 else await get_color_values(items['color'])
        producer = name_values['producer']
        quantity = items['quant']
        reserve = items['reserve']
        unit = name_values['unit']
        fifo = items['fifo'].strftime('%d.%m.%Y')
        author = items['author']
        status = items['status']
        size = items['pallet_size']
        comment = items['comment'].split(']')

        imageLinks = []

        try:
            if os.listdir(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}'):
                for file in os.listdir(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}'):
                    imageLinks.append(f'https://backraz.ru/images/{category}/{name}/{producer}/{color}/{file}')
            else:
                pass
        except FileNotFoundError:
            pass

        items_map = {
            'itemId': itemId, 'place': place, 'cell': cell, 'category': category,
            'name': name, 'color': color, 'producer': producer, 'quantity': quantity,
            'reserve': reserve, 'unit': unit, 'fifo': fifo, 'author': author,
            'status': status, 'comment': comment, 'pallet_size': size, 'images': imageLinks
        }
        allSimItemsList.append(items_map)

    if broadcast:
        for ws in CLIENTS_SIM:
            await CLIENTS_SIM[ws].send(json.dumps(allSimItemsList))
    else:
        return allSimItemsList


async def delClient(user_id):
    try:
        del CLIENTS_SIM[user_id]
    except KeyError:
        pass
