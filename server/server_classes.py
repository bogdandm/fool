import time
import random
import hashlib
import json
from datetime import datetime, timedelta

import gevent
from flask import Response

import server.const as const
from engine.engine import Game
from engine.ai import AI


class Session:
	def __init__(self, user, id_=None, dict_data: dict=None):
		self.user = user
		if id_ is None:
			self.id = hashlib.sha256(bytes(
				user + int(time.time() * 256 * 1000).__str__() + random.randint(0, 2 ** 20).__str__(),
				encoding='utf-8')
			).hexdigest()
		else:
			self.id = id_
		self.data = dict() if dict_data is None else dict_data

	def __setitem__(self, key, value):
		self.data[key] = value

	def __getitem__(self, key):
		return self.data[key]

	def __delitem__(self, key):
		del self.data[key]

	def add_cookie_to_resp(self, resp: Response):
		resp.set_cookie('sessID', self.id, expires=datetime.now() + timedelta(days=30))

	def get_data(self, key):
		return self.data[key] if key in self.data else None

	def set_data(self, key, value):
		self.data[key] = value

	def get_id(self) -> str:
		return self.id[:]


class Room:
	ids = set()

	def __init__(self, player1=None, player2=None):
		self.game = Game(seed=int(time.time() * 256 * 1000))
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
					json_dict = {'data': [ch.to_dict() for ch in changes]}
					self.game.changes = []
					text = json.dumps(json_dict)
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
		self.queues = [player1.get_data('msg_queue'), player2.get_data('msg_queue')]
		self.type = const.MODE_PVP

	def attack(self, player, card):
		pass  # TODO

	def defense(self, player, card):
		pass  # TODO

	def add_player(self, player):
		if self.players[0] is None:
			self.players[0] = player
			self.queues[0] = player.get_data('msg_queue')
		elif self.players[1] is None:
			self.players[1] = player
			self.queues[1] = player.get_data('msg_queue')
		else:
			return False
		return True

	def remove_player(self, player_n):
		self.players[player_n] = None
		pass  # TODO


class RoomPvE(Room):  # User - 0, AI - 1
	# don't have add_player method, because delete when player leave PvE room
	def __init__(self, player: Session=None):
		super().__init__(player)
		self.players[1] = AI(self.game, not const.PLAYER_HAND)
		self.queues = [player['msg_queue']]
		self.type = const.MODE_PVE
		if self.game.turn != const.PLAYER_HAND:
			x = self.players[1].attack()
			self.game.attack(x, ai=[self.players[1]])

	def attack(self, player, card):
		ai = self.players[not const.PLAYER_HAND]
		ai.end_game_ai('U', card)
		if not self.game.attack(card, ai=[ai]):
			return "Can't attack using this card"
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
		return 'OK'

	def defense(self, player, card):
		ai = self.players[not const.PLAYER_HAND]
		ai.end_game_ai('U', card)
		if not self.game.defense(card, ai=[ai]):
			return "Can't attack using this card"
		if card == -1:
			self.game.switch_turn(ai=[ai])
		x = ai.attack()
		self.game.attack(x, ai=[ai])
		if x == -1:
			self.game.switch_turn(ai=[ai])
		self.send_changes()
		return 'OK'


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
