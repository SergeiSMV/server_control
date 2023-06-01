import ast
import json
import websockets
from connections import sim_connect, sim_cursor
from router_init import router

CLIENTS_SIM = {}


@router.route('/sim_all_orders')
async def sim_all_orders(ws, path):
    global CLIENTS_SIM
    user_id = 0
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                user_id = client_data['user_id']
                CLIENTS_SIM[user_id] = ws
                result = await f_sim_all_orders()
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                await delClient(user_id)
                break
    except websockets.ConnectionClosedError:
        await delClient(user_id)


async def f_sim_all_orders(broadcast=False):
    allSimOrdersList = []

    sql = 'SELECT num, date, time, customer, MIN(status) AS MinStatus FROM orders GROUP BY num, date, time, customer'
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql, )
    result = sim_cursor.fetchall()
    sim_connect.commit()

    for order in result:
        # oder_id = order['id']
        num = order['num']
        date = order['date'].strftime('%d.%m.%Y')
        time = order['time']
        customer = order['customer']
        status = order['MinStatus']

        orders_map = {
            'num': num, 'date': date, 'time': time,
            'customer': customer, 'status': status
        }
        allSimOrdersList.append(orders_map)

    if broadcast:
        for ws in CLIENTS_SIM:
            await CLIENTS_SIM[ws].send(json.dumps(allSimOrdersList))
    else:
        return allSimOrdersList


async def delClient(user_id):
    try:
        del CLIENTS_SIM[user_id]
    except KeyError:
        pass
