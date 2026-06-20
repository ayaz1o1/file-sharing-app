import os
import sys

# Graphics overrides
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
else:
    os.environ['KIVY_GL_BACKEND'] = 'sdl2'

import socket
from threading import Thread
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.utils import platform

class FileSharingApp(App):
    def build(self):
        self.port = 8080
        self.shared_dir = self.get_shared_directory()
        self.ip_address = self.get_local_ip()
        
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        self.title_label = Label(text="⚡ P2P Socket Receiver ⚡", font_size='24sp', bold=True, size_hint_y=0.2)
        self.info_label = Label(text="Initializing socket stream listeners...", font_size='16sp', halign='center')
        
        self.layout.add_widget(self.title_label)
        self.layout.add_widget(self.info_label)
        
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE], self.permission_callback)
        else:
            self.start_server_thread()
            
        return self.layout

    def permission_callback(self, permissions, grants):
        self.start_server_thread()

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    def get_shared_directory(self):
        if platform == 'android':
            from android.storage import primary_external_storage_path
            download_path = os.path.join(primary_external_storage_path(), 'Download')
            if os.path.exists(download_path): return download_path
            return primary_external_storage_path()
        else:
            fallback_path = os.path.join(os.getcwd(), "shared_files")
            os.makedirs(fallback_path, exist_ok=True)
            return fallback_path

    def start_server_thread(self):
        server_thread = Thread(target=self.run_socket_server, daemon=True)
        server_thread.start()
        
        instructions = (
            f"📱 Phone Server Active!\n\n"
            f"Your Phone IP: {self.ip_address}\n"
            f"Listening on Port: {self.port}\n\n"
            f"Run 'client.py' on your laptop to transfer files.\n"
            f"Saving files directly to:\n{self.shared_dir}"
        )
        self.info_label.text = instructions

    def update_status(self, text):
        # Thread-safe method to update UI text status
        self.info_label.text = text

    def run_socket_server(self):
        # Open a low-level TCP socket server to accept raw byte buffers
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(("0.0.0.0", self.port))
            server_sock.listen(5)
            
            while True:
                try:
                    conn, addr = server_sock.accept()
                    # Spin off file receiver process into a background task
                    Thread(target=self.handle_incoming_file, args=(conn, addr), daemon=True).start()
                except Exception as e:
                    print(f"Socket Server Error: {e}")

    def handle_incoming_file(self, conn, addr):
        try:
            # Read metadata line until newline character flag
            reader = conn.makefile('rb')
            metadata = reader.readline().decode('utf-8').strip()
            if not metadata:
                return

            file_name, file_size = metadata.split(':')
            file_size = int(file_size)
            
            out_path = os.path.join(self.shared_dir, file_name)
            self.update_status(f"📥 Receiving: {file_name}\nFrom: {addr[0]}\nSize: {file_size / (1024*1024):.2f} MB")
            
            # Send greenlight signal back to laptop client program
            conn.sendall(b"READY")
            
            # Read raw binary payloads and stream directly down onto disk storage
            bytes_received = 0
            with open(out_path, 'wb') as fout:
                while bytes_received < file_size:
                    chunk = conn.recv(min(4096, file_size - bytes_received))
                    if not chunk:
                        break
                    fout.write(chunk)
                    bytes_received += len(chunk)
            
            self.update_status(f"✅ Successfully Saved:\n{file_name}\n\nWaiting for next file transfer...")
        except Exception as e:
            self.update_status(f"❌ Transfer Error:\n{e}\n\nRestarting Listener...")
        finally:
            conn.close()

if __name__ == '__main__':
    FileSharingApp().run()
