# -*- coding: utf-8 -*-
import time
import random
import hashlib
from datetime import datetime, timedelta
from re import search

import gevent
from gevent.queue import Queue

from flask import Flask, make_response, request, jsonify, redirect, Response

from engine.engine import Game
from engine.ai import AI


# TODO: проверка сессий
# TODO: write session documentation
class Server:
	SERVER_FOLDER = './server'
	STATIC_FOLDER = '/static'
	PLAYER_HAND = 0  # use in PvE
	MODE_PVE = 0
	MODE_PVP = 1

	def __init__(self):
		self.game = None
		self.ai = None
		self.app = Flask(__name__)
		self.cache = ServerCache(self.STATIC_FOLDER, self.SERVER_FOLDER)
		self.sessions = dict()
		self.rooms = dict()

		@self.app.route('/static_/svg/<path:path>')
		def send_static_file(path):
			response = make_response(self.cache.get(self.SERVER_FOLDER + self.STATIC_FOLDER + '/svg/' + path))
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
			return redirect('/static/index.html')

		@self.app.route('/api')
		def send_api_methods():
			return redirect('/static/api_methods.html')  # TODO: rewrite documentation

		@self.app.route("/api/subscribe")
		def subscribe():  # Create queue for updates from server
			def gen():
				q = Queue()
				session = self.sessions[request.cookies['sessID']]
				session['msg_queue'] = q
				try:
					while True:  # MainLoop for SSE, use threads
						result = q.get()
						ev = ServerSentEvent(str(result))
						yield ev.encode()
				except GeneratorExit:  # Or maybe use flask signals
					del session['msg_queue']

			return Response(gen(), mimetype="text/event-stream")

		@self.app.route("/api/unsubscribe")
		def unsubscribe():
			session = self.sessions[request.cookies['sessID']]
			del session['msg_queue']

		@self.app.route("/api/join")
		def join_room():
			mode = request.args['mode']
			session = self.sessions[request.cookies['sessID']]
			if mode == self.MODE_PVE:
				room = RoomPvE(session)
				self.rooms[room.id](room)
				session['cur_room'] = room
				session['player_n'] = self.PLAYER_HAND
			elif mode == self.MODE_PVP:
				pass  # TODO

		@self.app.route("/api/leave")
		def leave_room():
			session = self.sessions[request.cookies['sessID']]
			room = session['cur_room']
			room_id = room.id
			if room.type == self.MODE_PVE:
				del self.rooms[room_id]
				del session['cur_room']
			elif room.type == self.MODE_PVP:
				pass  # TODO

		@self.app.route("/api/init")
		def init():
			session = self.sessions[request.cookies['sessID']]
			room = session['cur_room']
			# TODO

		@self.app.route("/api/attack")
		def attack():
			session = self.sessions[request.cookies['sessID']]
			room = session['cur_room']
			card = request.args['mode']
			room.attack(session['player_n'], card)

		@self.app.route("/api/defense")
		def defense():
			session = self.sessions[request.cookies['sessID']]
			room = session['cur_room']
			card = request.args['mode']
			room.defense(session['player_n'], card)

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


class Session:
	def __init__(self, user):
		self.user = user
		self.id = hashlib.sha256(bytes(user + int(time.time() * 256 * 1000) + random.randint(0, 2 ** 20).__str__(),
									   encoding='utf-8')).hexdigest()
		self.data = dict()

	def add_cookie_to_resp(self, resp: Response):
		resp.set_cookie('sessID', self.id, expires=datetime.now() + timedelta(days=30))

	def get_data(self, key):
		return self.data.copy()[key]

	def set_data(self, key, value):
		self.data[key] = value

	def get_id(self):
		return self.id


class Room:
	ids = set()

	def __init__(self, player1=None, player2=None):
		self.game = Game()
		self.players = [player1, player2]
		self.queues = []
		id_tmp = random.randint(0, 2 ** 100)
		while id_tmp in self.ids:
			id_tmp = random.randint(0, 2 ** 100)
		self.id = id_tmp
		self.ids.add(id_tmp)
		self.type = None

	def __hash__(self):
		return self.id

	def send_changes(self):
		def notify():
			for player in [0, 1]:
				if player < len(self.queues):
					changes = self.game.changes[:]
					for change in changes:
						change.filter(player)
					json = {'data': [ch.to_dict() for ch in changes]}
					self.game.changes = []
					text = jsonify(json)
					self.queues[:][player].put(text)
			self.game.changes = []

		gevent.spawn(notify)

	def attack(self, player, card):
		pass

	def defense(self, player, card):
		pass

	def is_ready(self):
		return self.players[0] is not None and self.players[1] is not None


class RoomPvP(Room):
	def __init__(self, player1: Session=None, player2: Session=None):
		super().__init__(player1, player2)
		self.queues = [player1.get_data('queue'), player2.get_data('queue')]
		self.type = Server.MODE_PVP

	def attack(self, player, card):
		pass

	def defense(self, player, card):
		pass

	def add_player(self, player):
		if self.players[0] is None:
			self.players[0] = player
			self.queues[0] = player.get_data('queue')
		elif self.players[1] is None:
			self.players[1] = player
			self.queues[1] = player.get_data('queue')
		else:
			return False
		return True

	def remove_player(self, player_n):
		self.players[player_n] = None


class RoomPvE(Room):  # User - 0, AI - 1
	# don't have add_player method, because delete when player leave PvE room
	def __init__(self, player: Session=None):
		super().__init__(player, AI(self.game, not Server.PLAYER_HAND))
		self.queues = [player.get_data('queue')]
		self.type = Server.MODE_PVE
		if self.game.turn != Server.PLAYER_HAND:
			x = self.players[1].attack()
			self.game.attack(x, ai=[self.players[1]])

	def attack(self, player, card):
		ai = self.players[not Server.PLAYER_HAND]
		ai.end_game_ai('U', card)
		self.game.attack(card, ai=[ai])
		if card == -1:
			self.game.switch_turn(ai=[ai])
			x = ai.attack()
			self.game.attack(x, ai=[ai])
		else:
			x = ai.defense(self.game.table[-1][0])
			self.game.defense(x, ai=[ai])
			if x == -1:
				self.game.switch_turn(ai=[ai])
		self.send_changes()

	def defense(self, player, card):
		ai = self.players[not Server.PLAYER_HAND]
		ai.end_game_ai('U', card)
		self.game.defense(card, ai=[ai])
		if card == -1:
			self.game.switch_turn(ai=[ai])
		x = ai.attack()
		self.game.attack(x, ai=[ai])
		if x == -1:
			self.game.switch_turn(ai=[ai])
		self.send_changes()


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


class ServerCache:
	def __init__(self, static_folder, server_folder):
		self.data = {}
		for s in ['D', 'H', 'S', 'C']:
			for v in range(2, 15):
				path = server_folder + static_folder + '/svg/' + str(v) + s + '.svg'
				self.data[path] = open(path, encoding='utf-8').read()

	def get(self, path):
		if path not in self.data:
			self.data[path] = open(path, encoding='utf-8').read()
		return self.data[path]
