import json
import logging
import socket

class TCPLogstashHandler(logging.Handler):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = None  # 초기에는 연결하지 않음

    def create_socket(self):
        if self.sock is None:
            self.sock = socket.create_connection((self.host, self.port))

    def emit(self, record):
        try:
            self.create_socket()  # emit 시점에 소켓 연결
            log_entry = self.format(record)
            self.sock.sendall((log_entry + "\n").encode('utf-8'))
        except Exception:
            self.handleError(record)

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        super().close()
