from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import urllib.parse
import mimetypes
import pathlib
import json
from jinja2 import FileSystemLoader, Environment
from abc import ABC, abstractmethod


def format_date(data: str):
    """Format the date string to a readable format."""
    time = datetime.fromisoformat(data)
    return time.strftime("%b %d, %Y %H:%M:%S")


class Storage(ABC):
    """Abstract base class for storage management."""
    @abstractmethod
    def read_messages(self):
        pass

    @abstractmethod
    def write_message(self, new_message):
        pass


class StorageManager(Storage):
    def __init__(self, file: str):
        self.__file = pathlib.Path(file)
        self.init()

    def init(self):
        """Initialize the storage file if it does not exist."""
        if not self.__file.exists():
            try:
                with open(self.__file, "w", encoding="utf-8") as fh:
                    json.dump({}, fh, ensure_ascii=False, indent=2)
            except Exception as error:
                print(f"Error during creating a file: {error}")

    def read_messages(self):
        """Read messages from the storage file."""
        try:
            with open(self.__file, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as error:
            print(f"Error during reading a file: {error}")
            return {}

    def write_message(self, new_message):
        """Write a new message to the storage file."""
        try:
            storage = self.read_messages()
            timestamp = f"{datetime.now()}"
            storage[timestamp] = new_message
            with open(self.__file, "w", encoding="utf-8") as file:
                json.dump(storage, file, ensure_ascii=False, indent=2)
                print("Message added successfully")
        except Exception as error:
            print(f"Error during writing a file: {error}")


class HttpHandler(BaseHTTPRequestHandler):
    __storage = StorageManager("./storage/data.json")

    def do_GET(self):
        """Handle GET requests."""
        pr_url = urllib.parse.urlparse(self.path)

        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        elif pr_url.path == "/read":
            self.render_read_page()
        else:
            self.handle_404(pr_url.path)

    def do_POST(self):
        """Handle POST requests."""
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data_parsed = urllib.parse.unquote_plus(data.decode())
        message = {key: value for key, value in [el.split("=") for el in data_parsed.split("&")]}
        self.__storage.write_message(message)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html_file(self, filename, status=200):
        """Send an HTML file as a response."""
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(f"templates/{filename}", "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        """Send a static file as a response."""
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        self.send_header("Content-type", mt[0] if mt else "text/plain")
        self.end_headers()
        file_path = self.path
        if file_path.startswith('/style.css'):
            file_path = file_path.replace('/style.css', '/css/style.css')
        elif file_path.startswith('/logo.png'):
            file_path = file_path.replace('/logo.png', '/img/logo.png')
        with open(f".{file_path}", "rb") as file:
            self.wfile.write(file.read())

    def render_read_page(self):
        """Render the read page with stored messages."""
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("read.html")
        messages = self.__storage.read_messages()
        rendered = template.render(messages=messages, format_date=format_date)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(rendered.encode("utf-8"))

    def handle_404(self, path):
        """Handle 404 errors."""
        if pathlib.Path().joinpath(path[1:]).exists():
            self.send_static()
        else:
            self.send_html_file("error.html", 404)


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
