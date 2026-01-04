import subprocess
import sys
import time
import os

def main():
    # Use the same Python interpreter that is running this script
    py_exec = sys.executable
    
    # Get absolute paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(base_dir, "server.py")
    client_script = os.path.join(base_dir, "client.py")

    print(f"Using Python: {py_exec}")
    print("Launching Server in a new window...")
    
    # CREATE_NEW_CONSOLE is a Windows-only flag (0x10) to open a new terminal window
    # This prevents the server from blocking the current terminal
    subprocess.Popen([py_exec, server_script], creationflags=subprocess.CREATE_NEW_CONSOLE)

    print("Waiting 2 seconds for server to initialize...")
    time.sleep(2)

    print("Launching Client 1...")
    subprocess.Popen([py_exec, client_script])  # GUI doesn't need a console strictly, but Popen defaults are fine for now

    print("launching Client 2 (for testing multi-user)...")
    subprocess.Popen([py_exec, client_script])
    
    print("Done! You should see the Server window and two Client windows.")

if __name__ == "__main__":
    main()
