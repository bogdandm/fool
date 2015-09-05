from engine import *
from ai import AI

game = Game(True)
ai0 = AI(game, 0, enable_end_game=True)
ai1 = AI(game, 1)
while game.can_play() is None:
	if game.turn:
		game.attack(ai1.attack(), ai=ai1)
		game.print_state()
		if not game.can_continue_turn():
			game.switch_turn(ai1)
			continue

		game.defense(ai0.defense(game.table[-1][0]), ai=ai0)
		if not game.can_continue_turn():
			game.print_state()
			game.switch_turn(ai0)
	else:
		game.attack(ai0.attack(), ai=ai0)
		game.print_state()
		if not game.can_continue_turn():
			game.switch_turn(ai0)
			continue

		game.defense(ai1.defense(game.table[-1][0]), ai=ai1)
		if not game.can_continue_turn():
			game.print_state()
			game.switch_turn(ai1)

a = game.result
if a is not None:
	if a != -1:
		print('AI%i won!' % int(a))
	else:
		print('Draw')
	exit(a)