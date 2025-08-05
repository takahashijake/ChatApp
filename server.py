import socket
import threading
import sys
from commands import ServerAdminHandler

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
        
def handleClients(client_socket, client_address):
    message_receiver = MessageReceiver()
    clientName = ''
    with clients_lock:
        connected_clients.append(client_socket)
    try:
        name = client_socket.recv(1024)
        if not name:
            print(f"Client {client_socket.getpeername()} disconnected")
            return
        message_receiver.add_data(name)
        client_name = next(message_receiver.get_messages())

        with clients_lock:
            clientNames[client_name] = client_socket
        print(f"Conncetion from {client_socket.getpeername()}")

        join_message = f"{client_name} has joined the chat.\n"
        broadcast_message(join_message.encode('utf-8'), sender_socket=client_socket)
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            message_receiver.add_data(data)
            for full_message in message_receiver.get_messages():
        
                print(f"{client_name}: {full_message}")
                broadcast_message(f"{client_name}: {full_message}\n".encode('utf-8'), sender_socket=client_socket)
    except socket.error as e:
        print(f"Error handling client {client_socket.getpeername()}")
    except Exception as e:
        print("Unexpected error")
    finally:
        with clients_lock:
            if client_socket in connected_clients:
                connected_clients.remove(client_socket)
            if client_name in clientNames:
                del clientNames[client_name]
            if client_name:
                leave_message = f"\n{client_name} has left the chat.\n"
                broadcast_message(leave_message.encode('utf-8'))
                print(leave_message.strip())
            client_socket.close()
            print(f"Socket for {client_address} closed")

def broadcast_message(message: bytes, sender_socket = None):
    with clients_lock:
        for client_socket in connected_clients:
            if client_socket != sender_socket:
                try:
                    client_socket.sendall(message)
                except(BrokenPipeError, ConnectionResetError):
                    continue

def start_server():
    """
    Main server function that accepts new connections and spawns threads.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = 'localhost'
    port = 8000
    server_address = (host, port)

    try:
        server_socket.bind(server_address)
        print(f"Server started on {server_address}. Listening for connections...")
        server_socket.listen(5) # The backlog queue size
    except socket.error as e:
        print(f"Failed to bind socket: {e}")
        sys.exit(1)

    admin_handler = ServerAdminHandler(clientNames, clients_lock, broadcast_message)
    admin_thread = threading.Thread(target=admin_handler.handle_admin_commands)
    admin_thread.daemon = True
    admin_thread.start()
    # Main server loop to accept new connections indefinitely
    while True:
        try:
            # The accept() call will block here until a new client connects.
            # It returns a new socket object (conn) and the client's address.
            conn, addr = server_socket.accept()
            print(f"Connection from: {addr}")

            # Create a new thread to handle this specific client.
            client_thread = threading.Thread(target=handleClients, args=(conn, addr))
            
            # Start the new thread. It will now run the handle_client_connection function.
            client_thread.start()

        except KeyboardInterrupt:
            print("\nServer shutting down.")
            break
        except Exception as e:
            print(f"An error occurred while accepting a connection: {e}")
            
    # Clean up and close the main server socket
    server_socket.close()

if __name__ == '__main__':
    start_server()
