from engine.ai import AI
from engine.engine import Game
import time

seed = int(time.time())
print(seed)

game = Game(save_changes=False, log_on=True, seed=seed)
ai0 = AI(game, 0, './engine/settings/end_game_on.xml')
ai1 = AI(game, 1)
while game.can_play() is None:
	if game.turn:
		x = ai1.attack()
		ai0.end_game_ai('U', x)
		game.attack(x, ai=[ai0, ai1])
		game.print_state()
		if not game.can_continue_turn():
			game.switch_turn([ai0, ai1])
			continue

		x = ai0.defense(game.table[-1][0])
		ai1.end_game_ai('U', x)
		game.defense(x, ai=[ai0, ai1])
		game.print_state()
		if not game.can_continue_turn():
			game.switch_turn([ai0, ai1])
	else:
		game.print_state()
		x = ai0.attack()
		ai1.end_game_ai('U', x)
		game.attack(x, ai=[ai0, ai1])
		game.print_state()
		if not game.can_continue_turn():
			game.switch_turn([ai0, ai1])
			continue

		x = ai1.defense(game.table[-1][0])
		ai0.end_game_ai('U', x)
		game.defense(x, ai=[ai0, ai1])
		if not game.can_continue_turn():
			game.print_state()
			game.switch_turn([ai0, ai1])

a = game.result
if a is not None:
	if a != -1:
		print('AI%i won!' % int(a))
	else:
		print('Draw')
	exit(a)
