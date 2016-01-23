from configparser import ConfigParser
from math import factorial

from engine.engine import Card, difference


class AI:
	def __init__(self, game, hand_number: int, settings_path='./engine/settings/template.ini'):
		INICONFIG = ConfigParser()
		INICONFIG.read(settings_path)
		self.settings = {group:
							 {value: float(INICONFIG[group][value]) for value in INICONFIG[group]}
						 for group in INICONFIG}

		self.game = game
		self.hand = game.hand[hand_number]
		self.hand_number = hand_number
		self.unknown_cards = set(game.set.cards[:] + self.game.hand[not hand_number])
		self.off_cards = set()
		self.enemy_cards = set()
		self.table_cards = set()

	def __str__(self):
		return 'AI'

	def update_memory(self, mode='ALL', card: Card = None, inf=None):
		# mode=ALL|OFF|TAKE|TRUMP|TABLE

		# MY
		# OFF - перед тем, как карты будут скинуты в отбой
		# TAKE  - перед тем, как игрок возьмет карты
		# TRUMP - игрок берет козырь
		# TABLE - карты кладутся на стол

		if mode == 'OFF' or mode == 'ALL':
			for tmp in self.game.table:
				self.off_cards.add(tmp[0])
				self.off_cards.add(tmp[1])
			self.table_cards.clear()

		if mode == 'TAKE' or mode == 'ALL':
			if self.game.turn == self.hand_number:
				for tmp in self.game.table:
					if tmp[0] is not None:
						self.enemy_cards.add(tmp[0])
					if tmp[1] is not None:
						self.enemy_cards.add(tmp[1])
			self.table_cards.clear()

		if mode == 'TRUMP' or mode == 'ALL':
			if inf != self.hand_number:
				self.enemy_cards.add(self.game.trump_card)

		if mode == 'TABLE' or mode == 'ALL':
			if inf != self.hand_number:
				# if self.settings['all']['enable_end_game'] and not self.game.set.remain():
				# 	if self.game.trump_card is None and self.turns_tree is not None:
				# 		self.turns_tree = self.turns_tree.get_next_by_card(card)

				for c in list(self.enemy_cards):
					if card == c:
						self.enemy_cards.remove(c)
			self.table_cards.add(card)

		self.unknown_cards = self.unknown_cards.difference(
				self.off_cards | self.enemy_cards | self.table_cards | set(self.hand))

	def attack(self):
		stage = (1 - self.game.set.remain() / 39)
		result = None
		for card in self.hand:
			current_result = [card, 0]

			can_attack = False
			if self.game.table:
				for tmp in self.game.table:
					for card2 in tmp:
						if card2 is not None and card.number == card2.number:  # Если можно подкидывать
							can_attack = True
							if card.suit == self.game.trump_suit:
								current_result[1] += self.settings['all']['trump_suit_penalty']
						if can_attack: break
					if can_attack: break

				if not can_attack:
					current_result[1] = -1000
					continue

			current_result[1] += 27 - card.weight(self.game.trump_suit)

			if not self.game.table:
				for card2 in self.hand:  # Ищем пары (тройки)
					if card != card2 and card.number == card2.number:
						if card.suit != self.game.trump_suit and card2.suit != self.game.trump_suit:
							current_result[1] += self.settings['attack']['pair_bonus']

			k = self.settings['attack']['coefficient_of_probability']
			current_result[1] *= self.probability(card) ** (2 * stage) / k + (1 - 1 / k)  # [1-1/k, 1]

			if result is None or result[1] < current_result[1]:
				result = current_result

		if result is not None:
			r = self.hand.index(result[0])
			return r if not self.game.table or result[1] > self.settings['attack']['limit'] else -1
		else:
			return -1

	def defense(self, card: Card):
		stage = (1 - self.game.set.remain() / 39) * 100
		sums = []
		result = None
		for card_ in self.hand:
			sums.append([card_, 0])

			if card_.more(card, self.game.trump_suit):
				sums[-1][1] += 27 - card_.weight(self.game.trump_suit) - (self.settings['all']['trump_suit_penalty']
																		  if card_.suit == self.game.trump_suit else 0)
				# if card.number == card_.number: sums[-1][1] += 10

				k = self.settings['defense']['coefficient_of_probability']
				k2 = self.settings['defense']['coefficient_of_stage']
				sums[-1][1] *= (1 - self.probability_throw_up(card_)) ** \
							   (stage / 100 / 2 + k2) / k + (1 - 1 / k)
			# !!! Попробовать 1 - вер-сть при битве ИИ (для надежности)
			else:
				sums[-1][1] = -1000

			if result is None or result[1] < sums[-1][1]:
				result = sums[-1]

		# for tmp in sums:
		# 	print('%s|%f' % (tmp[0], tmp[1]))
		r = self.hand.index(result[0])
		return r if (
			result[1] > self.settings['defense']['limit'] or (
				len(self.table_cards) >= self.settings['defense']['count_of_cards'] and
				result[1] > self.settings['defense']['limit2'])
		) else -1

	def probability(self, card: Card):
		"""Вероятность того, что противник НЕ сможет побить card

		return number in [0, 1]
		:param card:
		"""
		for card_ in self.enemy_cards:  # Если у противника есть нужная карта, то 0%
			if card_.more(card, self.game.trump_suit):
				return 0

		yes = 0
		total = len(self.unknown_cards)
		enemy_cards_count = len(self.game.hand[not self.hand_number])
		for card_ in self.unknown_cards:
			if card_.more(card, self.game.trump_suit):
				yes += 1

		if (total - yes) >= enemy_cards_count:
			return factorial(total - yes) * factorial(total - enemy_cards_count) / \
				   (factorial(total) * factorial(total - yes - enemy_cards_count))
		else:  # Если у противника гарантированно есть хотя бы одна нужная карта
			return 0

	def probability_throw_up(self, card: Card):
		"""Вероятность того, что при защите с помощью card НЕ будет подкинута смежная карта
		:param card:
		"""
		for card_ in self.enemy_cards:  # Если у противника есть нужная карта, то 0%
			if card_.more(card, self.game.trump_suit):
				return 1

		tmp = list(set(difference([Card(x, card.number) for x in range(1, 5)], [card])) & set(self.unknown_cards))
		# Три карты того же достоинства

		yes = len(tmp)
		total = len(self.unknown_cards)
		enemy_cards_count = len(self.game.hand[not self.hand_number])
		if (total - yes) >= enemy_cards_count:
			return 1 - (factorial(total - yes) * factorial(total - enemy_cards_count) /
						(factorial(total) * factorial(total - yes - enemy_cards_count)))
		else:
			return 1
