import os
import sys

# ==============================================================================
# 1. HARD-FORCE GRAPHICS SETTINGS VIA KIVY CONFIG MATRIX
# ==============================================================================
from kivy.config import Config
# Force Kivy's window provider to use Angle (DirectX) directly, bypassing environment variables
Config.set('graphics', 'multisamples', '0')
Config.set('kivy', 'gl_backend', 'angle_sdl2')

if sys.platform == 'win32':
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

# Handle internal asset extraction paths if running inside a PyInstaller EXE bundle
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    os.chdir(bundle_dir)

# ==============================================================================
# 2. STANDARD LIBRARY IMPORTS
# ==============================================================================
import socket
import html
from threading import Thread
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from io import BytesIO
from email.parser import BytesParser
from email.policy import default

# ==============================================================================
# 3. KIVY USER INTERFACE IMPORTS
# ==============================================================================
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

# ==============================================================================
# 4. CONFIGURATION PARAMETERS
# ==============================================================================
SHARED_DIR = r"G:\Projects\File-Sharing-App\shared_files"
PORT = 8080

# ==============================================================================
# 5. WEBSERVER FILE ENGINE PIPELINE
# ==============================================================================
class DesktopShareHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SHARED_DIR, **kwargs)

    def list_directory(self, path):
        """Generates a styled, modern HTML web interface for the mobile browser."""
        try:
            dir_list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
            
        dir_list.sort(key=lambda a: a.lower())
        
        html_head = "<!DOCTYPE html><html><head><meta charset='utf-8'>" \
                    "<meta name='viewport' content='width=device-width, initial-scale=1.0'>" \
                    "<title>P2P File Share Dashboard</title><style>" \
                    "body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #333; }" \
                    ".container { max-width: 900px; margin: 0 auto; }" \
                    "header { background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }" \
                    "h1 { margin: 0; font-size: 24px; }" \
                    ".upload-card { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }" \
                    ".upload-btn { background-color: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; }" \
                    ".upload-btn:hover { background-color: #218838; }" \
                    ".file-list { background: white; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); list-style: none; padding: 0; margin: 0; overflow: hidden; }" \
                    ".file-item { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; border-bottom: 1px solid #eee; transition: background 0.2s; }" \
                    ".file-item:last-child { border-bottom: none; }" \
                    ".file-item:hover { background-color: #f8f9fa; }" \
                    ".file-info { display: flex; align-items: center; text-decoration: none; color: #007bff; font-weight: 500; font-size: 16px; }" \
                    ".file-icon { margin-right: 12px; font-size: 20px; }" \
                    ".download-btn { background-color: #007bff; color: white; text-decoration: none; padding: 6px 12px; border-radius: 4px; font-size: 14px; }" \
                    ".download-btn:hover { background-color: #0056b3; }" \
                    "</style></head><body><div class='container'><header>" \
                    "<h1>⚡ Laptop Wireless Portal</h1>" \
                    "<p style='margin: 5px 0 0 0; opacity: 0.9;'>Manage files directly from your mobile device browser</p>" \
                    "</header><div class='upload-card'>" \
                    "<h3 style='margin-top:0;'>📤 Upload Files to Laptop</h3>" \
                    "<form enctype='multipart/form-data' method='post'>" \
                    "<input name='file' type='file' required style='margin-bottom: 10px; display: block;'/>" \
                    "<input class='upload-btn' type='submit' value='Upload Now'/>" \
                    "</form></div><h2>Available Files on Laptop</h2><ul class='file-list'>"

        for filename in dir_list:
            if filename.startswith('.'): continue
            fullname = os.path.join(path, filename)
            display_name = link_name = filename
            icon = "📄"
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')): icon = "🖼️"
            elif filename.lower().endswith(('.mp4', '.mkv', '.avi')): icon = "🎬"
            elif filename.lower().endswith(('.mp3', '.wav', '.flac')): icon = "🎵"
            elif filename.lower().endswith('.pdf'): icon = "📕"
            elif os.path.isdir(fullname):
                icon = "📁"
                display_name = filename + "/"
                link_name = filename + "/"

            html_head += f"""
                <li class="file-item">
                    <a class="file-info" href="{html.escape(link_name)}">
                        <span class="file-icon">{icon}</span>
                        <span>{html.escape(display_name)}</span>
                    </a>
                    <a class="download-btn" href="{html.escape(link_name)}" download>Download</a>
                </li>
            """
            
        html_head += "</ul></div></body></html>"
        encoded = html_head.encode('utf-8', 'surrogateescape')
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return BytesIO(encoded)

    def do_POST(self):
        """Processes binary file buffers uploaded from your mobile phone web interface."""
        try:
            content_type = self.headers.get('Content-Type')
            if not content_type or 'multipart/form-data' not in content_type:
                self.send_error(400, "Bad Request")
                return
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            headers_payload = f"Content-Type: {content_type}\r\n\r\n".encode('utf-8')
            parsed_message = BytesParser(policy=default).parsebytes(headers_payload + body_bytes)

            file_saved = False
            for part in parsed_message.iter_parts():
                filename = part.get_filename()
                if filename and part.get_param('name') == 'file':
                    fn = os.path.basename(filename)
                    out_path = os.path.join(SHARED_DIR, fn)
                    file_payload = part.get_payload(decode=True)
                    with open(out_path, 'wb') as fout:
                        fout.write(file_payload)
                    file_saved = True
                    break
            if file_saved:
                self.send_response(303)
                self.send_header('Location', self.path)
                self.end_headers()
            else:
                self.send_error(400, "No file found")
        except Exception as e:
            self.send_error(500, f"Server Error: {e}")

# ==============================================================================
# 6. KIVY APPLICATION INTERFACE WINDOW
# ==============================================================================
class DesktopFileSharingApp(App):
    def build(self):
        os.makedirs(SHARED_DIR, exist_ok=True)
        self.title = "Wireless Portal Server"
        
        # Configure application window icon hooks
        if os.path.exists("app_icon.ico"):
            self.icon = "app_icon.ico"
            
        self.ip_address = self.get_wired_ip()
        
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        self.title_label = Label(text="⚡ Desktop Wireless Portal Server ⚡", font_size='22sp', bold=True, size_hint_y=0.2)
        self.info_label = Label(
            text=f"Server Live!\n\n👉 Open your mobile browser and type:\nhttp://{self.ip_address}:{PORT}\n\n📁 Shared Folder Path:\n{SHARED_DIR}",
            font_size='16sp', halign='center'
        )
        layout.add_widget(self.title_label)
        layout.add_widget(self.info_label)
        
        # Boot the HTTP listener engine in a safe background processing thread
        Thread(target=self.run_server, daemon=True).start()
        return layout

    def get_wired_ip(self):
        """Detects the laptop's active physical wired LAN IP address safely."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    def run_server(self):
        TCPServer.allow_reuse_address = True
        with TCPServer(("0.0.0.0", PORT), DesktopShareHandler) as httpd:
            httpd.serve_forever()

if __name__ == '__main__':
    DesktopFileSharingApp().run()
