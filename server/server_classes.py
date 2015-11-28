import time
from random import randint
from hashlib import sha256
from json import dumps
from datetime import datetime, timedelta
from threading import Thread

import gevent
from flask import Response, Request

import server.const as const
from engine.engine import Game
from engine.ai import AI
from server.database import DB


class Session:
	def __init__(self, user, activated, id_=None, admin=False, dict_data: dict=None):
		self.user = user
		self.activated = bool(activated)
		self.admin = admin
		if id_ is None:
			self.id = sha256(bytes(
				user + int(time.time() * 256 * 1000).__str__() + randint(0, 2 ** 20).__str__(),
				encoding='utf-8'
			)).hexdigest()
		else:
			self.id = id_
		self.data = dict() if dict_data is None else dict_data

	def __setitem__(self, key, value):
		self.data[key] = value

	def __getitem__(self, key):
		return self.data[key]

	def __delitem__(self, key):
		del self.data[key]

	def __str__(self):
		return self.user

	def add_cookie_to_resp(self, resp: Response):
		resp.set_cookie('sessID', self.id, expires=datetime.now() + timedelta(days=30))

	def delete_cookie(self, resp: Response):
		resp.set_cookie('sessID', self.id, expires=datetime.now() + timedelta(days=-30))

	def get_id(self) -> str:
		return self.id

	def update_activation_status(self):
		self.activated = bool(DB.check_user(self.user)[3])


