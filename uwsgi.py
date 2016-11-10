from pathlib import Path

from werkzeug.wsgi import DispatcherMiddleware

from server.server import Server


def simple(env, resp):
	resp(b'404 Page not found', [(b'Content-Type', b'text/plain')])
	return [b'No server for this url']


route = "/fool"
path = str(Path('.').absolute())
flask_server = Server("0.0.0.0", "bogdandm.ddns.net")
flask_server.app.config["APPLICATION_ROOT"] = route
flask_server.app.wsgi_app = DispatcherMiddleware(simple, {route: flask_server.app.wsgi_app})
app = flask_server.app