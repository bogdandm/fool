from engine import *
from ai import AI

result = [0, 0, 0]
for i in range(1000):
	seed = i * int(time.time())
	print(seed)

	game = Game(seed=seed)
	ai0 = AI(game, 0, './settings/end_game_on.xml')
	ai1 = AI(game, 1)
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

	a = game.result
	if a is not None:
		if a != -1:
			result[int(a)] += 1
			print('AI%i won!' % int(a))
		else:
			result[2] += 1
			print('Draw')
	print('==================')

print('AI0: %i, AI1: %i, Draw: %i' % (result[0], result[1], result[2]))
