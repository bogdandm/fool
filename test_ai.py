__author__ = 'Bogdan'
from engine import *
from ai import AI

game = Game()
ai = AI(game, 1)
while game.can_play():
	if not game.turn: # ����� �������
		game.print_state()
		i = int(input('(a) Card number (0-n): '))
		game.attack(i, ai)
		if not game.can_continue_turn(): # ���� ������ ��������, �� �� ������ ��)
			game.print_state()
			game.switch_turn(ai)
			continue
		
		game.defense(ai.defense(game.table[-1][0]))
		if not game.can_continue_turn():
			game.print_state()
			game.switch_turn(ai)
	else: # �� �������
		game.attack(ai.attack())
		if not game.can_continue_turn():
			game.print_state()
			game.switch_turn(ai)
			continue
		game.print_state()
		
		i = int(input('(d) Card number (0-n): '))
		game.defense(i, ai)
		if not game.can_continue_turn():
			game.print_state()
			game.switch_turn(ai)