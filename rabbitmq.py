import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

def create_queue(queue_name):
    channel.queue_declare(queue=queue_name)

def send_message(queue_name, message):
    channel.basic_publish(exchange='', routing_key=queue_name, body=message)

def receive_message(queue_name):
    method_frame, _, body = channel.basic_get(queue=queue_name, auto_ack=True)
    if method_frame:
        return body.decode()
    else:
        return None
