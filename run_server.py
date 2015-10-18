import socket

from server.server import Server

ip = socket.gethostbyname_ex(socket.gethostname())[2][0]
Server().run(ip)
