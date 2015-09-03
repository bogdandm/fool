from engine import *
from math import factorial


# from copy import deepcopy


class AI:
	def __init__(self, game: Game, hand_number: int):
		self.game = game
		self.hand = game.hand[hand_number]
		self.hand_number = hand_number
		self.unknown_cards = game.set.cards[:] + self.game.hand[not hand_number]
		self.oof_cards = []
		self.enemy_cards = []
		self.table_cards = []

	def update_memory(self, mode='all', card: Card = None, inf=None):
		# mode=ALL|OFF|TAKE|TRUMP|TABLE

		# OFF - перед тем, как карты будут скинуты в отбой
		# TAKE  - перед тем, как игрок возьмет карты
		# TRUMP - игрок берет козырь
		# TABLE - карты кладутся на стол

		if mode == 'OFF' or mode == 'ALL':
			for tmp in self.game.table:
				self.oof_cards.append(tmp[0])
				self.oof_cards.append(tmp[1])

		if mode == 'TAKE' or mode == 'ALL':
			if self.game.turn == self.hand_number:
				for tmp in self.game.table:
					self.enemy_cards.append(tmp[0])
					self.enemy_cards.append(tmp[1])

		if mode == 'TRUMP' or mode == 'ALL':
			if inf != self.hand_number:
				self.enemy_cards.append(self.game.trump_card)

		if mode == 'TABLE' or mode == 'ALL':
			if inf != self.hand_number:
				for i in range(len(self.enemy_cards)):
					if card == self.enemy_cards[i]:
						del self.enemy_cards[i]
			self.table_cards.append(card)

		self.unknown_cards = difference(self.unknown_cards, self.oof_cards + self.enemy_cards + self.table_cards)

	def attack(self):
		stage = (1 - self.game.set.remain() / 39) * 100
		sums = []
		result = None
		for card in self.hand:
			sums.append([card, 0])

			if self.game.table:
				for card2 in self.game.table:
					if card.number == card2.number:  # Если можно подкидывать
						break
					if stage < 50 and card2.weight() > 20:  # В начале игры сливаем крупные карты противника
						return -1
				else:
					continue

			sums[-1][1] += 27 - card.weight(self.game.trump_suit)

			# if card.number < 11 or stage > 75: # до поздней игры бережем крупные карты
			for card2 in self.hand:  # Ищем пары (тройки)
				if card.number == card2.number and card.suit != card2.suit != self.game.trump_suit:
					sums[-1][1] += 10
					print('pair')

			k = 2
			sums[-1][1] *= (1 - self.probability(card)) ** (2 * stage / 100) / k + (1 - 1 / k)

			if result is None or result[1] < sums[-1][1]:
				result = sums[-1]

		for tmp in sums:
			print('%s|%f' % (tmp[0].key(), tmp[1]))
		r = self.hand.index(result[0])
		return r if r > 10 or not self.game.table else -1

	def defense(self, card: Card):
		stage = (1 - self.game.set.remain() / 39) * 100
		sums = []
		result = None
		for card_ in self.hand:
			sums.append([card_, 0])

			if card_.more(card, self.game.trump_suit):
				sums[-1][1] += 27 - card.weight(self.game.trump_suit)
				# if card.number == card_.number: sums[-1][1] += 10

				"""tmp = difference([Card(card_.number, x) for x in range(1, 5)], [card_])  # Три карты того же достоинства
				if not (set(tmp) & set(self.unknown_cards)):  # Карты того же достоинства найдены
					tmp2 = set(tmp) & set(self.enemy_cards)  # Карты того же достоинства у противника
					if not tmp2 and card_.weight() < 19:
						# Если это карта меньше козырной 6ки и противник не будет подкидывать
						sums[-1][1] += 20
					elif tmp2:  # Если карты противник может подкидывать
						if Card(card_.number, self.game.trump_suit) not in list(tmp2):
							# Если у противника НЕ козырь того же достоинства
							sums[-1][1] += -20
						elif set(difference(tmp, [card_, Card(card_.number, self.game.trump_suit)])) & \
								set(self.enemy_cards):
							# Если у него только козырь того же достоинства
							pass"""
				k = 2
				sums[-1][1] *= (1 - self.probability_throw_up(card)) ** (2 * stage / 100) / k + (1 - 1 / k)
			else:
				sums[1] = -1000

			if result is None or result[1] < sums[-1][1]:
				result = sums[-1]

		r = self.hand.index(result[0])
		return r if r > 10 or not self.game.table else -1

	def probability(self, card):  # Вероятность побить card1
		for card_ in self.enemy_cards:  # Если у противника есть нужная карта, то 100%
			if card_.more(card, self.game.trump_suit):
				return 1

		yes = 0
		total = len(self.unknown_cards)
		enemy_cards_count = len(self.game.hand[not self.hand_number])
		for card_ in self.unknown_cards:
			if card_.more(card, self.game.trump_suit):
				yes += 1

		return factorial(total - yes) * factorial(total - enemy_cards_count) / \
			   (factorial(total) * factorial(total - yes - enemy_cards_count))

	def probability_throw_up(self, card):
		# Вероятность того, что при защите с помощью card будет подкинута смежная карта
		for card_ in self.enemy_cards:  # Если у противника есть нужная карта, то 100%
			if card_.more(card, self.game.trump_suit):
				return 1

		tmp = difference([Card(card.number, x) for x in range(1, 5)], [card, ])  # Три карты того же достоинства
		for i in range(3):
			if tmp[i] not in self.unknown_cards:
				del tmp[i]

		yes = len(tmp)
		total = len(self.unknown_cards)
		enemy_cards_count = len(self.game.hand[not self.hand_number])
		return factorial(total - yes) * factorial(total - enemy_cards_count) / \
			   (factorial(total) * factorial(total - yes - enemy_cards_count))
