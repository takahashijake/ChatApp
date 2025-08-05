import socket 
import sys
import threading
from server import MessageReceiver
from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout

session = PromptSession("You: ")
is_connected = threading.Event()
is_connected.set()
prompt_text = "You: "
def receive_message(sock):
    message_receiver = MessageReceiver()
    try:
        while is_connected.is_set():
            data = sock.recv(1024)
            if not data:
                is_connected.clear()
                break
            message_receiver.add_data(data)
            for message in message_receiver.get_messages():
                with patch_stdout(raw=True):
                    print_formatted_text(f"{message}") 

    except(ConnectionResetError, BrokenPipeError):
        is_connected.clear()
        print_formatted_text("Disonnected from server. ")
    except Exception as e:
        is_connected.clear()
        print_formatted_text(f"An error occured while receiving messages: {e}")

def start_client():
    stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 8000)

    print(f'Atteming to connect to {server_address}')

    try:
        stream_socket.connect(server_address)
        print("Successfully connected to server!")
    except socket.error as e:
        print(f"Connection failed: {e}")
        stream_socket.close()
        sys.exit(1)
    try: 
        name = session.prompt("Please enter your name: ")
        stream_socket.sendall((name + '\n').encode('utf-8'))

        receive_thread = threading.Thread(target=receive_message, args=(stream_socket,))
        receive_thread.daemon = True
        receive_thread.start()
        
    except (ConnectionResetError, BrokenPipeError, KeyboardInterrupt, Exception) as e:
        print("Failed to send name to server: {e}")
        stream_socket.close()
        sys.exit(1)

    try:
        while is_connected.is_set():
            message = session.prompt("You: ")
            if not message:
                continue
            full_message = (message + '\n').encode('utf-8')
            stream_socket.sendall(full_message)
    except ConnectionResetError:
        print("Lost connection to the server. ")
    except BrokenPipeError:
        print("Cannot send data. Conncetion is closed")
    except KeyboardInterrupt:
        print("Client shutting down")
    except Exception as e:
        print("Unexpected error occurred")
    finally:
        print("Closing socket")
        stream_socket.close()
        sys.exit()

start_client()