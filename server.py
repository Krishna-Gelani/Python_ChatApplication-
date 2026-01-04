import socket
import threading
import sqlite3
import datetime
from cryptography.fernet import Fernet

# Configuration
HOST = '127.0.0.1'
PORT = 55555
DB_NAME = 'chat_history.db'

# Simple Authentication (Username: Password)
USERS = {
    "alice": "password123",
    "bob": "securepass",
    "admin": "admin"
}

# Generate a key for this session (In a real app, use RSA for key exchange)
# We will send this key to clients upon connection so they can encrypt/decrypt
KEY = Fernet.generate_key()
cipher_suite = Fernet(KEY)

clients = []
nicknames = []

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (timestamp TEXT, sender TEXT, message TEXT)''')
    conn.commit()
    conn.close()

def save_message(sender, message):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO messages (timestamp, sender, message) VALUES (?, ?, ?)", 
                  (timestamp, sender, message))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving to DB: {e}")

def broadcast(message, _sender=None):
    """Broadcasts a raw message (bytes) to all clients."""
    for client in clients:
        try:
            client.send(message)
        except:
            # Clean up broken links potentially here, but usually handled in handle()
            pass

def handle(client):
    while True:
        try:
            # Receive message
            message_encrypted = client.recv(1024)
            if not message_encrypted:
                raise Exception("Empty message")
            
            # Decrypt to log and print on server
            try:
                decrypted_message = cipher_suite.decrypt(message_encrypted).decode('utf-8')
                
                # Check for special formats or just broadcast
                # We assume the client formats standard messages as "Nickname: Message"
                if ": " in decrypted_message:
                    parts = decrypted_message.split(": ", 1)
                    if len(parts) == 2:
                        sender, msg_content = parts
                        save_message(sender, msg_content)
                        print(f"Log: {sender} said {msg_content}")
                
                broadcast(message_encrypted)
                
            except Exception as e:
                # Could be a system message or error
                print(f"Decryption error or malformed message: {e}")
                
        except:
            if client in clients:
                index = clients.index(client)
                clients.remove(client)
                client.close()
                nickname = nicknames[index]
                broadcast(cipher_suite.encrypt(f'{nickname} left the chat!'.encode('utf-8')))
                nicknames.remove(nickname)
                print(f"{nickname} disconnected.")
            break

def receive():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    
    print(f"Server is running on {HOST}:{PORT}")
    print(f"Session Encryption Key: {KEY.decode()}")
    print("Waiting for connections...")

    init_db()

    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        # 1. Send the Encryption Key first
        client.send(KEY)

        # 2. Authentication Protocol
        # Request Username
        client.send(cipher_suite.encrypt("USERNAME".encode('utf-8')))
        encrypted_username = client.recv(1024)
        username = cipher_suite.decrypt(encrypted_username).decode('utf-8')
        
        # Request Password
        client.send(cipher_suite.encrypt("PASSWORD".encode('utf-8')))
        encrypted_password = client.recv(1024)
        password = cipher_suite.decrypt(encrypted_password).decode('utf-8')

        # Verify
        if username in USERS and USERS[username] == password:
            client.send(cipher_suite.encrypt("LOGIN_SUCCESS".encode('utf-8')))
            nicknames.append(username)
            clients.append(client)

            print(f"Nickname of the client is {username}!")
            broadcast(cipher_suite.encrypt(f"{username} joined the chat!".encode('utf-8')))
            
            # Start handling thread
            thread = threading.Thread(target=handle, args=(client,))
            thread.start()
        else:
            client.send(cipher_suite.encrypt("LOGIN_FAILED".encode('utf-8')))
            client.close()
            print(f"Failed login attempt for {username}")

if __name__ == "__main__":
    receive()
