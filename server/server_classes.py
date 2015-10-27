import time
import random
import hashlib
from datetime import datetime, timedelta

import gevent
from flask import jsonify, Response

import server.const as const
from engine.engine import Game
from engine.ai import AI


class Session:
	def __init__(self, user, id=None):
		self.user = user
		if id is None:
			self.id = hashlib.sha256(bytes(user +
										   int(time.time() * 256 * 1000).__str__() +
										   random.randint(0, 2 ** 20).__str__(),
										   encoding='utf-8')).hexdigest()
		else:
			self.id = id
		self.data = dict()

	def add_cookie_to_resp(self, resp: Response):
		resp.set_cookie('sessID', self.id, expires=datetime.now() + timedelta(days=30))

	def get_data(self, key):
		return self.data.copy()[key]

	def set_data(self, key, value):
		self.data[key] = value

	def get_id(self) -> str:
		return self.id[:]


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
		self.type = const.MODE_PVP

	def attack(self, player, card):
		pass  # TODO

	def defense(self, player, card):
		pass  # TODO

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
		super().__init__(player, AI(self.game, not const.PLAYER_HAND))
		self.queues = [player.get_data('queue')]
		self.type = const.MODE_PVE
		if self.game.turn != const.PLAYER_HAND:
			x = self.players[1].attack()
			self.game.attack(x, ai=[self.players[1]])

	def attack(self, player, card):
		ai = self.players[not const.PLAYER_HAND]
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
		ai = self.players[not const.PLAYER_HAND]
		ai.end_game_ai('U', card)
		self.game.defense(card, ai=[ai])
		if card == -1:
			self.game.switch_turn(ai=[ai])
		x = ai.attack()
		self.game.attack(x, ai=[ai])
		if x == -1:
			self.game.switch_turn(ai=[ai])
		self.send_changes()


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
