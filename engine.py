import random

random.seed()


def difference(list1, list2) -> list:
	return list(set(list1).difference(list2))


class Card:
	CLUBS = 1  # ♣
	SPADES = 2  # ♠
	DIAMONDS = 3  # ♦
	HEARTS = 4  # ♥
	# 2-10
	VALET = 11
	QUEEN = 12
	KING = 13
	ACE = 14

	def __init__(self, suit, card_number, id_=-1):
		self.id = id_
		self.suit = suit
		self.number = card_number

	def print(self):
		print(self.number, end='')
		if self.suit == 1:
			print('C', end='')
		elif self.suit == 2:
			print('S', end='')
		elif self.suit == 3:
			print('D', end='')
		elif self.suit == 4:
			print('H', end='')

	def key(self) -> str:
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

	def more(self, card2, trump_card_suit) -> bool:
		return (self.suit == card2.suit and self.number > card2.number) or \
			   (self.suit == trump_card_suit and card2.suit != trump_card_suit)

	def weight(self, trump_suit):
		return self.number + (13 if self.suit == trump_suit else 0)


class Set:
	def __init__(self):
		self.cards = []
		for y in range(2, 15):
			for x in range(1, 5):
				self.cards.append(Card(x, y))
		random.shuffle(self.cards)

	def take_card(self) -> Card:
		if not len(self.cards):
			return None
		return self.cards.pop()

	def remain(self):
		return len(self.cards)


class Game:
	def __init__(self):
		self.set = Set()
		self.hand = []  # user, AI
		self.hand.append([])
		self.hand.append([])
		for i in range(6):
			self.hand[0].append(self.set.take_card())
			self.hand[1].append(self.set.take_card())
		self.trump_card = self.set.take_card()
		self.trump_suit = self.trump_card.suit
		self.turn = 1  # random.randint(0, 1)

		self.table = []

	def attack(self, card_number: int, ai=None) -> bool:
		if card_number >= len(self.hand[self.turn]):
			return False

		can_attack = False
		card = self.hand[self.turn][card_number]
		if not self.table:
			can_attack = True
			if ai is not None: ai.update_memory('TABLE', card, self.turn)
			self.table.append([card, None])
		else:
			for tmp in self.table:
				for c in tmp:
					if c and c.number == card.number:
						if ai is not None: ai.update_memory('TABLE', card, self.turn)
						self.table.append([card, None])
						can_attack = True
						break
				if can_attack:
					break
		if can_attack:
			del self.hand[self.turn][card_number]
		return can_attack

	def defense(self, card_number, card_number_table=-1, ai=None) -> bool:
		if card_number >= len(self.hand[not self.turn]):
			return False

		card1 = self.hand[not self.turn][card_number]
		card2 = self.table[card_number_table][0]

		if not card1.more(card2, self.trump_suit) or self.table[card_number_table][1] is not None or card2 is None:
			return False

		if ai is not None: ai.update_memory('TABLE', card1, not self.turn)
		self.table[card_number_table][1] = card1
		del self.hand[not self.turn][card_number]
		return True

	def switch_turn(self, ai=None):
		not_take = True
		for c_ in self.table:  # Берем карты или нет
			if c_[1] is None:
				not_take = False
				if ai is not None: ai.update_memory('TAKE')
				for tmp in self.table:
					for c in tmp:
						if c: self.hand[not self.turn].append(c)
				break
		if not_take:
			if ai is not None: ai.update_memory('OFF')
		self.table = []

		if self.set.remain():
			for i in range(6 - len(self.hand[self.turn])):
				card = self.set.take_card()
				if card is not None:
					self.hand[self.turn].append(card)
				elif self.trump_card is not None:
					if ai is not None: ai.update_memory('TRUMP', inf=self.turn)
					self.hand[self.turn].append(self.trump_card)
					self.trump_card = None
				else:
					break
			for i in range(6 - len(self.hand[not self.turn])):
				card = self.set.take_card()
				if card is not None:
					self.hand[not self.turn].append(card)
				elif self.trump_card is not None:
					if ai is not None: ai.update_memory('TRUMP', inf=not self.turn)
					self.hand[not self.turn].append(self.trump_card)
					self.trump_card = None
				else:
					break

		if not_take:
			self.turn = not self.turn
			print('Player switch...')
		else:
			print('Take cards...')

	def can_continue_turn(self) -> bool:
		result = True

		if len(self.hand[not self.turn]) == 0:
			return False

		tmp_b = False  # Можно атаковать
		for card in self.hand[self.turn]:
			for tmp in self.table:
				if tmp[1] is None: tmp_b = True
				for c in tmp:
					tmp_b = tmp_b or (c and c.number == card.number)
					if tmp_b: break
				if tmp_b: break
			if tmp_b: break
		result = result and tmp_b

		tmp_b = True  # Нужно и можно защищаться
		for tmp in self.table:
			if tmp[1] is None:
				tmp2_b = False
				for card in self.hand[not self.turn]:
					tmp2_b = tmp2_b or card.more(tmp[0], self.trump_suit)
					if tmp2_b: break
				tmp_b = tmp_b and tmp2_b
				if not tmp_b: break
		result = result and tmp_b

		return result

	def can_play(self) -> bool:
		return self.hand[0] and self.hand[1]

	def print_state(self):
		print('==========================')
		print('Trump card:', end='\t')
		if self.trump_suit is None:
			print('None', end='')
		else:
			self.trump_card.print()
		print('\tRemaining:\t%i' % self.set.remain())

		print('\nAI %s' % ('<-' if self.turn else ''))
		for card in self.hand[1]:
			card.print()
			print(end='\t')

		print('\n\n')
		for card in self.hand[0]:
			card.print()
			print(end='\t')
		print('\nPlayer %s' % ('<-' if not self.turn else ''))

		print('\nTable:')
		for pair in self.table:
			pair[0].print()
			print(end='\t')
		print()
		for pair in self.table:
			if pair[1]: pair[1].print()
			print(end='\t')
		print('\n==========================')
