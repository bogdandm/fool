import socket

from gevent.wsgi import WSGIServer

from server.server import Server

if __name__ == "__main__":
	flask_server = Server()
	ip = socket.gethostbyname_ex(socket.gethostname())[2][0]
	print(ip)
	server = WSGIServer((ip, 80), flask_server.app)
	server.serve_forever()