class Room:
	ids = set()

	def __init__(self, player1=None, player2=None):
		id_tmp = randint(0, 2 ** 100)
		while id_tmp in self.ids:
			id_tmp = randint(0, 2 ** 100)
		seed = int(time.time() * 256) ^ id_tmp
		seed = sha256(
			seed.to_bytes((seed.bit_length() // 8) + 1, byteorder='little')
		).hexdigest()
		# seed='315af9e74414592d4ca337ec02bb034680e380ff7b9e1a7027ecd4d6a2576d47'
		self.game = Game(seed=seed, log_on=const.ENABLE_GAME_LOGGING)
		self.players = [player1, player2]
		self.queues = []
		self.id = id_tmp
		self.ids.add(id_tmp)
		self.type = None

	def __hash__(self):
		return self.id

	def send_changes(self):
		def notify():
			for player in [0, 1]:
				if player < len(self.queues):
					changes = [change.copy() for change in self.game.changes]
					for change in changes:
						change.filter(player)
					json_dict = {'data': [ch.to_dict() for ch in changes]}
					text = dumps(json_dict)
					self.queues[:][player].put(text)
			self.game.changes = []

		gevent.spawn(notify)

	def send_player_inf(self):
		def notify():
			for player in [0, 1]:
				if player < len(self.queues):
					self.queues[:][player].put(dumps({
						'you': self.players[player].__str__(),
						'other': self.players[not player].__str__(),
						'your_hand': player
					}))

		gevent.spawn(notify)

	def send_msg(self, msg):
		def notify():
			for i in [0, 1]:
				if i < len(self.queues) and self.queues[i] is not None:
					self.queues[:][i].put(msg)

		gevent.spawn(notify)

	def attack(self, player, card):
		# abstract
		pass

	def defense(self, player, card):
		# abstract
		pass

	def is_ready(self):
		return self.players[0] is not None and self.players[1] is not None


class RoomPvP(Room):
	def __init__(self, player1: Session=None, player2: Session=None):
		super().__init__(player1, player2)
		self.queues = [player1['msg_queue'] if player1 is not None else None,
					   player2['msg_queue'] if player2 is not None else None]
		self.type = const.MODE_PVP

	def attack(self, player, card):
		if player != self.game.turn:
			return "You can't attack now"
		if not self.game.attack(card):
			return "Can't attack using this card"
		if card == -1:
			self.game.switch_turn()

		if not self.game.can_continue_turn() and self.game.can_play() is not None:
			self.send_changes()
			return 'END'
		# wait for defense or attack
		self.send_changes()
		self.send_msg(dumps({
			'data': [{
				'type': 'wait',
				'player': 1 - player,
				'card': None,
				'inf': None
			}]
		}))
		return 'OK'

	def defense(self, player, card):
		if player == self.game.turn:
			return "You can't defense now"
		if not self.game.defense(card):
			return "Can't defense using this card"
		if card == -1:
			self.game.switch_turn()

		if not self.game.can_continue_turn() and self.game.can_play() is not None:
			self.send_changes()
			return 'END'
		# wait for attack
		self.send_changes()
		self.send_msg(dumps({
			'data': [{
				'type': 'wait',
				'player': self.game.turn,
				'card': None,
				'inf': None
			}]
		}))
		return 'OK'

	def add_player(self, player):
		if self.players[0] is None:
			self.players[0] = player
			self.queues[0] = player['msg_queue']
			return 0
		elif self.players[1] is None:
			self.players[1] = player
			self.queues[1] = player['msg_queue']
			return 1
		else:
			return -1

	def remove_player(self, player_n):
		self.players[player_n] = None
		self.queues[player_n] = None
		self.send_msg('wait')
		seed = int(time.time() * 256) ^ self.id + randint(1, 100)
		self.game = Game(seed=sha256(
			seed.to_bytes((seed.bit_length() // 8) + 1, byteorder='little')
		).hexdigest())


class RoomPvE(Room):  # User - 0, AI - 1
	# don't have add_player method, because delete when player leave PvE room
	def __init__(self, player: Session):
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
			if self.game.can_play() is not None:
				self.send_changes()
				return 'END'

			x = ai.attack()
			self.game.attack(x, ai=[ai])
			if self.game.can_play() is not None:
				self.send_changes()
				return 'END'
		else:
			if self.game.can_play() is not None:
				self.send_changes()
				return 'END'

			x = ai.defense(self.game.table[-1][0])
			self.game.defense(x, ai=[ai])
			if x == -1:
				self.game.switch_turn(ai=[ai])
			if self.game.can_play() is not None:
				self.send_changes()
				return 'END'
		self.send_changes()
		return 'OK'

	def defense(self, player, card):
		ai = self.players[not const.PLAYER_HAND]
		ai.end_game_ai('U', card)
		if not self.game.defense(card, ai=[ai]):
			return "Can't attack using this card"
		if card == -1:
			self.game.switch_turn(ai=[ai])
		if self.game.can_play() is not None:
			self.send_changes()
			return 'END'

		x = ai.attack()
		self.game.attack(x, ai=[ai])
		if self.game.can_play() is not None:
			self.send_changes()
			return 'END'

		if x == -1:
			self.game.switch_turn(ai=[ai])
		if self.game.can_play() is not None:
			self.send_changes()
			return 'END'

		self.send_changes()
		return 'OK'


class ServerCache:
	def __init__(self, static_folder, server_folder):
		self.data = dict()
		for s in ['D', 'H', 'S', 'C']:
			for v in range(2, 15):
				path = server_folder + static_folder + '/svg/' + str(v) + s + '.svg'
				self.data[path] = open(path, encoding='utf-8').read()

	def get(self, path):
		if path not in self.data:
			self.data[path] = open(path, encoding='utf-8').read()
		return self.data[path]


class Logger:
	def __init__(self, log_file=False, db_log=True):
		self.log = []
		self.time_log = []
		self.request_in_last_sec = 0
		self.log_file = open("server/log/log.txt", 'a') if log_file else None
		self.write_to_DB = db_log

		def timer_handler():
			while self.thread_run:
				self.time_log.append(self.request_in_last_sec)
				self.request_in_last_sec = 0
				if len(self.time_log) > 60 * 10:
					self.time_log = self.time_log[-60 * 5:]
				time.sleep(1)

		self.thread_run = True
		self.thread = Thread(target=timer_handler, name="RequestPerSecTimer").start()

	def write_record(self, request: Request, response: Response):
		self.request_in_last_sec += 1
		record = "{ip}\t{url}\t{method}\t{status}".format(
			ip=request.remote_addr,
			url=request.url,
			method=request.method,
			status=response.status
		)
		self.log.append(record)
		if self.log_file is not None:
			self.log_file.write(record + '\n')
			self.log_file.flush()
		if self.write_to_DB:
			DB.write_log_record(
				ip=request.remote_addr,
				url=request.url,
				method=request.method,
				status=response.status
			)
		if len(self.log) > const.LOG_MAX_LENGTH:
			self.log = self.log[-const.MAX_LOG_LENGTH_AFTER_CLEANING:]

	def write_msg(self, msg):
		if self.log_file is not None:
			self.log_file.write(msg)
			self.log_file.flush()
		if self.write_to_DB:
			DB.write_log_msg(msg)

	def stop(self):
		self.thread_run = False
