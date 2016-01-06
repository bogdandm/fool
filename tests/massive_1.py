import time

from engine.ai import AI
from engine.engine import Game

COUNT = 100000

result = [0, 0, 0, 0]
for i in range(COUNT):
	seed = i * int(time.time())
	# print(seed)

	game = Game(save_changes=False, log_on=False, seed=seed)
	ai0 = AI(game, 0)
	ai1 = AI(game, 1)
	t1 = time.time()
	while game.can_play() is None:
		if game.turn:
			x = ai1.attack()
			ai0.end_game_ai('U', x)
			game.attack(x, ai=[ai0, ai1])
			if not game.can_continue_turn():
				game.switch_turn([ai0, ai1])
				continue

			x = ai0.defense(game.table[-1][0])
			ai1.end_game_ai('U', x)
			game.defense(x, ai=[ai0, ai1])
			if not game.can_continue_turn():
				game.switch_turn([ai0, ai1])
		else:
			x = ai0.attack()
			ai1.end_game_ai('U', x)
			game.attack(x, ai=[ai0, ai1])
			if not game.can_continue_turn():
				game.switch_turn([ai0, ai1])
				continue

			x = ai1.defense(game.table[-1][0])
			ai0.end_game_ai('U', x)
			game.defense(x, ai=[ai0, ai1])
			if not game.can_continue_turn():
				game.switch_turn([ai0, ai1])

	t2 = time.time()
	result[3] += (t2 - t1) * 1000
	a = game.result
	if a is not None:
		if a != -1:
			result[int(a)] += 1
		else:
			result[2] += 1

	# print('%.4f%%' % (result[0] / (result[0] + result[1])))

print('AI0: %i, AI1: %i, Draw: %i\nAvg. time: %i ms' % (result[0], result[1], result[2], result[3] / COUNT))
