from engine import *
from ai import AI
from end_game_ai import *
import random
import time

res = []
for i in range(100):
	random.seed(i)
	g = Game(seed=i*int(time.time()))
	s = Set(seed=i*int(time.time()))
	g.set.cards = []
	g.trump_card = None
	g.trump_suit = 4
	g.hand = [
		[s.take_card() for x in range(5)],
		[s.take_card() for y in range(5)]
	]

	ai = AI(g, 0, './settings/end_game_on.xml')
	turns_tree = Turn(not 0, turn_type='D', game=g, ai=ai)
	print('%i%% (%i/%i)' % (
		turns_tree.win / (turns_tree.lose + turns_tree.win) * 100, turns_tree.win, turns_tree.lose + turns_tree.win))
	res.append(turns_tree.lose + turns_tree.win)

print(sum(res) / len(res))
