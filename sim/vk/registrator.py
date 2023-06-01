from connections import sim_connect, sim_cursor
from sim.history.sim_create_history import sim_create_history

from sim.sim_send_qrcode import sql_send_qr
from sim.sql_functions.get_place_values import get_place_values


async def registrator(data, cell_id):
    author = data['author']
    document = data['document']

    # получаем последний добавленный id
    get_id = 'SELECT MAX(id) FROM items'
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(get_id, )
    last_id = sim_cursor.fetchall()
    sim_connect.commit()

    # запись в историю
    comment = f'входной контроль: {document}'
    await sim_create_history(last_id[0]['MAX(id)'], 'поступление', comment, author)

    # отправка QR кода
    place_info = await get_place_values(cell_id)
    data['place'] = place_info['place']
    data['cell'] = place_info['cell']
    data['itemId'] = last_id[0]['MAX(id)']
    qr_data = {'data': data}
    await sql_send_qr(qr_data)