import random
import time
from datetime import datetime


def difference(list1, list2) -> list:
	return list(set(list1).difference(list2))


class Change:
	def __init__(self, type_, player, card, inf):
		self.type = type_
		self.player = player
		self.card = card
		self.inf = inf

	def __str__(self):
		return "<%s> %s: %s" % (
			self.type,
			str(self.player) if self.player is not None else '-',
			self.card if self.card is not None else
			(str(self.inf) if self.inf is not None else '-')
		)

	def __repr__(self):
		return self.__str__()

	def to_dict(self):
		return {
			'type': self.type,
			'player': self.player,
			'card': self.card,
			'inf': self.inf
		}

	def filter(self, player):
		if self.type == 'get_card' and self.player != player:
			self.card = None
		elif self.type == 'game_end':
			self.player = player
		return self

	def copy(self):
		return Change(self.type, self.player, self.card, self.inf)


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

	suits = [None, 'C', 'S', 'D', 'H']

	def __init__(self, suit, card_number):
		self.suit = suit
		self.number = card_number

	def __str__(self) -> str:  # Возвращает строку вида 00X
		return str(self.number) + self.suits[self.suit]

	def __repr__(self) -> str:
		return "'" + self.__str__() + "'"

	def __eq__(self, other):
		return self.number == other.number and self.suit == other.suit

	def __ne__(self, other):
		return self.number != other.number or self.suit != other.suit

	def __hash__(self):
		return (((self.suit - 1) << 4) | (self.number - 1)) << 1

	def more(self, card2, trump_card_suit) -> bool:  # Self бьет card2
		return (self.suit == card2.suit and self.number > card2.number) or \
			   (self.suit == trump_card_suit and card2.suit != trump_card_suit)

	def weight(self, trump_suit):  # Вес карты
		return self.number + (13 if self.suit == trump_suit else 0)

	def copy(self):
		return Card(self.suit, self.number)


class Set:  # Колода
	def __init__(self, set_to_copy=None, seed=None):
		if set_to_copy is not None:
			self.cards = []  # set_to_copy.cards[:]
		else:
			random.seed(seed)
			self.cards = [Card(suit, value) for value in range(2, 15) for suit in range(1, 5)]
			random.shuffle(self.cards)

	def take_card(self) -> Card:  # Выдаем карту из колоды
		if not self.cards:
			return None
		return self.cards.pop()

	def remain(self):
		return len(self.cards)


