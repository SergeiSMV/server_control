import ast
import json
from datetime import datetime
from datetime import date

import websockets
from router_init import router
from connections import sim_connect, sim_cursor
from sim.orders.sim_all_orders import f_sim_all_orders
from sim.orders.sim_uniq_items import f_sim_uniq_items
from sim.sim_all_items import f_sim_all_items
from sim.sql_functions.get_color_id import get_color_id
from sim.sql_functions.get_name_id import get_name_id
from sim.sql_functions.get_producer_id import get_producer_id


@router.route('/sim_add_order')
async def sim_add_order(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            result = await f_sim_add_order(client_data)
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def f_sim_add_order(data):
    order_data = data['items']
    author = data['author']
    num = datetime.now().strftime('%Y%m%d%H%M%S')
    date_order = date.today().strftime('%Y-%m-%d')
    time_order = datetime.now().strftime('%H:%M')

    for i in order_data:
        category = i['category']
        name = i['name']
        color = i['color']
        producer = i['producer']
        quantity = i['q_order']
        comment = i['comment']

        producer_id = await get_producer_id(producer)
        name_id = await get_name_id(category, name, producer_id)
        color_id = 0 if color == '' else await get_color_id(color)

        sim = 'SELECT * FROM items WHERE name = %s AND color = %s ORDER by fifo'
        sim_val = (name_id, color_id)
        sim_connect.ping(reconnect=True)
        sim_cursor.execute(sim, sim_val)
        items_list = sim_cursor.fetchall()
        sim_connect.commit()

        for item in items_list:
            base_quantity = int(item['quant'])
            base_reserve = int(item['reserve'])
            place_id = item['place']
            item_id = item['id']

            check_quantity = (base_quantity - base_reserve) - int(quantity)

            # если в ближайшей, согласно fifo, ячейке количество комлектующих больше, чем запрошено, то формируем
            # резерв и прерываем цикл
            if check_quantity >= 0:

                # обновляем (добавляем) резерв в основной базе СиМ
                updt_reserve = 'UPDATE items SET reserve = reserve + %s WHERE id = %s'
                updt_reserve_value = (quantity, item_id)
                sim_connect.ping(reconnect=True)
                sim_cursor.execute(updt_reserve, updt_reserve_value)
                sim_connect.commit()

                # добавляем в заявку информацию о комплектующих к выдаче
                crt = 'INSERT INTO orders ' \
                      '(num, item_id, place, name, color, producer, date, time, customer, order_quant, comment) '\
                      'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                crt_val = (num, item_id, place_id, name_id, color_id, producer_id, date_order, time_order, author,
                           quantity, comment)
                sim_connect.ping(reconnect=True)
                sim_cursor.execute(crt, crt_val)
                sim_cursor.fetchall()
                sim_connect.commit()
                break

            # если в ближайшей, согласно fifo, ячейке количество комлектующих меньше, чем запрошено, то формируем
            # резерв и продолжаем цикл по ячейкам согласно ФИФО
            if check_quantity < 0:

                # вычитаем резерв из количество комплектующих в ячейке, для корректного sql запроса и исключения
                # reserve > quantity
                quantity_max = base_quantity - base_reserve

                # ставим в резерв максимально доступное количество комплектующих в текущей ячейке
                if quantity_max == 0:
                    continue
                else:
                    # обновляем (добавляем) резерв в основную базу СиМ
                    updt_reserve = 'UPDATE items SET reserve = reserve + %s WHERE id = %s'
                    updt_reserve_value = (quantity_max, item_id)
                    sim_connect.ping(reconnect=True)
                    sim_cursor.execute(updt_reserve, updt_reserve_value)
                    sim_connect.commit()

                    # добавляем в заявку информацию о комплектующих к выдаче
                    crt = 'INSERT INTO orders ' \
                          '(num, item_id, place, name, color, producer, date, time, customer, order_quant, comment) ' \
                          'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                    crt_val = (num, item_id, place_id, name_id, color_id, producer_id, date_order, time_order, author, quantity_max, comment)
                    sim_connect.ping(reconnect=True)
                    sim_cursor.execute(crt, crt_val)
                    sim_cursor.fetchall()
                    sim_connect.commit()
                    quantity = check_quantity * -1
                continue

    await f_sim_all_items(broadcast=True)
    await f_sim_all_orders(broadcast=True)
    await f_sim_uniq_items(broadcast=True)
    return 'done'
