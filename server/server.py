# -*- coding: utf-8 -*-
import time
from re import search

from flask import Flask, make_response, request, jsonify

from engine.engine import Game
from engine.ai import AI


class Server:
	serverFolder = '/server'
	staticFolder = '/static'
	playerHand = 0

	def __init__(self):
		self.game = None
		self.ai = None
		self.app = Flask(__name__)

		@self.app.route('/')
		def send_root():
			response = make_response(open(
				'.' + self.serverFolder + '/index.html',
				encoding='utf-8'
			).read())
			response.headers["Content-type"] = "text/html"
			return response

		@self.app.route('/static_/<path:path>')
		def send_static_file(path):
			response = make_response(
				open('.' + self.serverFolder + self.staticFolder + '/' + path, encoding='utf-8').read())
			if search('^.*\.html$', path):
				response.headers["Content-type"] = "text/html"
			elif search('^.*\.css$', path):
				response.headers["Content-type"] = "text/css"
			elif search('^.*\.js$', path):
				response.headers["Content-type"] = "text/javascript"
			elif search('^.*\.svg', path):
				response.headers["Content-type"] = "image/svg+xml"
			return response

		@self.app.route('/api')
		def send_api_methods():
			response = make_response(
				open('.' + self.serverFolder + self.staticFolder + '/api_methods.html', encoding='utf-8').read())
			response.headers["Content-type"] = "text/html"
			return response

		@self.app.route('/api/<path:method>')
		def send_api_response(method):
			if method == 'init':
				self.game = Game(log_on=True, seed=int(time.time() * 256 * 1000))
				self.ai = AI(self.game, not self.playerHand)
				if self.game.turn != self.playerHand:
					x = self.ai.attack()
					self.game.attack(x, ai=[self.ai])

			elif method == 'attack':
				x = int(request.args('card'))
				self.ai.end_game_ai('U', x)
				self.game.attack(x, ai=[self.ai])
				if not self.game.can_continue_turn():
					self.game.switch_turn(ai=[self.ai])
				else:
					x = self.ai.defense(self.game.table[-1][0])
					self.game.defense(x, ai=[self.ai])
					if not self.game.can_continue_turn():
						self.game.switch_turn(ai=[self.ai])

			elif method == 'defense':
				x = int(request.args('card'))
				self.ai.end_game_ai('U', x)
				self.game.defense(x, ai=[self.ai])
				if not self.game.can_continue_turn():
					self.game.switch_turn(ai=[self.ai])
				else:
					x = self.ai.attack()
					self.game.attack(x, ai=[self.ai])
					if not self.game.can_continue_turn():
						self.game.switch_turn(ai=[self.ai])

			changes = self.game.changes[:]
			self.game.changes = []
			for change in changes:
				change.filter(self.playerHand)
			json = {'data': [ch.to_dict() for ch in changes]}
			text = jsonify(json)
			response = make_response(text)
			response.headers["Content-type"] = "text/plain"
			return response

	def run(self):
		self.app.run(debug=True, port=80)