class Game:
	def __init__(self, save_changes=True, log_on=False, seed: int = int(time.time() * 256 * 1000), game=None):
		self.log_on = log_on
		self.save_changes = save_changes
		if game is not None:
			# Copy (not really full copy, only necessary fields are copied)
			self.set = None
			self.turn = game.turn
			self.hand = [game.hand[0][:], game.hand[1][:]]
			self.trump_card = None
			self.trump_suit = game.trump_suit
			self.table = []
			for tmp in game.table:
				self.table.append([])
				for c in tmp:
					self.table[-1].append(None if c is None else c.copy())
			self.continue_turn = game.continue_turn
			self.result = game.result

		else:
			if self.save_changes:
				self.changes = []
			random.seed(seed)
			if log_on:
				self.log = open('./engine/logs/game %s.txt' % datetime.now().strftime('%m-%d-%Y %H-%M-%S-%f'), 'w')
				self.log.write('*Start at %s*\n' % datetime.now().strftime('%H-%M-%S-%f'))
				self.log.write('seed: %s\n' % seed.__str__())
				self.log.flush()
			else:
				self.log = None

			self.set = Set(seed=seed)
			self.turn = random.randint(0, 1)
			if self.save_changes:
				self.changes.append(Change('player_switch', int(self.turn), None, None))
			self.hand = []  # user, AI
			self.hand.append([])
			self.hand.append([])

			for i in range(6):
				card = self.set.take_card()
				if self.save_changes:
					self.changes.append(Change('set_decr', None, None, None))
					self.changes.append(Change('get_card', int(not self.turn), card.__str__(), 0))
				self.hand[not self.turn].append(card)

				card = self.set.take_card()
				if self.save_changes:
					self.changes.append(Change('set_decr', None, None, None))
					self.changes.append(Change('get_card', int(self.turn), card.__str__(), 0))
				self.hand[self.turn].append(card)

				if self.log_on:
					self.log.write('p%i: get(%s)\n' % (self.turn, self.hand[self.turn][-1]))
					self.log.write('p%i: get(%s)\n' % (not self.turn, self.hand[not self.turn][-1]))
					self.log.flush()

			self.trump_card = self.set.take_card()
			if self.save_changes:
				self.changes.append(Change('set_decr', None, None, None))
				self.changes.append(Change('trump_card', None, self.trump_card.__str__(), None))
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
				result |= self.hand[i][g].__hash__() << offset
				offset += 8
			offset += 8
		offset += 8

		for i in range(len(self.table)):
			result |= self.table[i][0].__hash__() << offset
			offset += 8
			if self.table[i][1] is not None:
				result |= self.table[i][1].__hash__() << offset
			offset += 8
		# offset += 16

		result |= ((self.trump_suit - 1) << offset) | (self.turn << (offset + 2)) | (
			(self.set.remain() << (offset + 4)) if self.set is not None else 0)
		return result

	def attack(self, card_number: int, ai=None) -> bool:  # Меняет состояние игры
		# if not (0 <= card_number < len(self.hand[self.turn]) or card_number == -1):
		# 	return False

		if card_number == -1:
			if self.table and self.table[-1][1] is not None:
				# Можно не атаковать если на столе есть побитая пара
				self.continue_turn = False
				return True
			else:
				return False

		can_attack = False
		card = self.hand[self.turn][card_number]
		if not self.table:
			can_attack = True
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
			if self.save_changes:
				self.changes.append(Change('attack', int(self.turn), self.hand[self.turn][card_number].__str__(), None))
			if self.log_on:
				self.log.write('p%i: a(%s)\n' % (self.turn, self.hand[self.turn][card_number]))
				self.log.flush()
			del self.hand[self.turn][card_number]
		return can_attack

	def defense(self, card_number: int, card_number_table: int = -1, ai=None) -> bool:  # Меняет состояние игры
		if card_number == -1:
			if self.table and self.table[-1][1] is None:
				# Можно взять карты если стол не пустой и есть не побитая карта
				self.continue_turn = False
				return True
			else:
				return False

		try:
			card1 = self.hand[not self.turn][card_number]
		except KeyError:
			return False

		card2 = self.table[card_number_table][0]

		if not card1.more(card2, self.trump_suit):
			return False

		if ai is not None:
			for a in ai:
				a.update_memory('TABLE', card1, not self.turn)

		self.table[card_number_table][1] = card1
		if self.save_changes:
			self.changes.append(Change(
					'defense',
					int(not self.turn),
					self.hand[not self.turn][card_number].__str__(),
					None
			))
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
					a.update_memory('TAKE', card=-1)
			if self.save_changes:
				self.changes.append(Change('take_cards', int(not self.turn), None, None))
			if self.log_on:
				self.log.write('p%i: take_cards()\n' % (not self.turn))
				self.log.flush()
			for tmp in self.table:
				for c in tmp:
					if c is not None:
						self.hand[not self.turn].append(c)
						if self.save_changes:
							self.changes.append(Change('get_card', int(not self.turn), c.__str__(), 1))
						if self.log_on:
							self.log.write('p%i: get(%s)\n' % (not self.turn, c))
							self.log.flush()
		else:
			if ai is not None:
				for a in ai:
					a.update_memory('OFF', card=-1)
		self.table = []
		if self.save_changes:
			self.changes.append(Change('table_clear', None, None, None))

		for player in [self.turn, not self.turn]:
			if self.set is not None and self.set.remain() or self.trump_card is not None:  # Если есть что взять
				for i in range(6 - len(self.hand[player])):
					card = self.set.take_card()
					if card is not None:
						self.hand[player].append(card)
						if ai is not None:
							for a in ai:
								if a.hand_number == player:
									a.update_memory('MY', card)
						if self.save_changes:
							self.changes.append(Change('set_decr', None, None, None))
							self.changes.append(Change('get_card', int(player), card.__str__(), 0))
						if self.log_on:
							self.log.write('p%i: get(%s)\n' % (player, card))
							self.log.flush()

					elif self.trump_card is not None:
						self.hand[player].append(self.trump_card)
						if ai is not None:
							for a in ai:
								a.update_memory('TRUMP', inf=player)
								if a.hand_number == player:
									a.update_memory('MY', self.trump_card)
						if self.save_changes:
							self.changes.append(Change('get_card', int(player), self.trump_card.__str__(), 0))
							self.changes.append(Change('trump_card', None, 'None', None))
						if self.log_on:
							self.log.write('p%i: get(%s)\n' % (player, self.trump_card))
							self.log.flush()
						self.trump_card = None

					else:
						break

		if not_take:
			self.turn = not self.turn
			if self.save_changes:
				self.changes.append(Change('player_switch', int(self.turn), None, None))
			if self.log_on:
				self.log.write('p%i: switch()\n' % self.turn)
				self.log.flush()

	def can_continue_turn(self) -> bool:
		if not self.hand[self.turn] or not self.hand[not self.turn]:
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

	def can_play(self, easy=False):
		la = len(self.hand[self.turn])
		ld = len(self.hand[not self.turn])

		if not easy:
			need_cards = ((6 - la) if la < 6 else 0) + 1
			available_cards = self.set.remain() + (self.trump_card is not None)
		else:
			available_cards = need_cards = 0

		# Если на руках есть карты
		# ИЛИ
		# если у защищающегося закончились карты И в колоде достаточно карт (хотя бы 1 защищаемуся)
		# ИЛИ
		# если можно добрать из колоды
		# ИЛИ
		# если у атакуещего нет карт и на столе есть не побитые карты

		# TODO: переделать под другую механику взятия карт в конце игры
		if la and ld:
			return None
		elif not easy and (not la and ld and available_cards or
								   available_cards and need_cards <= available_cards):
			return None
		elif not la and self.table and self.table[0][0] is not None and self.table[0][1] is None:
			return None
		else:
			if self.log_on:
				self.log.write('*End at %s*\n' % datetime.now().strftime('%H-%M-%S-%f'))
				self.log.flush()
			if not la and ld:
				if self.log_on:
					self.log.write('p%i: win()\n' % self.turn)
					self.log.flush()
				if self.save_changes:
					self.changes.append(Change('game_end', None, None, self.turn))
				self.result = self.turn
				return self.turn
			elif la and not ld:
				if self.log_on:
					self.log.write('p%i: win()\n' % (not self.turn))
					self.log.flush()
				if self.save_changes:
					self.changes.append(Change('game_end', None, None, int(not self.turn)))
				self.result = int(not self.turn)
				return not self.turn
			else:
				if self.log_on:
					self.log.write('__: draw()\n')
					self.log.flush()
				if self.save_changes:
					self.changes.append(Change('game_end', None, None, -1))
				self.result = -1
				return -1

	def print_state(self, player=-1):
		s = """==========================
{trump}\tRemaining:\t{remaining}

Player 1 {turn_p1}
{cards1}

{cards2}
Player 0 {turn_p0}

Table:
{attack}
{defense}
==========================
""".format(trump=('Trump card:\t%s' % self.trump_card) if self.trump_card is not None
		else 'Trump suit:\t%s' % Card.suits[self.trump_suit],
		   remaining=self.set.remain(),
		   turn_p1='<-' if self.turn else '',
		   turn_p0='<-' if not self.turn else '',
		   cards1="\t".join(map(lambda c: c.__str__(), self.hand[1])) if player == -1 else len(self.hand[1]),
		   cards2="\t".join(map(lambda c: c.__str__(), self.hand[0])) if player == -1
		   else "\t".join(map(lambda c: c.__str__(), self.hand[player])),
		   attack="\t".join(map(lambda c: c[0].__str__(), self.table)),
		   defense="\t".join(map(lambda c: c[1].__str__() if c[1] is not None else '  ', self.table))
		   )
		print(s)
