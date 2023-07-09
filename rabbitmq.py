import pika
parameters = pika.ConnectionParameters('localhost')
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

def connect():
    global connection, channel
    parameters = pika.ConnectionParameters('localhost')
    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            break
        except pika.exceptions.AMQPConnectionError:
            print("Error de conexión. Intentando reconectar...")
            continue

def create_queue(queue_name):
    try:
        channel.queue_declare(queue=queue_name, durable=True)
    except (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelClosedByBroker):
        print("Error de conexión. Reconectando...")
        connect()
        channel.queue_declare(queue=queue_name, durable=True)

def send_message(queue_name, message):
    try:
        channel.basic_publish(exchange='', routing_key=queue_name, body=message)
    except (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelClosedByBroker):
        print("Error de conexión. Reconectando...")
        connect()
        channel.basic_publish(exchange='', routing_key=queue_name, body=message)

def receive_message(queue_name):
    try:
        method_frame, _, body = channel.basic_get(queue=queue_name, auto_ack=True)
        if method_frame:
            return body.decode()
        else:
            return None
    except (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelClosedByBroker):
        print("Error de conexión. Reconectando...")
        connect()
        method_frame, _, body = channel.basic_get(queue=queue_name, auto_ack=True)
        if method_frame:
            return body.decode()
        else:
            return None

def delete_queue(queue_name):
    try:
        channel.queue_delete(queue=queue_name)
    except (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelClosedByBroker):
        print("Error de conexión. Reconectando...")
        connect()
        channel.queue_delete(queue=queue_name)

# Llamamos a la función connect para establecer la conexión inicial
connect()
