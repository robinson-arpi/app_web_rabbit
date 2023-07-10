from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room
import threading
from rabbitmq import create_queue, send_message, delete_queue, receive_message

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuración de RabbitMQ
# ...

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/chat', methods=['POST'])
def chat():
    session['recipient_id'] = request.form['recipient_id']
    session['sender_id'] = request.form['sender_id']
    return render_template('chat.html', receptor=session['recipient_id'], nick = session['sender_id'])

@socketio.on('connect')
def handle_connect():
    recipient_id = session.get('recipient_id')

    if recipient_id:
        queue_name = f'{recipient_id}'

        # Crear la cola en RabbitMQ
        create_queue(queue_name)

        # Crear un objeto Room para el chat
        join_room(queue_name)

        # Recuperar y enviar el historial de mensajes al nuevo cliente
        previous_messages = []
        while True:
            message = receive_message(queue_name)
            if message:
                previous_messages.append(message)
            else:
                break

        for message in previous_messages:
            emit('message', {'message': message, 'queue_name': queue_name})

@socketio.on('disconnect')
def handle_disconnect():
    recipient_id = session.get('recipient_id')

    if recipient_id:
        queue_name = f'{recipient_id}'

        # Eliminar la cola en RabbitMQ
        #delete_queue(queue_name)

@socketio.on('message')
def handle_message(data):
    recipient_id = session.get('recipient_id')

    if recipient_id:
        queue_name = f'{recipient_id}'

        # Enviar el mensaje a la cola en RabbitMQ
        send_message(queue_name, data['message'])

        # Publicar el mensaje en la sala del chat
        emit('message', {'message': data['message'], 'queue_name': queue_name}, room=queue_name)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)