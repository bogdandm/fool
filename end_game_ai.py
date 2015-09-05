import time
import random

from ai import Game


# Turn(self.hand_number, type='A'|'D', game=self.game, ai=self)
class Turn:
	def __init__(self, player, turn_type, card=None, prev=None, game: Game = None, ai=None):
		self.logging = prev is None
		self.ai = prev.ai if prev is not None else ai
		self.player = player
		self.type = turn_type  # A | D | T | S
		self.card = card
		self.win = 0
		self.lose = 0
		self.prev = prev
		self.next = []

		self.game = Game(game=(prev.game if (prev is not None) else game))
		self.card_str = self.game.hand[self.player][self.card] if (card is not None and card != -1) else '___'
		self.game.log_on = False

		if prev is None:
			self.next_turns()

	def __str__(self):
		return '%s %s' % (self.type, self.card_str)

	def __cmp__(self, other):
		return self.win / (self.win + self.lose) - other.win / (other.win + other.lose)

	def __eq__(self, other):
		return self.type == other.type and self.card == other.card and self.player == other.player

	def __hash__(self):
		return self.card + ord(self.type) * 100 + self.player * 10000

	def get_next(self):
		return max(self.next).card

	def get_next_by_card(self, card):
		for turn in self.next:
			if turn.card == card:
				return turn

	def next_turns(self):
		if self.game.can_play() is not None:  # Если этот ход последний, то начинаем возрат по дереву
			self.return_to_root(self.game.can_play())
			return

		if self.type == 'A':
			for i in range(len(self.game.hand[not self.player])):  # Пробуем защищаться всем подряд
				turn = Turn(not self.player, 'D', i, self)
				if turn not in self.next and turn.game.defense(i):
					self.next.append(turn)
					turn.next_turns()
				else:
					del turn

			if not self.next:
				turn = Turn(not self.player, 'T', -1, self)  # Берем, если не можем отбиться
				turn.game.defense(-1)
				turn.game.switch_turn()
				if turn not in self.next:
					self.next.append(turn)
					turn.next_turns()

		elif self.type == 'D':
			for i in range(len(self.game.hand[not self.player])):  # Атакуем всем подряд
				turn = Turn(not self.player, 'A', i, self)
				if turn not in self.next and turn.game.attack(i):
					self.next.append(turn)
					turn.next_turns()
				else:
					del turn

			turn = Turn(not self.player, 'S', -1, self)  # Так же пробуем не подкидывать
			if turn not in self.next and turn.game.attack(-1):
				turn.game.switch_turn()
				self.next.append(turn)
				turn.next_turns()
			else:
				del turn

		elif self.type == 'T':
			for i in range(len(self.game.hand[not self.player])):  # Атакуем всем подряд
				turn = Turn(not self.player, 'A', i, self)
				if turn not in self.next and turn.game.attack(i):
					self.next.append(turn)
					turn.next_turns()
				else:
					del turn

		elif self.type == 'S':
			for i in range(len(self.game.hand[not self.player])):  # Атакуем всем подряд
				turn = Turn(not self.player, 'A', i, self)
				if turn not in self.next and turn.game.attack(i):
					self.next.append(turn)
					turn.next_turns()
				else:
					del turn

	def return_to_root(self, res):
		# test=[]
		pointer = self
		win = 1 if res == self.ai.hand_number else 0
		lose = 1 if res == (not self.ai.hand_number) else 0
		while pointer is not None:
			# test.append(pointer)
			pointer.win += win
			pointer.lose += lose
			if pointer.logging and random.randint(1, 10000) == 1000:
				print(get_leaf_count(pointer))
				t=time.time()
				log = open('./logs/log %i.txt' % int(time.time() * 256 * 1000), 'w')
				M = [['\t' for g in range(get_max_length_of_chain(pointer) + 1)]
					 for i in range(get_leaf_count(pointer)) ]
				tree_to_list(pointer, M, 0, 0)
				for row in M:
					for s in row:
						log.write(s + '\t')
					log.write('\n')
				log.close()
				print((time.time()-t))
			pointer = pointer.prev


def tree_to_list(root, M, row, column):
	M[row][column] = root.__str__()
	sum = 0
	for r in root.next:
		tree_to_list(r, M, row + sum, column + 1)
		sum += get_leaf_count(r)


def get_leaf_count(root: Turn):
	res = 0
	for r in root.next:
		if len(r.next):
			res += get_leaf_count(r)
		else:
			res += 1
	if not root.next:
		res += 1
	return res


def get_max_length_of_chain(root):
	res = []
	for r in root.next:
		if len(r.next):
			res.append(get_max_length_of_chain(r) + 1)
		else:
			res.append(1)
	return max(res)
