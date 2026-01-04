import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
from cryptography.fernet import Fernet
import winsound  # Windows only
import sys
import random


class ChatClient:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 55555
        self.cipher_suite = None
        self.running = True
        self.username = ""
        
        # Main Root
        self.root = tk.Tk()
        self.root.withdraw() # Hide until checking login
        
        self.gui_login()
        
        self.root.mainloop()

    def gui_login(self):
        self.login_win = tk.Toplevel()
        self.login_win.title("Secure Chat - Login")
        self.login_win.geometry("300x250")
        self.login_win.configure(bg="#f0f0f0")
        self.login_win.resizable(False, False)

        tk.Label(self.login_win, text="Username", bg="#f0f0f0").pack(pady=5)
        self.username_entry = tk.Entry(self.login_win)
        self.username_entry.pack(pady=5)

        tk.Label(self.login_win, text="Password", bg="#f0f0f0").pack(pady=5)
        self.password_entry = tk.Entry(self.login_win, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self.login_win, text="Login", command=self.login, bg="#4CAF50", fg="white").pack(pady=20)
        
        # Handle interaction if user closes login window
        self.login_win.protocol("WM_DELETE_WINDOW", self.on_login_close)

    def on_login_close(self):
        self.root.destroy()
        sys.exit()

    def play_notification(self):
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except:
            pass

    def login(self):
        user = self.username_entry.get()
        pwd = self.password_entry.get()
        
        if not user or not pwd:
            messagebox.showerror("Error", "Please fill valid fields")
            return

        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.host, self.port))
            
            # 1. Receive Encryption Key
            key = self.client.recv(1024)
            self.cipher_suite = Fernet(key)
            
            # 2. Handle Auth Protocol
            msg = self.client.recv(1024)
            if self.cipher_suite.decrypt(msg).decode() == 'USERNAME':
                self.client.send(self.cipher_suite.encrypt(user.encode('utf-8')))
            
            msg = self.client.recv(1024)
            if self.cipher_suite.decrypt(msg).decode() == 'PASSWORD':
                self.client.send(self.cipher_suite.encrypt(pwd.encode('utf-8')))
            
            msg = self.client.recv(1024)
            response = self.cipher_suite.decrypt(msg).decode()
            
            if response == "LOGIN_SUCCESS":
                self.username = user
                self.login_win.destroy()
                self.setup_chat_gui()
            else:
                messagebox.showerror("Error", "Login Failed")
                self.client.close()
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect: {e}")

    def setup_chat_gui(self):
        self.root.deiconify() # Show the main window
        self.root.title(f"Secure Chat - {self.username}")
        self.root.geometry("600x600")
        self.root.configure(bg="#2c3e50")

        # Top Bar
        top_frame = tk.Frame(self.root, bg="#34495e", height=50)
        top_frame.pack(fill=tk.X)
        self.status_label = tk.Label(top_frame, text="Status: Online", fg="#2ecc71", bg="#34495e", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=10, pady=10)

        # Chat Area
        self.chat_area = scrolledtext.ScrolledText(self.root, bg="#ecf0f1", font=("Arial", 10))
        self.chat_area.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)
        self.chat_area.config(state='disabled')

        # Input Area
        bottom_frame = tk.Frame(self.root, bg="#2c3e50")
        bottom_frame.pack(padx=10, pady=10, fill=tk.X)

        self.msg_entry = tk.Entry(bottom_frame, font=("Arial", 12))
        self.msg_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        self.msg_entry.bind("<Return>", self.send_message)

        # Emoji Button
        emoji_btn = tk.Button(bottom_frame, text="😊", command=self.add_emoji, font=("Arial", 12))
        emoji_btn.pack(side=tk.LEFT, padx=(0, 5))

        send_btn = tk.Button(bottom_frame, text="Send", command=self.send_message, bg="#3498db", fg="white", font=("Arial", 10, "bold"))
        send_btn.pack(side=tk.LEFT)

        # Start Receiving Thread
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def add_emoji(self):
        self.msg_entry.insert(tk.END, "😊")
        self.msg_entry.focus()

    def send_message(self, event=None):
        message = self.msg_entry.get()
        if message:


            full_msg = f"{self.username}: {message}"
            try:
                encrypted = self.cipher_suite.encrypt(full_msg.encode('utf-8'))
                self.client.send(encrypted)
                self.msg_entry.delete(0, tk.END)
            except:
                self.handle_disconnect()

    def receive_messages(self):
        while self.running:
            try:
                message_encrypted = self.client.recv(1024)
                if not message_encrypted:
                    break
                
                message = self.cipher_suite.decrypt(message_encrypted).decode('utf-8')
                # Use after() to safely update GUI from thread
                self.root.after(0, self.display_message, "", message)
                self.root.after(0, self.play_notification)
            except:
                if self.running:
                    self.root.after(0, self.handle_disconnect)
                break

    def display_message(self, sender, message):
        self.chat_area.config(state='normal')
        if sender:
            self.chat_area.insert(tk.END, f"{sender}: {message}\n")
        else:
            self.chat_area.insert(tk.END, f"{message}\n")
        self.chat_area.yview(tk.END)
        self.chat_area.config(state='disabled')

    def handle_disconnect(self):
        # Ensure label exists before configuring
        if hasattr(self, 'status_label'):
            self.status_label.config(text="Status: Offline", fg="red")
        print("Disconnected")
        self.running = False
        if hasattr(self, 'client'):
            self.client.close()

    def on_close(self):
        self.running = False
        if hasattr(self, 'client'):
            self.client.close()
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    client = ChatClient()
