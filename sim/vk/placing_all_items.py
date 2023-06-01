from connections import sim_connect, sim_cursor
from sim.sim_all_items import f_sim_all_items
from sim.sql_functions.get_nm_item_id import get_nm_item_id
from sim.sql_functions.get_producer_id import get_producer_id
from sim.sql_functions.get_unit_id import get_unit_id
from sim.vk.placing_big_pallets import placing_big_pallets
from sim.vk.placing_standart_pallets import placing_standart_pallets
from sim.vk.vk_all_items import f_vk_all_items


async def placing_all_items(data):
    category = data['category']
    name = data['name']
    producer = data['producer']
    unit = data['unit']
    pallet_row = data['pallet_row']  # количество ТМЦ в ряду
    pallet_quantity = data['pallet_quantity']  # количество ТМЦ на паллете
    pallet_size = data['pallet_size']  # размер паллета
    quantity_move = data['quantity_move']  # количество для размещения

    # расчет количества паллет для размещения
    pallet_count = int(quantity_move) / int(pallet_quantity)

    # получаем id ТМЦ по категории, наименованию, поставщику
    producer_id = await get_producer_id(producer)
    unit_id = await get_unit_id(unit)
    nm_item_id = await get_nm_item_id(category, name, producer_id, unit_id)

    # получаем информацию о ТМЦ (размеры, количество в таре)
    sql_item_info = 'SELECT * FROM nomenclature WHERE id = %s'
    item_value = (nm_item_id,)
    sim_connect.ping(reconnect=True)
    sim_cursor.execute(sql_item_info, item_value)
    item_info = sim_cursor.fetchone()
    sim_connect.commit()

    box_size_string = item_info['box_size']  # размер тары
    box_quantity_string = item_info['box_quantity']  # количество ТМЦ в таре

    # расчет высоты паллета
    box_size_list = box_size_string.split('x')
    box_height = box_size_list[1]  # высота тары ТМЦ
    boxes = (int(pallet_quantity) / int(box_quantity_string))  # количество тары на паллете
    boxes_rows = boxes / int(pallet_row)  # количество рядов тары на паллете
    pallet_height = (int(box_height) * boxes_rows) + 150  # 150 - высота поддона

    await placing_big_pallets(data, pallet_height, pallet_count) if pallet_size == 'big' else await placing_standart_pallets(data, pallet_height, pallet_count)
    await f_vk_all_items(broadcast=True)
    await f_sim_all_items(broadcast=True)
