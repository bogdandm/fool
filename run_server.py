import socket
import sys

from gevent.wsgi import WSGIServer

from server.server import Server


def get_argk(argv: list) -> dict:
	return dict(zip(argv[1::2], argv[2::2]))


def get_outer_ip():
	import subprocess
	res = subprocess.Popen("curl.exe ifconfig.co --connect-timeout 5",
						   shell=True, stdout=subprocess.PIPE).stdout.read()
	if not res:
		res = subprocess.Popen("curl.exe ifconfig.me --connect-timeout 5",
							   shell=True, stdout=subprocess.PIPE).stdout.read()
	return res.decode()[:-1]


if __name__ == "__main__":
	argk = get_argk(sys.argv)
	if "-l" in argk:
		ip = "0.0.0.0"
		outer_ip = "localhost"
	else:
		if "-domen" in argk:
			outer_ip = argk["-d"]
		else:
			outer_ip = get_outer_ip()
		if "-ip" in argk:
			ip = argk["-ip"]
		else:
			ip = socket.gethostbyname_ex(socket.gethostname())[2][0]
	flask_server = Server(ip, outer_ip, seed=None)
	print("http://" + ip)
	print("http://" + outer_ip)
	server = WSGIServer((ip, 80), flask_server.app)
	server.serve_forever()
