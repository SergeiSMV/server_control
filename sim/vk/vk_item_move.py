import ast
import json

import websockets
from router_init import router
from sim.vk.placing_all_items import placing_all_items
from sim.vk.placing_partial_items import placing_partial_items
from sim.vk.update_vk_all_exceptions import update_vk_all_exceptions
from sim.vk.update_vk_partial_exceptions import update_vk_partial_exceptions


@router.route('/vk_item_move')
async def vk_item_move(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_vk_item_move(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_vk_item_move(data):
    category = data['category']
    quantity = data['quantity']
    items_exceptions = data['exceptions']
    quantity_move = data['quantity_move']

    quantity_residue = int(quantity) - int(quantity_move)

    # если ТМЦ присутствуют в списке исключения
    if category in items_exceptions:
        await update_vk_all_exceptions(data) if quantity_residue == 0 else await update_vk_partial_exceptions(data)
    # если ТМЦ отсутствует в списке исключения
    else:
        await placing_all_items(data) if quantity_residue == 0 else await placing_partial_items(data)

    # await f_vk_all_items(broadcast=True)
    return 'done'
