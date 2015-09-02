from engine import *


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

	def update_memory(self, mode='all', card=None, inf=None):
		# mode=ALL|OFF|TAKE|TRUMP|TABLE

		# OFF - перед тем, как карты будут скинуту в отбой
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
		trump = self.game.trump_card
		stage = (1 - self.game.set.remain() / 39) * 100
		sums = []
		can_attack = True
		result = None
		for card in self.hand:
			sums.append((card, 0))
			if self.game.table:
				can_attack = False  # Можно ли подкинуть эту карту
				for card2 in self.game.table:
					if card.number == card2.number:
						can_attack = True
						break
			if not can_attack: continue  # Если нет, проверяем следующую
			sums[-1][1] += 27 - card.weight(self.game.trump_suit)
			# if card.number < 11 or stage > 75: # до поздней игры бережем крупные карты
			for card2 in self.hand:  # Ищем пары (тройки)
				if card.number == card2.number and card.suit != card2.suit and card2.suit != trump.suit:
					sums[-1][1] += 10
			sums[-1][1] *= (1 - self.probability(card)) / (2 - stage / 100)
			if result is None or result[1] < sums[-1][1]:
				result = sums[-1]
		return self.hand.index(result[0])

	def defense(self, card):
		return None

	def probability(self, card1):  # Вероятность побить card1
		for card in self.enemy_cards:  # Если у противника есть нужная карта, то 100%
			if card.more(card1, self.game.trump_suit):
				return 1

		yes = 0
		all = len(self.game.hand[not self.hand_number])
		enemy_cards_count = len(self.game.hand[not self.hand_number])
		for card in self.unknown_cards:
			if card.more(card1, self.game.trump_suit):
				yes += 1
		return 1 - (1 - yes / all) ** enemy_cards_count
