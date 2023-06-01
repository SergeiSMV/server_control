import ast
import json
import os
from email.mime.application import MIMEApplication

import qrcode as qrcode
import websockets
from router_init import router
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


@router.route('/send_qr')
async def send_qr(ws, path):
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                result = await sql_send_qr(client_data)
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                break
    except websockets.ConnectionClosedError:
        pass


async def sql_send_qr(data):
    item_data = data['data']
    itemId = item_data['itemId']
    category = item_data['category']
    name = item_data['name']
    color = item_data['color']
    producer = item_data['producer']
    fifo = item_data['fifo']
    place = item_data['place']
    cell = item_data['cell']
    text = f'{category}\n{name} {color}\n({producer})\n{fifo}\n{place} {cell}'

    # with open('/usr/local/bin/images/qrcode.jpeg', 'wb') as fl:
    #     Code128(bcode, writer=ImageWriter()).write(fl)

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=20,
        border=4,
    )
    qr.add_data(str(itemId))
    qr.make()
    img = qr.make_image()
    img.save('/usr/local/bin/server_control/qrcode.jpeg')

    base_image = Image.open('/usr/local/bin/server_control/qrcode.jpeg')
    base_size = base_image.size
    new_size = (base_size[0], base_size[1] + 300)
    image = Image.new('RGB', new_size, (255, 255, 255))
    image.paste(base_image, (0, 0))

    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("DejaVuSans.ttf", 35, encoding='UTF-8')
    draw.text((100, 610), text, font=font, fill=(0, 0, 0))
    image_convert = image.convert('RGB')
    image_convert.save('/usr/local/bin/server_control/qrcode.pdf')

    # image.save('/usr/local/bin/images/qrcode.jpeg')

    sender = 's9051133401@yandex.ru'
    password = '20Cthtuf01'
    server = smtplib.SMTP('smtp.yandex.ru', 587)
    server.starttls()

    with open('/usr/local/bin/server_control/qrcode.pdf', 'rb') as f:
        doc = f.read()

    # with open('/usr/local/bin/images/qrcode.jpeg', 'rb') as f:
    #     img_data = f.read()
    msg = MIMEMultipart()
    msg['Subject'] = f'{category} {name} {color} ({fifo})'
    msg['From'] = sender
    text = MIMEText(f'QR-код для {category} {name} {color}.\nПоставщик: {producer}\nДата поступления: {fifo}')
    msg.attach(text)
    # image = MIMEImage(doc)
    document = MIMEApplication(doc, _subtype="pdf")
    document.add_header('Content-Disposition', 'attachment', filename=str('qrcode.pdf'))
    msg.attach(document)

    try:
        server.login(sender, password)
        # server.sendmail(sender, 'sklad1@tungstone.ru', msg.as_string())
        server.sendmail(sender, 's9051133401@yandex.ru', msg.as_string())
        server.sendmail(sender, 'gorbunova@tungstone.ru', msg.as_string())
        server.quit()
        os.remove('/usr/local/bin/server_control/qrcode.jpeg')
        os.remove('/usr/local/bin/server_control/qrcode.pdf')
    except Exception as _ex:
        pass

    return 'done'

