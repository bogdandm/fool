__author__ = 'Bogdan'
import random

random.seed()


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

	def more(self, card2, trump_card) -> bool:
		return (self.suit == card2.suit and self.number > card2.number) or \
			   (self.suit == trump_card.suit and card2.suit != trump_card.suit)


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
		self.turn = random.randint(0, 1)

		self.table = []

	def attack(self, card_number: int):
		if card_number >= len(self.hand[self.turn]):
			return False

		b = False
		card = self.hand[self.turn][card_number]
		if not self.table:
			self.table.append([card, None])
		else:
			for tmp in self.table:
				for c in tmp:
					if c and c.number == card.number:
						self.table.append([card, None])
						b = True
						break
				if b:
					break
			else:
				return False
		del self.hand[self.turn][card_number]
		return True

	def defense(self, card_number, card_number_table):
		if card_number >= len(self.hand[not self.turn]):
			return False

		card1 = self.hand[not self.turn][card_number]
		card2 = self.table[card_number_table][0]

		if not card1.more(card2, self.trump_card) or \
				not (self.table[card_number_table][1] is None) or \
				not (card2 is Card):
			return False

		self.table[card_number_table][1] = card1
		del self.hand[not self.turn][card_number]
		return True

	def print_state(self):
		print('==========================')
		print('Trump card:', end='\t')
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

	def switch_turn(self):
		b = True
		for c_ in self.table:
			if c_[1] is None:
				b = False
				for tmp in self.table:
					for c in tmp:
						if c: self.hand[not self.turn].append(c)
				break
		self.table = []

		if self.set.remain():
			for i in range(6 - len(self.hand[self.turn])):
				self.hand[self.turn].append(self.set.take_card())
			for i in range(6 - len(self.hand[not self.turn])):
				self.hand[not self.turn].append(self.set.take_card())

		if b: self.turn = not self.turn
		print('Player switch...')

	def can_continue_turn(self) -> bool:
		b = True

		tmp_b = False
		for card in self.hand[self.turn]:
			for tmp in self.table:
				if tmp[1] is None: tmp_b = True
				for c in tmp:
					tmp_b = tmp_b or (c and c.number == card.number)
					if tmp_b: break
				if tmp_b: break
			if tmp_b: break
		b = b and tmp_b

		tmp_b = True
		for tmp in self.table:
			if tmp[1] is None:
				tmp2_b = False
				for card in self.hand[not self.turn]:
					tmp2_b = tmp2_b or card.more(tmp[0], self.trump_card)
					if tmp2_b: break
				tmp_b = tmp_b and tmp2_b
				if not tmp_b: break
		b = b and tmp_b

		return b

	def can_play(self) -> bool:
		return self.set and (self.hand[0] or self.hand[1])
