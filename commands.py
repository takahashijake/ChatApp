import threading
from typing import Dict, List, Any 
from prompt_toolkit import PromptSession # New import
from prompt_toolkit import print_formatted_text # New import

class ServerAdminHandler:  
    def __init__(self, clientNames: Dict[str, Any], clients_lock: threading.Lock, broadcast_message):
        self.clients_by_name = clientNames
        self.clients_lock = clients_lock
        self.broadcast_message = broadcast_message
        self.running = True
        self.session = PromptSession() # New: Create a session object

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
                    self.running = False
                    break
                else:
                    print_formatted_text("Unknown command. Available commands: kick <name>, list, exit")
            except (EOFError, KeyboardInterrupt):
                print_formatted_text("Admin console closing.")
                break
            except Exception as e:
                print_formatted_text(f"An error occurred: {e}")
    
    def kick_user(self, name_to_kick: str):
        """Forcefully disconnects a user by name."""
        name_to_kick = name_to_kick.strip()
        with self.clients_lock:
            target_socket = self.clients_by_name.get(name_to_kick)
            if target_socket:
                print_formatted_text(f"Kicking user '{name_to_kick}'...")
                kicked_user_message = f"[Server] You have been kicked from the server.\n"
                broadcast_kick_message = f"[Server] User '{name_to_kick}' has been kicked.\n"
            
                try:
                    target_socket.send(kicked_user_message.encode('utf-8'))
                except Exception as e:
                    print_formatted_text(f"Failed to send kick message to '{name_to_kick}': {e}")
                finally:
                    target_socket.close()
                    del self.clients_by_name[name_to_kick]
                    self.broadcast_message(broadcast_kick_message.encode('utf-8'))

            else:
                print_formatted_text(f"User '{name_to_kick}' not found.")

    def list_users(self):
        """Prints a list of connected users to the server console."""
        with self.clients_lock:
            names = self.clients_by_name.keys()
            if names:
                print_formatted_text("Connected users:", ", ".join(names))
            else:
                print_formatted_text("No users are currently connected.")