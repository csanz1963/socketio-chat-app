import os
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ChatServerFixed")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
app.config['DEBUG'] = False

# Configuración explícita para Socket.IO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=True,
    always_connect=True
)

# Estado del chat
clients = {}
usernames = {}

@app.route('/')
def index():
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chat Multiplataforma - Cloud FIXED</title>
        <style>body { font-family: Arial; margin: 40px; text-align: center; }</style>
    </head>
    <body>
        <h1>✅ Chat Multiplataforma - Cloud FIXED</h1>
        <p>Servidor Socket.IO funcionando</p>
        <div id="status">Estado: Conectando...</div>
        <div id="users">Usuarios: 0</div>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
        <script>
            const socket = io({
                transports: ['websocket', 'polling'],
                timeout: 10000
            });
            
            socket.on('connect', function() {
                document.getElementById('status').textContent = 'Estado: CONECTADO';
                socket.emit('register', {username: 'WebUser'});
            });
            
            socket.on('users_update', function(data) {
                document.getElementById('users').textContent = 'Usuarios: ' + data.count;
            });
            
            socket.on('disconnect', function() {
                document.getElementById('status').textContent = 'Estado: DESCONECTADO';
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'users_online': len(clients)}

@socketio.on('connect')
def handle_connect():
    logger.info(f"✅ Cliente conectado: {request.sid}")
    clients[request.sid] = request.sid
    emit('connected', {'message': 'Bienvenido al chat!'})

@socketio.on('disconnect')
def handle_disconnect():
    username = usernames.get(request.sid, 'Unknown')
    if request.sid in clients:
        del clients[request.sid]
    if request.sid in usernames:
        del usernames[request.sid]
    
    logger.info(f"❌ Cliente desconectado: {username}")
    emit('users_update', {'count': len(clients)}, broadcast=True)

@socketio.on('register')
def handle_register(data):
    username = data.get('username', f'User_{request.sid[:6]}')
    usernames[request.sid] = username
    
    logger.info(f"👤 Usuario registrado: {username}")
    emit('users_list', {'users_online': list(usernames.values())})
    emit('user_joined', {'username': username}, broadcast=True)

@socketio.on('chat_message')
def handle_chat_message(data):
    username = usernames.get(request.sid, 'Unknown')
    message = data.get('message', '')
    
    logger.info(f"💬 Mensaje de {username}: {message}")
    emit('chat_message', {
        'username': username,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Iniciando servidor FIXED en puerto {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
