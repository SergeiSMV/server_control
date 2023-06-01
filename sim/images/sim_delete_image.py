import ast
import json
import websockets
from router_init import router
import os

from sim.sim_all_items import f_sim_all_items


@router.route('/sim_delete_image')
async def sim_delete_image(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_delete_image(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_delete_image(data):
    item = data['item']
    image_link = data['link']
    category = item['category']
    name = item['name']
    producer = item['producer']
    color = item['color']

    link = image_link.replace('https://backraz.ru', '/usr/local/bin')
    directory1 = f'/usr/local/bin/images/{category}/{name}/{producer}/{color}'
    directory2 = f'/usr/local/bin/images/{category}/{name}/{producer}'
    directory3 = f'/usr/local/bin/images/{category}/{name}'
    directory4 = f'/usr/local/bin/images/{category}'
    directory5 = f'/usr/local/bin/images'
    try:
        os.remove(link)
    except FileNotFoundError:
        pass

    try:
        os.rmdir(directory1) if len(os.listdir(directory1)) == 0 else None
    except FileNotFoundError:
        pass

    try:
        os.rmdir(directory2) if len(os.listdir(directory2)) == 0 else None
    except FileNotFoundError:
        pass

    try:
        os.rmdir(directory3) if len(os.listdir(directory3)) == 0 else None
    except FileNotFoundError:
        pass

    try:
        os.rmdir(directory4) if len(os.listdir(directory4)) == 0 else None
    except FileNotFoundError:
        pass

    try:
        os.rmdir(directory5) if len(os.listdir(directory5)) == 0 else None
    except FileNotFoundError:
        pass

    await f_sim_all_items(broadcast=True)
    return 'done'
