import random
import time
from datetime import datetime


def difference(list1, list2) -> list:
	return list(set(list1).difference(list2))


class Card:
	"""CLUBS = 1  # ♣
	SPADES = 2  # ♠
	DIAMONDS = 3  # ♦
	HEARTS = 4  # ♥

	2-10
	VALET = 11
	QUEEN = 12
	KING = 13
	ACE = 14"""

	def __init__(self, suit, card_number):
		self.suit = suit
		self.number = card_number

	def __str__(self) -> str:  # Возвращает строку вида 00X
		s = str(self.number)
		if self.suit == 1:
			s += 'C'
		elif self.suit == 2:
			s += 'S'
		elif self.suit == 3:
			s += 'D'
		elif self.suit == 4:
			s += 'H'
		return s

	def __eq__(self, other):
		return self.number == other.number and self.suit == other.suit

	def __ne__(self, other):
		return self.number != other.number or self.suit != other.suit

	def __hash__(self):
		return self.suit * 100 + self.number

	def more(self, card2, trump_card_suit) -> bool:  # Self бьет card2
		return (self.suit == card2.suit and self.number > card2.number) or \
			   (self.suit == trump_card_suit and card2.suit != trump_card_suit)

	def weight(self, trump_suit):  # Вес карты
		return self.number + (13 if self.suit == trump_suit else 0)

	def copy(self):
		return Card(self.suit, self.number)


class Set:  # Колода
	def __init__(self, set_to_copy=None, seed=None):
		random.seed(seed)
		if set_to_copy is not None:
			self.cards = set_to_copy.cards[:]
		else:
			self.cards = []
			for y in range(2, 15):
				for x in range(1, 5):
					self.cards.append(Card(x, y))
			random.shuffle(self.cards)

	def take_card(self) -> Card:  # Выдаем карту из колоды
		if not len(self.cards):
			return None
		return self.cards.pop()

	def remain(self):
		return len(self.cards)


