from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room
import pika
import threading
from pika.exceptions import AMQPConnectionError

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configuración de RabbitMQ
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USERNAME = 'guest'
RABBITMQ_PASSWORD = 'guest'

# Crear un diccionario para almacenar los hilos activos por cliente
active_threads = {}

def consume_messages(queue_name, sender_id, stop_event):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD))
    )
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    def callback(ch, method, properties, body):
        # Emitir el mensaje recibido al cliente a través de WebSocket
        if sender_id == 'robin':
            socketio.emit('message_r', {'message': body.decode()})
            # Confirmar el procesamiento exitoso del mensaje
            channel.basic_ack(delivery_tag=method.delivery_tag)
            print('robin')
        elif sender_id == 'mauro':
            socketio.emit('message_m', {'message': body.decode()})
            # Confirmar el procesamiento exitoso del mensaje
            channel.basic_ack(delivery_tag=method.delivery_tag)
            print('mauro')
        elif sender_id == 'cristian':
            socketio.emit('message_c', {'message': body.decode()})
            # Confirmar el procesamiento exitoso del mensaje
            channel.basic_ack(delivery_tag=method.delivery_tag)
            print('cristian')
        elif sender_id == 'vero':
            socketio.emit('message_v', {'message': body.decode()})    
            # Confirmar el procesamiento exitoso del mensaje
            channel.basic_ack(delivery_tag=method.delivery_tag)
            print('vero')
        # Imprimir el mensaje consumido en la consola
        print(f'Message consumed-> {queue_name}: {body.decode()}')

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
    return render_template('chat.html', emisor=session['sender_id'], receptor=session['recipient_id'])

@socketio.on('connect')
def handle_connect():
    recipient_id = session.get('recipient_id')
    sender_id = session.get('sender_id')

    if recipient_id and sender_id:
        queue_name = f'{recipient_id}_{sender_id}'
        print(f'consume de -> {queue_name}')

        # Crear un objeto Event para controlar el ciclo del hilo
        stop_event = threading.Event()

        t = threading.Thread(target=consume_messages, args=(queue_name, sender_id, stop_event))
        t.start()

        # Registrar el hilo activo en el diccionario
        active_threads[sender_id] = (t, stop_event)

@socketio.on('disconnect')
def handle_disconnect():
    sender_id = session.get('sender_id')

    if sender_id in active_threads:
        # Obtener el hilo y el objeto Event correspondientes al cliente desconectado
        t, stop_event = active_threads.pop(sender_id)

        # Establecer la bandera en el objeto Event para indicar al hilo que debe finalizar
        stop_event.set()

        # Esperar a que el hilo termine su ejecución
        t.join()
        print("Mata hilo")

@socketio.on('message')
def handle_message(message):
    recipient_id = session.get('recipient_id')
    sender_id = session.get('sender_id')

    if recipient_id and sender_id:
        queue_name = f'{sender_id}_{recipient_id}'

        # Publicar el mensaje en la cola RabbitMQ
        publish_message(queue_name, message)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
