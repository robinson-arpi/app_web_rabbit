from flask import Flask, render_template, request
from flask_socketio import SocketIO
from rabbitmq import create_queue, send_message, receive_message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_queues', methods=['GET'])
def create_queues():
    id = request.args.get('ID')
    id_destinatario = request.args.get('ID_destinatario')
    create_queue(id)
    create_queue(id_destinatario)
    return 'Colas creadas'

@socketio.on('message')
def handle_message(data):
    id_destinatario = data['ID_destinatario']
    message = data['message']
    send_message(id_destinatario, message)

@socketio.on('get_messages')
def get_messages(data):
    id = data['ID']
    messages = []
    while True:
        message = receive_message(id)
        if message:
            messages.append(message)
        else:
            break
    socketio.emit('messages', messages)


if __name__ == '__main__':
    socketio.run(app)