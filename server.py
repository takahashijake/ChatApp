import socket
import threading
import sys
from commands import ServerAdminHandler

from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout

connected_clients = []
clients_lock = threading.Lock()
clientNames = {}
kicked_clients = set()
class MessageReceiver:
    def __init__(self):
        self._buffer = b''

    def add_data(self, chunk: bytes):
        self._buffer += chunk

    def get_messages(self):
        while b'\n' in self._buffer:
            newline_index = self._buffer.find(b'\n')
            
            message_bytes = self._buffer[:newline_index]
            self._buffer = self._buffer[newline_index + 1:]

            yield message_bytes.decode('utf-8')

    def has_pending_data(self) -> bool:
        return bool(self._buffer)
        
def handleClients(client_socket, client_address, admin_print_func):
    message_receiver = MessageReceiver()
    clientName = ''
    with clients_lock:
        connected_clients.append(client_socket)
    try:
        name = client_socket.recv(1024)
        if not name:
            admin_print_func(f"Client {client_socket.getpeername()} disconnected")
            return
        message_receiver.add_data(name)
        client_name = next(message_receiver.get_messages()).strip() # Use .strip() for the name
        
        with clients_lock:
            clientNames[client_name] = client_socket
        admin_print_func(f"Connection from {client_socket.getpeername()}")

        join_message = f"{client_name} has joined the chat.\n"
        broadcast_message(join_message.encode('utf-8'), sender_socket=client_socket)
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            message_receiver.add_data(data)
            for full_message in message_receiver.get_messages():
                admin_print_func(f"{client_name}: {full_message}")
                broadcast_message(f"{client_name}: {full_message}\n".encode('utf-8'), sender_socket=client_socket)
    except socket.error as e:
        admin_print_func(f"Error handling client {client_socket.getpeername()}")
    except Exception as e:
        admin_print_func("Unexpected error")
    finally:
        with clients_lock:
            if client_socket in connected_clients:
                connected_clients.remove(client_socket)
            if client_name in clientNames:
                del clientNames[client_name]
            if client_name:
                leave_message = f"{client_name} has left the chat.\n"
                broadcast_message(leave_message.encode('utf-8'))
                admin_print_func(leave_message.strip())
            client_socket.close()
            admin_print_func(f"Socket for {client_address} closed")
            
def broadcast_message(message: bytes, sender_socket = None):
    with clients_lock:
        for client_socket in connected_clients:
            if client_socket != sender_socket:
                try:
                    client_socket.sendall(message)
                except(BrokenPipeError, ConnectionResetError):
                    continue

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = 'localhost'
    port = 8000
    server_address = (host, port)

    try:
        server_socket.bind(server_address)
        print_formatted_text(f"Server started on {server_address}. Listening for connections...")
        server_socket.listen(5)
    except socket.error as e:
        print_formatted_text(f"Failed to bind socket: {e}")
        sys.exit(1)

    # Use a custom prompt_toolkit session for the server
    admin_session = PromptSession()
    def admin_print_func(text):
        with patch_stdout(raw=True):
            print_formatted_text(text)

    admin_handler = ServerAdminHandler(clientNames, clients_lock, broadcast_message, admin_print_func)
    admin_thread = threading.Thread(target=admin_handler.handle_admin_commands)
    admin_thread.daemon = True
    admin_thread.start()

    while True:
        try:
            conn, addr = server_socket.accept()
            admin_print_func(f"Connection from: {addr}")
            client_thread = threading.Thread(target=handleClients, args=(conn, addr, admin_print_func))
            client_thread.start()
        except KeyboardInterrupt:
            admin_print_func("Server shutting down.")
            break
        except Exception as e:
            admin_print_func(f"An error occurred while accepting a connection: {e}")
            
    server_socket.close()

if __name__ == '__main__':
    start_server()