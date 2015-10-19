import socket

from gevent.wsgi import WSGIServer

from server.server import Server

if __name__ == "__main__":
	app = Server()
	ip = socket.gethostbyname_ex(socket.gethostname())[2][0]
	server = WSGIServer((ip, 80), app)
	server.serve_forever()
