from engine.ai import AI
from engine.end_game_ai import *

log = open('./logs/log_5.txt', 'w')
res = []
t_ = []
for i in range(1, 100):
	seed = i * int(time.time())
	g = Game(seed=seed)
	s = Set(seed=seed)
	print('s: %i' % seed)
	g.set.cards = []
	g.trump_card = None
	g.trump_suit = 4
	g.hand = [
		[s.take_card() for x in range(3)],
		[s.take_card() for y in range(3)]
	]

	ai = AI(g, 0, './settings/end_game_on.xml')

	games_hashes = set()
	t = time.time()
	turns_tree = Turn(not g.turn, turn_type='D', game=g, ai=ai, hashes=games_hashes)
	t_.append((time.time() - t))
	res.append(turns_tree.lose + turns_tree.win)
	log.write(('%i\t%f\n' % (res[-1], t_[-1])).replace('.', ','))
	log.flush()

	print('%i%% (%i/%i), %.3f sec' % (
		turns_tree.win / (turns_tree.lose + turns_tree.win) * 100,
		turns_tree.win,
		turns_tree.lose + turns_tree.win,
		t_[-1]
	))

print('%.2f, %.2f sec per 1k el.' % (sum(res) / len(res),
									 sum([t_[i] / res[i] * 1000 for i in range(len(res))]) / len(res)))
