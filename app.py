from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room
import pika
import threading
from pika.exceptions import AMQPConnectionError


app = Flask(__name__)
app.secret_key = 'your_secret_key'
#socketio = SocketIO(app, ping_timeout=30)  # Aumentar el tiempo de espera a 30 segundos
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# Configuración de RabbitMQ
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USERNAME = 'guest'
RABBITMQ_PASSWORD = 'guest'


def consume_messages(queue_name):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD))
    )
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    def callback(ch, method, properties, body):
        # Emitir el mensaje recibido al cliente a través de WebSocket
        socketio.emit('message', body.decode())

        # Imprimir el mensaje consumido en la consola
        print(f'Message consumed-> {queue_name}: {body.decode()}')

        # Confirmar el procesamiento exitoso del mensaje
        channel.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming()



def publish_message(queue_name, message):
    print(f'Received message from client {queue_name}: {message}')
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD))
        )
        channel = connection.channel()
        channel.queue_declare(queue=queue_name)
        channel.basic_publish(exchange='', routing_key=queue_name, body=message.encode())
        connection.close()
    except AMQPConnectionError as e:
        print(f"Error al conectar con RabbitMQ: {e}")

@app.route('/')
def login():
    return render_template('login.html')


@app.route('/chat', methods=['POST'])
def chat():
    session['sender_id'] = request.form['sender_id']
    session['recipient_id'] = request.form['recipient_id']
    return render_template('chat.html',emisor=request.form['sender_id'], receptor=request.form['recipient_id'])


@socketio.on('connect')
def handle_connect():
    recipient_id = session.get('recipient_id')
    sender_id = session.get('sender_id')

    if recipient_id and sender_id:
        queue_name = f'{recipient_id}_{sender_id}'

        t = threading.Thread(target=consume_messages, args=(queue_name,))
        t.start()


@socketio.on('message')
def handle_message(message):
    recipient_id = session.get('recipient_id')
    sender_id = session.get('sender_id')

    if recipient_id and sender_id:
        queue_name = f'{sender_id}_{recipient_id}'

        # Publicar el mensaje en la cola RabbitMQ
        publish_message(queue_name, message)

        # Emitir el mensaje recibido al cliente a través de WebSocket
        socketio.emit('message', message, room=f'{recipient_id}_{sender_id}')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)