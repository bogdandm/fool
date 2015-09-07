from engine import *
from ai import AI
from end_game_ai import *


def main():
	seed = 1441647431  # int(time.time())
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
	g.print_state()

	ai = AI(g, 0, './settings/end_game_on.xml')
	games_hashes = set()

	t = time.time()
	turns_tree = Turn(not g.turn, turn_type='D', game=g, ai=ai, hashes=games_hashes)
	print('%f sec' % (time.time() - t))
	# tree_log(turns_tree)

	print(g.__hash__())
	print('%i%% (%i/%i)' % (
		((turns_tree.win / (turns_tree.lose + turns_tree.win)) if (turns_tree.lose + turns_tree.win) > 0 else 0) * 100,
		turns_tree.win,
		turns_tree.lose + turns_tree.win
	))


main()
