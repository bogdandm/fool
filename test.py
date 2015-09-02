from engine import *

g = Game()
while g.can_play():
	g.print_state()
	i = int(input('(a) Card number (0-n): '))
	g.attack(i)
	if not g.can_continue_turn():
		g.print_state()
		g.switch_turn()
		continue
	g.print_state()
	i = int(input('(d) Card number (0-n): '))
	j = int(input('to (0-n): '))
	g.defense(i, j)
	if not g.can_continue_turn():
		g.print_state()
		g.switch_turn()
