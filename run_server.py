import socket

from gevent.wsgi import WSGIServer

from server.server import Server


def get_ip():
	import subprocess
	res = subprocess.Popen("curl.exe ifconfig.co", shell=True, stdout=subprocess.PIPE).stdout.read()
	return res.decode()[:-1]


if __name__ == "__main__":
	outer_ip = get_ip()
	ip = socket.gethostbyname_ex(socket.gethostname())[2][0]
	flask_server = Server(ip, outer_ip)
	print(ip)
	print(outer_ip)
	server = WSGIServer((ip, 80), flask_server.app)
	server.serve_forever()
