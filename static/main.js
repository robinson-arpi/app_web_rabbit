var socket = io();

function createQueues() {
    var ID = document.getElementById('ID').value;
    var ID_destinatario = document.getElementById('ID_destinatario').value;
    var url = '/create_queues?ID=' + ID + '&ID_destinatario=' + ID_destinatario;
    fetch(url)
        .then(response => response.text())
        .then(data => {
            console.log(data);
        })
        .catch(error => {
            console.error(error);
        });
}

function sendMessage() {
    var ID_destinatario = document.getElementById('ID_destinatario').value;
    var message = document.getElementById('message');
    var message_content = ID_destinatario +  ": " + message.value;
    socket.emit('message', { 'ID_destinatario': ID_destinatario, 'message': message_content });
    message = "";
}

function getMessages() {
    var ID = document.getElementById('ID').value;
    socket.emit('get_messages', { 'ID': ID });
}

socket.on('messages', function (messages) {
    var messagesDiv = document.getElementById('messages');
    for (var i = 0; i < messages.length; i++) {
        var message = messages[i];
        var messageElement = document.createElement('p');
        messageElement.innerText = message;
        messagesDiv.insertAdjacentElement('beforeend', messageElement);
    }
});
