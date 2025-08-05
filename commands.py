import threading
from typing import Dict, List, Any 
from prompt_toolkit import PromptSession # New import
from prompt_toolkit import print_formatted_text # New import
import time
class ServerAdminHandler:  
    def __init__(self, clientNames: Dict[str, Any], clients_lock: threading.Lock, broadcast_message, admin_print_func):
        self.clients_by_name = clientNames
        self.clients_lock = clients_lock
        self.broadcast_message = broadcast_message
        self.running = True
        self.session = PromptSession() # New: Create a session object
        self.admin_print_func = admin_print_func

    def closeAllClients(self):
        with self.clients_lock:
            for client in self.clients_by_name:
                client_socket = self.clients_by_name.get(client)
                if client_socket:
                    endingMessage = "Server is shutting down. Press any key to exit"
                    try:
                        client_socket.send(endingMessage.encode('utf-8'))
                    except Exception as e:
                        self.admin_print_func(f"Faild to kick a user")
                    finally:
                        client_socket.close()
                        message = "successfully kicked user!"
                        self.broadcast_message(message.encode('utf-8'))




    def handle_admin_commands(self):
        """
        Runs in a separate thread and listens for admin commands from the console.
        """
        while self.running:
            try:
                # Use session.prompt() instead of input()
                command_line = self.session.prompt("Admin > ").strip()
                if not command_line:
                    continue
                
                command = command_line.split()
                action = command[0].lower()
                
                if action == "kick" and len(command) > 1:
                    name_to_kick = command[1]
                    self.kick_user(name_to_kick)
                elif action == "list":
                    self.list_users()
                elif action == "exit":
                    print_formatted_text("Exiting admin console.")
                    self.closeAllClients()
                    self.running = False
                    exit()
                    break
                else:
                    print_formatted_text("Unknown command. Available commands: kick <name>, list, exit")
            except (EOFError, KeyboardInterrupt):
                print_formatted_text("Admin console closing.")
                break
            except Exception as e:
                print_formatted_text(f"An error occurred: {e}")
    
    def kick_user(self, name_to_kick: str):
        with self.clients_lock:
            target_socket = self.clients_by_name.get(name_to_kick)
            if target_socket:
                self.admin_print_func(f"Kicking user '{name_to_kick}'...")
                kicked_user_message = f"[Server] You have been kicked from the server.\n"
                broadcast_kick_message = f"[Server] User '{name_to_kick}' has been kicked.\n"
                
                try:
                    target_socket.send(kicked_user_message.encode('utf-8'))
                except Exception as e:
                    self.admin_print_func(f"Failed to send kick message to '{name_to_kick}': {e}")
                finally:
                    # Closing the socket will cause the client handler thread to finish.
                    target_socket.close()
                    # It's better to remove the client name here to avoid issues
                    del self.clients_by_name[name_to_kick]
                    self.broadcast_message(broadcast_kick_message.encode('utf-8'))
                
                # Add a small delay to allow the client handler thread to finish its logging.
                time.sleep(0.1)

            else:
                self.admin_print_func(f"User '{name_to_kick}' not found.")
    def list_users(self):
        """Prints a list of connected users to the server console."""
        with self.clients_lock:
            names = self.clients_by_name.keys()
            if names:
                print_formatted_text("Connected users:", ", ".join(names))
            else:
                print_formatted_text("No users are currently connected.")