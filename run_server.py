import socket

from gevent.wsgi import WSGIServer

from server.server import Server

if __name__ == "__main__":
	ip = socket.gethostbyname_ex(socket.gethostname())[2][0]
	flask_server = Server(ip)
	print(ip)
	server = WSGIServer((ip, 80), flask_server.app)
	server.serve_forever()
