import xml.dom.minidom as dom
from math import factorial

from engine import *
from end_game_ai import Turn


class AI:
	def __init__(self, game: Game, hand_number: int, settings_path='./settings/template.xml'):
		xml = dom.parse(settings_path)
		self.settings = {
			'all': {
				'trump_suit_penalty':
					int(xml.getElementsByTagName('all')[0].
						getElementsByTagName('trump_suit_penalty')[0].childNodes[0].data),
				'enable_end_game':
					int(xml.getElementsByTagName('all')[0].
						getElementsByTagName('enable_end_game')[0].childNodes[0].data),
				'hashes_in_tree':
					int(xml.getElementsByTagName('all')[0].
						getElementsByTagName('hashes_in_tree')[0].childNodes[0].data)
			},
			'attack': {
				'pair_bonus':
					int(xml.getElementsByTagName('attack')[0].
						getElementsByTagName('pair_bonus')[0].childNodes[0].data),
				'coefficient_of_probability':
					int(xml.getElementsByTagName('attack')[0].
						getElementsByTagName('coefficient_of_probability')[0].childNodes[0].data),
				'limit':
					int(xml.getElementsByTagName('attack')[0].
						getElementsByTagName('limit')[0].childNodes[0].data),
			},
			'defense': {
				'coefficient_of_probability':
					int(xml.getElementsByTagName('defense')[0].
						getElementsByTagName('coefficient_of_probability')[0].childNodes[0].data),
				'coefficient_of_stage':
					int(xml.getElementsByTagName('defense')[0].
						getElementsByTagName('coefficient_of_stage')[0].childNodes[0].data),
				'limit':
					int(xml.getElementsByTagName('defense')[0].
						getElementsByTagName('limit')[0].childNodes[0].data),
				'count_of_cards':
					int(xml.getElementsByTagName('defense')[0].
						getElementsByTagName('count_of_cards')[0].childNodes[0].data),
				'limit2':
					int(xml.getElementsByTagName('defense')[0].
						getElementsByTagName('limit2')[0].childNodes[0].data),
			}
		}

		self.game = game
		self.hand = game.hand[hand_number]
		self.hand_number = hand_number
		self.unknown_cards = game.set.cards[:] + self.game.hand[not hand_number]
		self.oof_cards = []
		self.enemy_cards = []
		self.table_cards = []
		self.turns_tree = None

	def update_memory(self, mode='all', card: Card = None, inf=None):
		# mode=ALL|OFF|TAKE|TRUMP|TABLE

		# MY
		# OFF - перед тем, как карты будут скинуты в отбой
		# TAKE  - перед тем, как игрок возьмет карты
		# TRUMP - игрок берет козырь
		# TABLE - карты кладутся на стол

		if mode == 'OFF' or mode == 'ALL':
			if self.turns_tree is not None:
				self.turns_tree = self.turns_tree.get_next_by_card(-1)

			for tmp in self.game.table:
				self.oof_cards.append(tmp[0])
				self.oof_cards.append(tmp[1])
			self.table_cards = []

		if mode == 'TAKE' or mode == 'ALL':
			if self.turns_tree is not None:
				self.turns_tree = self.turns_tree.get_next_by_card(-1)

			if self.game.turn == self.hand_number:
				for tmp in self.game.table:
					if tmp[0] is not None:
						self.enemy_cards.append(tmp[0])
					if tmp[1] is not None:
						self.enemy_cards.append(tmp[1])
			self.table_cards = []

		if mode == 'TRUMP' or mode == 'ALL':
			if inf != self.hand_number:
				self.enemy_cards.append(self.game.trump_card)

		if mode == 'TABLE' or mode == 'ALL':
			if inf != self.hand_number:
				# if self.settings['all']['enable_end_game'] and not self.game.set.remain():
				# 	if self.game.trump_card is None and self.turns_tree is not None:
				# 		self.turns_tree = self.turns_tree.get_next_by_card(card)

				for c in self.enemy_cards:
					if card == c:
						self.enemy_cards.remove(c)
			self.table_cards.append(card)

		self.unknown_cards = difference(self.unknown_cards,
										self.oof_cards + self.enemy_cards + self.table_cards + self.hand)

	def attack(self):
		if self.settings['all']['enable_end_game'] and not self.game.set.remain() and self.game.trump_card is None:
			if self.turns_tree is not None:
				return self.end_game_ai('D')
			if len(self.game.hand[0]) <= 5 and len(self.game.hand[1]) <= 5:
				if (len(self.game.hand[0]) + len(self.game.hand[1]) + len(self.game.table) * 1.5) <= 10:
					return self.end_game_ai('D')

		stage = (1 - self.game.set.remain() / 39) * 100
		sums = []
		result = None
		for card in self.hand:
			sums.append([card, 0])

			can_attack = False
			if self.game.table:
				for tmp in self.game.table:
					for card2 in tmp:
						if card2 is not None and card.number == card2.number:  # Если можно подкидывать
							can_attack = True
							if card.suit == self.game.trump_suit:
								sums[-1][1] += self.settings['all']['trump_suit_penalty']
						"""if stage < 50 and card2.weight(self.game.trump_suit) > 20:
							# В начале игры сливаем крупные карты противника
							return -1"""
						if can_attack: break
					if can_attack: break

				if not can_attack:
					sums[-1][1] = -1000
					continue

			sums[-1][1] += 27 - card.weight(self.game.trump_suit)

			# if card.number < 11 or stage > 75: # до поздней игры бережем крупные карты
			for card2 in self.hand:  # Ищем пары (тройки)
				if card != card2 and card.number == card2.number:
					if card.suit != self.game.trump_suit and card2.suit != self.game.trump_suit:
						sums[-1][1] += self.settings['attack']['pair_bonus']
					# print('pair')

			k = self.settings['attack']['coefficient_of_probability']
			sums[-1][1] *= self.probability(card) ** (2 * stage / 100) / k + (1 - 1 / k)
			# !!! Попробовать 1 - вер-сть при битве ИИ (для надежности)

			if result is None or result[1] < sums[-1][1]:
				result = sums[-1]

		# for tmp in sums:
		# 	print('%s|%f' % (tmp[0], tmp[1]))
		r = self.hand.index(result[0])
		return r if not self.game.table or result[1] > self.settings['attack']['limit'] else -1

	def defense(self, card: Card):
		if self.settings['all']['enable_end_game'] and not self.game.set.remain() and self.game.trump_card is None:
			if self.turns_tree is not None:
				return self.end_game_ai('A')
			if (len(self.game.hand[0]) + len(self.game.hand[1]) + len(self.game.table) * 1.5) <= 10:
				return self.end_game_ai('A')

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
				sums[-1][1] *= self.probability_throw_up(card_) ** \
							   (stage / 100 / 2 + self.settings['defense']['coefficient_of_stage']) / k + (1 - 1 / k)
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

	def end_game_ai(self, mode, i=None):
		# mode = 'A' | 'D' | 'U'
		if self.turns_tree is None and mode != 'U':
			print('tree_enable')
			games_hashes = set()
			self.turns_tree = Turn(not self.hand_number, turn_type=mode, game=self.game, ai=self, hashes=games_hashes)

		if mode == 'A' or mode == 'D':
			self.turns_tree = self.turns_tree.get_next()
			return self.turns_tree.card
		elif mode == 'U' and self.turns_tree is not None:
			self.turns_tree = self.turns_tree.get_next_by_card(i)
			return None

	def probability(self, card):
		# Вероятность того, что противник НЕ сможет побить card
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
		else:
			return 0

	def probability_throw_up(self, card):
		# Вероятность того, что при защите с помощью card НЕ будет подкинута смежная карта
		for card_ in self.enemy_cards:  # Если у противника есть нужная карта, то 0%
			if card_.more(card, self.game.trump_suit):
				return 0

		tmp = list(set(difference([Card(x, card.number) for x in range(1, 5)], [card])) & set(self.unknown_cards))
		# Три карты того же достоинства

		yes = len(tmp)
		total = len(self.unknown_cards)
		enemy_cards_count = len(self.game.hand[not self.hand_number])
		if (total - yes) >= enemy_cards_count:
			return factorial(total - yes) * factorial(total - enemy_cards_count) / \
				   (factorial(total) * factorial(total - yes - enemy_cards_count))
		else:
			return 0
