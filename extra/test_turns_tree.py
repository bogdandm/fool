import random
import time

from engine import *
from ai import AI
from end_game_ai import *

res = []
for i in range(1, 100):
	seed = i * int(time.time())
	g = Game(seed=seed)
	s = Set(seed=seed)
	print('s: %i' % seed)
	g.set.cards = []
	g.trump_card = None
	g.trump_suit = 4
	g.hand = [
		[s.take_card() for x in range(5)],
		[s.take_card() for y in range(5)]
	]

	ai = AI(g, 0, './settings/end_game_on.xml')
	games_hashes = []
	turns_tree = Turn(not g.turn, turn_type='D', game=g, ai=ai, hashes=games_hashes)
	# print(g.__hash__())
	print('%i%% (%i/%i)' % (
		(turns_tree.win / (turns_tree.lose + turns_tree.win)) if not (turns_tree.lose + turns_tree.win) else 0 * 100, turns_tree.win, turns_tree.lose + turns_tree.win))
	res.append(turns_tree.lose + turns_tree.win)

print(sum(res) / len(res))
