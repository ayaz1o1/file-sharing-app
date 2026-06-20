import socket
import os
import sys

PORT = 8080

def send_file(server_ip, file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found!")
        return

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    print(f"🚀 Connecting to phone at {server_ip}:{PORT}...")
    try:
        # Establish a raw TCP stream connection straight to the phone
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, PORT))
            
            # Send file metadata first (Name and Size), separated by a custom delimiter
            metadata = f"{file_name}:{file_size}".encode('utf-8')
            s.sendall(metadata + b'\n')
            
            # Wait for phone acknowledgment
            ack = s.recv(1024)
            if ack != b"READY":
                print("❌ Phone rejected the transfer initialization.")
                return

            print(f"📤 Sending '{file_name}' ({file_size / (1024*1024):.2f} MB)...")
            with open(file_path, "rb") as f:
                bytes_sent = 0
                while chunk := f.read(4096):
                    s.sendall(chunk)
                    bytes_sent += len(chunk)
                    # Simple progress printing tracking line
                    print(f"\rProgress: {(bytes_sent / file_size) * 100:.1f}%", end="")
            
            print("\n✅ Transfer Complete!")
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")

if __name__ == "__main__":
    print("⚡ P2P Dedicated File Sharing Client ⚡")
    target_ip = input("Enter your mobile phone IP address (from app screen): ").strip()
    target_file = input("Drag and drop or type the path of the file to send: ").strip('" ')
    
    send_file(target_ip, target_file)
