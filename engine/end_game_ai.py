# import time
# import random

from engine.engine import Game, Card


# Turn(self.hand_number, type='A'|'D', game=self.game, ai=self)
class Turn:
	def __init__(self, player, turn_type, card=None, prev=None, game: Game=None, ai=None, hashes=None):
		self.ai = prev.ai if prev is not None else ai

		self.hash = self.ai.settings['all']['hashes_in_tree']
		self.hashes = prev.hashes if prev is not None else hashes

		self.player = player
		self.type = turn_type  # A | D | T | S
		self.card = card
		self.win = 0
		self.lose = 0
		self.prev = prev
		self.next = []

		self.game = Game(save_changes=False, game=(prev.game if (prev is not None) else game))
		self.card_obj = self.game.hand[self.player][self.card] if (card is not None and card != -1) else '___'
		self.game.log_on = False

		if prev is None:
			self.next_turns()

	def __str__(self):
		return '%s%i %s' % (self.type, self.player, self.card_obj)

	def __cmp__(self, other):
		return (((self.win / (self.win + self.lose)) if self.win != 0 else 0) - (
			(other.win / (other.win + other.lose)) if other.win != 0 else 0))

	def __gt__(self, other):
		return (((self.win / (self.win + self.lose)) if self.win != 0 else 0) - (
			(other.win / (other.win + other.lose)) if other.win != 0 else 0)) > 0

	def __lt__(self, other):
		return (((self.win / (self.win + self.lose)) if self.win != 0 else 0) - (
			(other.win / (other.win + other.lose)) if other.win != 0 else 0)) < 0

	def next_turns(self):
		if self.game.can_play(True) is not None:  # Если этот ход последний, то начинаем возрат по дереву
			res = self.game.can_play(True)
			turn = Turn(res, 'R', prev=self)
			self.next.append(turn)
			self.return_to_root(res)
			return

		if self.type == 'A':
			for i in range(len(self.game.hand[not self.player])):  # Пробуем защищаться всем подряд
				turn = Turn(not self.player, 'D', i, self)
				if turn.game.defense(i):
					h = turn.game.__hash__()
					if not self.hash or h not in turn.hashes:
						if self.hash: turn.hashes.add(h)
						self.next.append(turn)
						turn.next_turns()
					else:
						del turn
				else:
					del turn

			if not self.next:
				turn = Turn(not self.player, 'T', -1, self)  # Берем, если не можем отбиться
				turn.game.defense(-1)
				turn.game.switch_turn()
				h = turn.game.__hash__()
				if not self.hash or h not in turn.hashes:
					if self.hash: turn.hashes.add(h)
					self.next.append(turn)
					turn.next_turns()

		elif self.type == 'D':
			for i in range(len(self.game.hand[not self.player])):  # Атакуем всем подряд
				turn = Turn(not self.player, 'A', i, self)
				if turn.game.attack(i):
					h = turn.game.__hash__()
					if not self.hash or h not in turn.hashes:
						if self.hash: turn.hashes.add(h)
						self.next.append(turn)
						turn.next_turns()
				else:
					del turn

			turn = Turn(not self.player, 'S', -1, self)  # Так же пробуем не подкидывать
			if turn.game.attack(-1):
				turn.game.switch_turn()
				h = turn.game.__hash__()
				if not self.hash or h not in turn.hashes:
					if self.hash: turn.hashes.add(h)
					self.next.append(turn)
					turn.next_turns()
			else:
				del turn

		elif self.type == 'T':
			for i in range(len(self.game.hand[not self.player])):  # Атакуем всем подряд
				turn = Turn(not self.player, 'A', i, self)
				if turn.game.attack(i):
					h = turn.game.__hash__()
					if not self.hash or h not in turn.hashes:
						if self.hash: turn.hashes.add(h)
						self.next.append(turn)
						turn.next_turns()
				else:
					del turn

		elif self.type == 'S':
			for i in range(len(self.game.hand[not self.player])):  # Атакуем всем подряд
				turn = Turn(not self.player, 'A', i, self)
				if turn.game.attack(i):
					h = turn.game.__hash__()
					if not self.hash or h not in turn.hashes:
						if self.hash: turn.hashes.add(h)
						self.next.append(turn)
						turn.next_turns()
				else:
					del turn

		self.cleaning()

	def return_to_root(self, res):
		# test=[]
		pointer = self
		win = 1 if res == self.ai.hand_number else 0
		lose = 1 if res == (not self.ai.hand_number) else 0
		while pointer is not None:
			# test.append(pointer)
			pointer.win += win
			pointer.lose += lose
			pointer = pointer.prev
		del self.game

	def get_next(self):
		if self.next:
			if self.next[-1] is not None and self.next[-1].type != 'R':
				return self.next[-1]
			else:
				return None
		else:
			self.hashes = set()
			self.next_turns()
			return self.get_next()

	def get_next_by_card(self, card):
		if card == -1 and (self.type == 'S' or self.type == 'T'):
			return self
		for turn in self.next:
			if turn.type == 'R':
				return None
			if isinstance(card, int):
				if turn.card == card:
					return turn
				else:
					del turn
			elif isinstance(card, Card):
				if turn.card_obj == card:
					return turn
				else:
					del turn

		print('Error in get_next_by_card [%s|%s]' % (self, card))
		self.hashes = set()
		self.next_turns()
		return self.get_next_by_card(card)

	def cleaning(self):
		if self.player == self.ai.hand_number:
			return
		max = None
		trash = []
		for i in range(len(self.next)):
			if max is None or self.next[i] > self.next[max]:
				if max is not None:
					trash.append(max)
				max = i
			else:
				trash.append(i)

		trash.sort(reverse=True)
		for i in trash:
			del self.next[i]

	def delete(self):
		for g in self.next:
			g.delete()
			self.next.remove(g)
			del g
