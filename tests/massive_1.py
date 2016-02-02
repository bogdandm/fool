import time
from math import sqrt

from engine.ai import AI
from engine.engine import Game

COUNT = 7500

result = [0, 0, 0, 0]
arr = []
settings = './engine/settings/3.ini'
print(settings)
for i in range(COUNT):
	seed = i * int(time.time())
	# print(seed)
	game = Game(save_changes=False, log_on=False, seed=seed)
	ai0 = AI(game, 0, settings)
	ai1 = AI(game, 1, './engine/settings/2.ini')
	t1 = time.time()
	while game.can_play() is None:
		if game.turn:
			x = ai1.attack()
			game.attack(x, ai=[ai0, ai1])
			if not game.can_continue_turn():
				game.switch_turn([ai0, ai1])
				continue

			x = ai0.defense(game.table[-1][0])
			game.defense(x, ai=[ai0, ai1])
			if not game.can_continue_turn():
				game.switch_turn([ai0, ai1])
		else:
			x = ai0.attack()
			game.attack(x, ai=[ai0, ai1])
			if not game.can_continue_turn():
				game.switch_turn([ai0, ai1])
				continue

			x = ai1.defense(game.table[-1][0])
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

		# arr.append(result[0] / (result[0] + result[1]))
		# n = len(arr)
		# print('%.4f%% s: %.2f' % (result[0] / (result[0] + result[1]),
		# 							  sqrt(sum(map(lambda x: x ** 2, arr[-500:])) / n + sum(arr[-500:]) ** 2 / n)
		# 							  ))

print('%.4f%% AI0: %i, AI1: %i, Draw: %i\nAvg. time: %i ms' % (
	result[0] / (result[0] + result[1]), result[0], result[1], result[2], result[3] / COUNT))
