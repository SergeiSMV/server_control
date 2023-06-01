import ast
import json
import websockets
from router_init import router
import base64
import os

from sim.sim_all_items import f_sim_all_items


@router.route('/sim_add_image')
async def sim_add_image(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_add_image(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_add_image(data):
    itemData = data['item_data']
    category = itemData['category']
    name = itemData['name']
    producer = itemData['producer']
    color = itemData['color']
    files = []
    count = 1
    code = data['image']
    link = ''
    try:
        if os.listdir(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}'):
            for file in os.listdir(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}'):
                files.append(int(file.split('.')[0]))
            image_name = count + max(files)
            link = f'https://backraz.ru/images/{category}/{name}/{producer}/{color}/{image_name}.jpg'
            with open(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}/{image_name}.jpg', 'wb') as fh:
                fh.write(base64.b64decode(code))
            fh.close()
        else:
            image_name = count
            link = f'https://backraz.ru/images/{category}/{name}/{producer}/{color}/{image_name}.jpg'
            with open(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}/{image_name}.jpg', 'wb') as fh:
                fh.write(base64.b64decode(code))
            fh.close()
    except FileNotFoundError:
        os.makedirs(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}')
        image_name = count
        link = f'https://backraz.ru/images/{category}/{name}/{producer}/{color}/{image_name}.jpg'
        with open(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}/{image_name}.jpg', 'wb') as fh:
            fh.write(base64.b64decode(code))
        fh.close()
    await f_sim_all_items(broadcast=True)
    return link