class Game:
	def __init__(self, log_on=False, seed: int = int(time.time() * 256 * 1000), game=None):
		self.log_on = log_on
		if game is not None:
			self.set = Set(game.set)
			self.turn = game.turn
			self.hand = [game.hand[0][:], game.hand[1][:]]
			self.trump_card = None if game.trump_card is None else game.trump_card.copy()
			self.trump_suit = game.trump_suit
			self.table = []
			for tmp in game.table[:]:
				self.table.append([])
				for c in tmp:
					self.table[-1].append(None if c is None else c.copy())
			self.continue_turn = game.continue_turn
			self.result = game.result

		else:
			random.seed(seed)
			if log_on:
				self.log = open('./logs/game %s.txt' % datetime.now().strftime('%m-%d-%Y %H-%M-%S-%f'), 'w')
				self.log.write('*Start at %s*\n' % datetime.now().strftime('%H-%M-%S-%f'))
				self.log.write('seed: %i\n' % seed)
				self.log.flush()
			else:
				self.log = None

			self.set = Set(seed=seed)
			self.turn = random.randint(0, 1)
			self.hand = []  # user, AI
			self.hand.append([])
			self.hand.append([])

			for i in range(6):
				self.hand[not self.turn].append(self.set.take_card())
				self.hand[self.turn].append(self.set.take_card())
				if self.log_on:
					self.log.write('p%i: get(%s)\n' % (self.turn, self.hand[self.turn][-1]))
					self.log.write('p%i: get(%s)\n' % (not self.turn, self.hand[not self.turn][-1]))
					self.log.flush()

			self.trump_card = self.set.take_card()
			if self.log_on:
				self.log.write('__: trump_card(%s)\n' % self.trump_card)
				self.log.flush()
			self.trump_suit = self.trump_card.suit

			self.table = []
			self.continue_turn = True
			self.result = None

	def __hash__(self):
		result = 0
		offset = 0
		for i in range(len(self.hand)):
			for g in range(len(self.hand[i])):
				result += self.hand[i][g].__hash__() * 10 ** offset
				offset += 3

		for i in range(len(self.table)):
			result += self.table[i][0].__hash__() * 10 ** offset
			offset += 3
			result += self.table[i][1].__hash__() * 10 ** offset if self.table[i][0] is not None else 0
			offset += 3

		result += self.trump_suit * offset + self.turn * (offset + 1) + self.set.remain() * (offset + 2)
		return result

	def attack(self, card_number: int, ai=None) -> bool:  # Меняет состояние игры
		if not (0 <= card_number < len(self.hand[self.turn]) or card_number == -1):
			return False
		if card_number == -1:
			if self.table and self.table[-1][1] is not None:
				# Можно не атаковать если на столе есть побитая пара
				# print('skip...')
				self.continue_turn = False
				return True
			else:
				return False

		can_attack = False
		card = self.hand[self.turn][card_number]
		if not self.table:
			can_attack = True
			if ai is not None:
				if ai is not None:
					for a in ai:
						a.update_memory('TABLE', card, self.turn)
			self.table.append([card, None])
		else:  # Подкидывание
			for tmp in self.table:
				for c in tmp:
					if c and c.number == card.number:
						if ai is not None:
							for a in ai:
								a.update_memory('TABLE', card, self.turn)
						self.table.append([card, None])
						can_attack = True
						break
				if can_attack:
					break

		if can_attack:
			if self.log_on:
				self.log.write('p%i: a(%s)\n' % (self.turn, self.hand[self.turn][card_number]))
				self.log.flush()
			del self.hand[self.turn][card_number]
		return can_attack

	def defense(self, card_number: int, card_number_table: int = -1, ai=None) -> bool:  # Меняет состояние игры
		# print('Take' if card_number == -1 else self.hand[not self.turn][card_number])
		if card_number == -1:
			if self.table and self.table[-1][1] is None:
				# Можно взять карты если стол не пустой и есть не побитая карта
				self.continue_turn = False
				return True
			else:
				return False

		if not (0 <= card_number < len(self.hand[not self.turn])):
			return False

		card1 = self.hand[not self.turn][card_number]
		card2 = self.table[card_number_table][0]

		if not card1.more(card2, self.trump_suit) or card2 is None:
			return False

		if ai is not None:
			for a in ai:
				a.update_memory('TABLE', card1, not self.turn)

		self.table[card_number_table][1] = card1
		if self.log_on:
			self.log.write('p%i: d(%s)\n' % (not self.turn, self.hand[not self.turn][card_number]))
			self.log.flush()
		del self.hand[not self.turn][card_number]
		return True

	def switch_turn(self, ai=None):  # Заканчивает раунд и переключает игрока (если был отбой)
		not_take = True
		if self.table[-1][1] is None:  # Берем карты или нет
			not_take = False
			if ai is not None:
				for a in ai:
					a.update_memory('TAKE')
			for tmp in self.table:
				for c in tmp:
					if c: self.hand[not self.turn].append(c)
		else:
			if ai is not None:
				for a in ai:
					a.update_memory('OFF')
		self.table = []

		if self.set.remain() or self.trump_suit is not None:  # Если есть что взять
			for i in range(6 - len(self.hand[self.turn])):
				card = self.set.take_card()
				if card is not None:
					self.hand[self.turn].append(card)
					if ai is not None:
						for a in ai:
							if a.hand_number == self.turn:
								a.update_memory('MY', card)
					if self.log_on:
						self.log.write('p%i: get(%s)\n' % (self.turn, card))
						self.log.flush()

				elif self.trump_card is not None:
					if ai is not None:
						for a in ai:
							a.update_memory('TRUMP', inf=self.turn)
							if a.hand_number == self.turn:
								a.update_memory('MY', card)
					self.hand[self.turn].append(self.trump_card)
					if self.log_on:
						self.log.write('p%i: get(%s)\n' % (self.turn, self.trump_card))
						self.log.flush()
					self.trump_card = None

				else:
					break

			for i in range(6 - len(self.hand[not self.turn])):
				card = self.set.take_card()
				if card is not None:
					self.hand[not self.turn].append(card)
					if ai is not None:
						for a in ai:
							if a.hand_number == (not self.turn):
								a.update_memory('MY', card)
					if self.log_on:
						self.log.write('p%i: get(%s)\n' % (not self.turn, card))
						self.log.flush()

				elif self.trump_card is not None:
					if ai is not None:
						for a in ai:
							a.update_memory('TRUMP', inf=not self.turn)
							if a.hand_number == (not self.turn):
								a.update_memory('MY', card)
					self.hand[not self.turn].append(self.trump_card)
					if self.log_on:
						self.log.write('p%i: get(%s)\n' % (not self.turn, self.trump_card))
						self.log.flush()
					self.trump_card = None

				else:
					break

		if not_take:
			self.turn = not self.turn
			# print('Player switch...')
			if self.log_on:
				self.log.write('p%i: switch()\n' % self.turn)
				self.log.flush()
		else:
			# print('Take cards...')
			if self.log_on:
				self.log.write('p%i: take_cards()\n' % (not self.turn))
				self.log.flush()

	def can_continue_turn(self) -> bool:
		if not len(self.hand[self.turn]) or not len(self.hand[not self.turn]):
			# Если закончились карты
			return False
		if not self.continue_turn:
			# Если ход остановлен с помощью -1
			self.continue_turn = True
			return False

		if not self.table:
			return True

		if self.table[-1][1] is not None:
			# Можно атаковать
			for card in self.hand[self.turn]:
				for tmp in self.table:
					for c in tmp:
						if c is not None and c.number == card.number:
							return True
		else:
			# Возможно защищаться

			tmp = self.table[-1]
			for card in self.hand[not self.turn]:
				if card.more(tmp[0], self.trump_suit):
					return True
		return False

	def can_play(self) -> bool:
		l0 = len(self.hand[self.turn])
		l1 = len(self.hand[not self.turn])
		need_cards = ((6 - l0) if l0 < 6 else 0) + 1
		available_cards = self.set.remain() + (self.trump_card is not None)

		# Если на руках есть карты
		# ИЛИ
		# если у защищающегося закончились карты И в колоде достаточно карт (хотя бы 1 защищаемуся)
		# ИЛИ
		# если у атакуещего нет карт или есть что взять
		if l0 and l1 or l0 == 0 and l1 and available_cards or available_cards and need_cards <= available_cards:
			return None
		else:
			if self.log_on:
				self.log.write('*End at %s*\n' % datetime.now().strftime('%H-%M-%S-%f'))
				self.log.flush()
			if not l0 and l1:
				if self.log_on:
					self.log.write('p%i: win()\n' % self.turn)
					self.log.flush()
				self.result = self.turn
				return self.turn
			elif l0 and not l1:
				if self.log_on:
					self.log.write('p%i: win()\n' % (not self.turn))
					self.log.flush()
				self.result = int(not self.turn)
				return not self.turn
			else:
				if self.log_on:
					self.log.write('__: draw()\n')
					self.log.flush()
				self.result = -1
				return -1

	def print_state(self, player=-1):
		print('==========================')
		print('Trump card:', end='\t')
		if self.trump_suit is None:
			print('None', end='')
		else:
			print(self.trump_card, end='\t')
		print('Remaining:\t%i' % self.set.remain())

		print('\nAI %s' % ('<-' if self.turn else ''))
		if player == -1:
			for card in self.hand[not player]:
				print(card, end='  ')
		else:
			print(len(self.hand[1]))

		print('\n')
		for card in self.hand[player]:
			print(card, end='  ')
		print('\nPlayer %s' % ('<-' if not self.turn else ''))

		print('\nTable:')
		for pair in self.table:
			print(pair[0], end='\t')
		print()
		for pair in self.table:
			if pair[1]:
				print(pair[1], end='\t')
			else:
				print(end='\t')
		print('\n==========================')
