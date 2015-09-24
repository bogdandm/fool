from engine.ai import AI

game = Game(True)
ai = AI(game, 1)
while game.can_play() is None:
	if not game.turn:  # Игрок атакует
		game.print_state()
		r = True
		while r:
			i = int(input('(a) Card number (1-n): '))
			r = not game.attack(i - 1 if i > 0 else -1, ai=ai)
		game.print_state()
		if not game.can_continue_turn():
			input('No choice, press Enter')
			game.switch_turn(ai)
			continue

		game.defense(ai.defense(game.table[-1][0]), ai=ai)
		if not game.can_continue_turn():
			game.print_state()
			input('No choice, press Enter')
			game.switch_turn(ai)
	else:  # ИИ атакует
		game.attack(ai.attack(), ai=ai)
		game.print_state()
		if not game.can_continue_turn():
			input('No choice, press Enter')
			game.switch_turn(ai)
			continue

		r = True
		while r:
			i = int(input('(d) Card number (1-n): '))
			# i = -1
			r = not game.defense(i - 1 if i > 0 else -1, ai=ai)
		game.print_state()
		if not game.can_continue_turn():
			input('No choice, press Enter')
			game.switch_turn(ai)

a = game.result
if a is not None:
	if a != -1:
		print('%s won!' % ('AI' if a else 'Player'))
	else:
		print('Draw')
	exit(a)