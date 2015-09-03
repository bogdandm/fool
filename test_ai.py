__author__ = 'Bogdan'
from engine import *
from ai import AI

game = Game()
ai = AI(game, 1)
while game.can_play():
	if not game.turn:  # Игрок атакует
		game.print_state()
		r = True
		while r:
			i = int(input('(a) Card number (1-n): '))
			r = not game.attack(i - 1 if i > 0 else -1, ai=ai)
		game.print_state()
		if not game.can_continue_turn():
			input('No choice, press Enter')
			game.switch_turn(ai)
			continue

		game.defense(ai.defense(game.table[-1][0]), ai=ai)
		if not game.can_continue_turn():
			game.print_state()
			input('No choice, press Enter')
			game.switch_turn(ai)
	else:  # ИИ атакует
		game.attack(ai.attack(), ai=ai)
		game.print_state()
		if not game.can_continue_turn():
			input('No choice, press Enter')
			game.switch_turn(ai)
			continue

		r = True
		while r:
			i = int(input('(d) Card number (1-n): '))
			r = not game.defense(i - 1 if i > 0 else -1, ai=ai)
		game.print_state()
		if not game.can_continue_turn():
			input('No choice, press Enter')
			game.switch_turn(ai)
