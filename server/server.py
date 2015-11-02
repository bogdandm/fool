# -*- coding: utf-8 -*-
import time
import random
import hashlib
from re import search

import gevent
from gevent.queue import Queue
from flask import Flask, Response, make_response, request, redirect

import server.const as const
from server.server_classes import RoomPvE, ServerCache, Session
from server.database import DB


# TODO: проверка сессий
# TODO: write session documentation
class Server:
	def __init__(self):
		self.game = None
		self.ai = None
		self.app = Flask(__name__)
		self.cache = ServerCache(const.STATIC_FOLDER, const.SERVER_FOLDER)
		res = DB.get_sessions()
		self.sessions = dict()
		if res is not None:
			for row in res:
				self.sessions[row[1]] = Session(*row)
		self.rooms = dict()

		@self.app.route('/static_/svg/<path:path>')
		def send_static_file(path):
			response = make_response(self.cache.get(const.SERVER_FOLDER + const.STATIC_FOLDER + '/svg/' + path))
			if search('^.*\.html$', path):
				response.headers["Content-type"] = "text/html"
			elif search('^.*\.css$', path):
				response.headers["Content-type"] = "text/css"
			elif search('^.*\.js$', path):
				response.headers["Content-type"] = "text/javascript"
			elif search('^.*\.svg', path):
				response.headers["Content-type"] = "image/svg+xml"
			return response

		@self.app.route('/')
		def send_root():
			return redirect('/static/arena.html')

		@self.app.route('/api')
		def send_api_methods():
			return redirect('/static/api_methods.html')  # TODO: rewrite documentation

		@self.app.route("/api/subscribe")
		def subscribe():  # Create queue for updates from server
			def gen(sess_id):
				q = MyQueue()
				session = self.sessions[sess_id]
				session['msg_queue'] = q

				def notify():
					q.put('init')

				gevent.spawn(notify)

				try:
					while True:  # MainLoop for SSE, use threads
						result = q.get()
						if not q.stopped:
							ev = ServerSentEvent(str(result))
							yield ev.encode()
						else:
							break
				except:  # Or maybe use flask signals
					del session['msg_queue']
				finally:
					del session['msg_queue']

			return Response(gen(request.cookies['sessID']), mimetype="text/event-stream")

		@self.app.route("/api/unsubscribe")
		def unsubscribe():
			session = self.sessions[request.cookies['sessID']]
			session['msg_queue'].stopped = True

			def notify():
				session['msg_queue'].put('stop')

			gevent.spawn(notify)
			return 'OK'

		@self.app.route("/api/join")
		def join_room():
			mode = int(request.args['mode'])
			session = self.sessions[request.cookies['sessID']]
			if mode == const.MODE_PVE:
				room = RoomPvE(session)
				self.rooms[room.id] = room
				session['cur_room'] = room
				session['player_n'] = const.PLAYER_HAND
				room.send_changes()
				return 'OK'
			elif mode == const.MODE_PVP:
				pass  # TODO

		@self.app.route("/api/leave")
		def leave_room():
			session = self.sessions[request.cookies['sessID']]
			room = session['cur_room']
			room_id = room.id
			if room.type == const.MODE_PVE:
				del self.rooms[room_id]
				del session['cur_room']
				return 'OK'
			elif room.type == const.MODE_PVP:
				pass  # TODO

		@self.app.route("/api/attack")
		def attack():
			session = self.sessions[request.cookies['sessID']]
			room = session['cur_room']
			card = int(request.args['card'])
			return room.attack(session['player_n'], card)

		@self.app.route("/api/defense")
		def defense():
			session = self.sessions[request.cookies['sessID']]
			room = session['cur_room']
			card = int(request.args['card'])
			return room.defense(session['player_n'], card)

		@self.app.route("/api/check_user", methods=['POST'])
		def check_user():
			password = request.form.get('pass')
			sha256 = hashlib.sha256(bytes(password, encoding='utf-8')).hexdigest() if password is not None else None

			(result, uid) = DB.check_user(request.form.get('user_name'), sha256)
			response = make_response(result.__str__())
			response.headers["Content-type"] = "text/plain"
			return response

		@self.app.route("/api/add_user", methods=['POST'])
		def add_user():
			password = request.form.get('pass')
			sha256 = hashlib.sha256(bytes(password, encoding='utf-8')).hexdigest() if password is not None else None

			result = DB.add_user(request.form.get('user_name'), sha256)
			if result == 'OK':
				redirect('menu.html')
			else:
				redirect('')  # TODO

		@self.app.route("/api/init_session", methods=['POST'])  # -> bool
		def init_session():
			if 'sessID' in request.cookies and request.cookies['sessID'] in self.sessions:
				response = make_response('OK')
				response.headers["Content-type"] = "text/plain"
				return response
			user_name = request.form.get('user_name')
			password = request.form.get('pass')
			sha256 = hashlib.sha256(bytes(password, encoding='utf-8')).hexdigest() if password is not None else None
			(result, uid) = DB.check_user(request.form.get('user_name'), sha256)
			if result:
				s = Session(user_name)
				self.sessions[s.get_id()] = s
				DB.add_session(s, uid)

				response = make_response('True')
				response.headers["Content-type"] = "text/plain"
				s.add_cookie_to_resp(response)
				return response
			else:
				response = make_response('False')
				response.headers["Content-type"] = "text/plain"
				return response

		# TODO: Переделать под новую архитектуру
		"""@self.app.route('/api/<path:method>')
		def send_api_response(method):
			if method == 'training/init':
				seed = 369942366670219  # int(time.time() * 256 * 1000)
				print(seed)
				self.game = Game(log_on=True, seed=seed)
				self.ai = AI(self.game, not self.playerHand)
				if self.game.turn != self.playerHand:
					x = self.ai.attack()
					self.game.attack(x, ai=[self.ai])

			elif method == 'training/attack':
				x = int(request.args['card'])
				self.ai.end_game_ai('U', x)
				self.game.attack(x, ai=[self.ai])
				if x == -1:
					self.game.switch_turn(ai=[self.ai])
					x = self.ai.attack()
					self.game.attack(x, ai=[self.ai])
				else:
					x = self.ai.defense(self.game.table[-1][0])
					self.game.defense(x, ai=[self.ai])
					if x == -1:
						self.game.switch_turn(ai=[self.ai])

			elif method == 'training/defense':
				x = int(request.args['card'])
				self.ai.end_game_ai('U', x)
				self.game.defense(x, ai=[self.ai])
				if x == -1:
					self.game.switch_turn(ai=[self.ai])
				x = self.ai.attack()
				self.game.attack(x, ai=[self.ai])
				if x == -1:
					self.game.switch_turn(ai=[self.ai])

			for change in self.game.changes:
				change.filter(self.playerHand)
			json = {'data': [ch.to_dict() for ch in self.game.changes]}
			self.game.changes = []
			text = jsonify(json)
			response = make_response(text)
			response.headers["Content-type"] = "text/plain"
			return response"""

	def run(self, ip):
		random.seed(int(time.time() * 256 * 1000))
		self.app.run(host=ip, debug=True, port=80)


class ServerSentEvent(object):
	def __init__(self, data):
		self.data = data
		self.event = None
		self.id = None
		self.desc_map = {
			self.data: "data",
			self.event: "event",
			self.id: "id"
		}

	def encode(self):
		if not self.data:
			return ""
		lines = ["%s: %s" % (v, k) for k, v in self.desc_map.items() if k]
		return "%s\n\n" % "\n".join(lines)


class MyQueue(Queue):
	def __init__(self, maxsize=None, items=None):
		super().__init__(maxsize, items)
		self.stopped = False
