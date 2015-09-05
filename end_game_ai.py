from copy import deepcopy

from ai import *


# Turn(self.hand_number, type='A'|'D', game=self.game, ai=self)
class Turn:
	def __init__(self, player, type, card=None, prev=None, game: Game = None, ai: AI = None):
		self.ai = prev.ai if prev is not None else ai
		self.player = player
		self.type = type  # A | D | T | S
		self.card = card
		self.win = 0
		self.lose = 0
		self.prev = prev
		self.next = []

		self.game = deepcopy(prev.game if (prev is not None) else game)
		self.game.log_on = False

	def __str__(self):
		return '<p%i: %s(%s)>' % (self.player, self.type, self.game.hand[self.player])

	def __cmp__(self, other):
		return self.win / (self.win + self.lose) - other.win / (other.win + other.lose)

	def get_next(self):
		return max(self.next).card

	def get_next_by_card(self, card):
		for turn in self.next:
			if turn.card==card:
				return turn

	def next_turns(self):
		if self.game.can_play() is not None:  # Если этот ход последний, то начинаем возрат по дереву
			self.return_to_root(self.game.can_play())
			return

		if self.type == 'A':
			for i in range(self.ai.game.hand[not self.player]):  # Пробуем защищаться всем подряд
				turn = Turn(not self.player, 'D', i, self)
				if turn.game.defense(i):
					self.next.append(turn)
					turn.next_turns()

			turn = Turn(not self.player, 'T', -1, self)  # Так же пробуем взять карты
			turn.game.defense(-1)
			turn.game.switch_turn()
			self.next.append(turn)
			turn.next_turns()

		elif self.type == 'D':
			for i in range(self.ai.game.hand[not self.player]):  # Атакуем всем подряд
				turn = Turn(not self.player, 'A', i, self)
				if turn.game.attack(i):
					self.next.append(turn)
					turn.next_turns()

			turn = Turn(not self.player, 'T', -1, self)  # Так же пробуем не подкидывать
			turn.game.attack(-1)
			turn.game.switch_turn()
			self.next.append(turn)
			turn.next_turns()

		elif self.type == 'T':
			for i in range(self.ai.game.hand[not self.player]):  # Атакуем всем подряд
				turn = Turn(self.player, 'A', i, self)
				if turn.game.attack(i):
					self.next.append(turn)
					turn.next_turns()

		elif self.type == 'S':
			for i in range(self.ai.game.hand[not self.player]):  # Атакуем всем подряд
				turn = Turn(not self.player, 'A', i, self)
				if turn.game.attack(i):
					self.next.append(turn)
					turn.next_turns()

	def return_to_root(self, res):
		pointer = self
		win = 1 if res == self.ai.hand_number else 0
		lose = 1 if res == (not self.ai.hand_number) else 0
		while pointer != None:
			pointer.win += win
			pointer.lose += lose
			pointer = pointer.prev
