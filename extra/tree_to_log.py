def tree_log(root):
	import time
	print(get_leaf_count(root))
	t = time.time()
	log = open('./../logs/log %i.txt' % int(time.time() * 256 * 1000), 'w')
	M = [['-\t' for g in range(get_leaf_count(root))]
		 for i in range(get_max_length_of_chain(root) + 1)]
	tree_to_list(root, M, 0, 0)
	for i in range(len(M[0])):
		for g in range(len(M)):
			log.write(M[g][i] + '\t')
		log.write('\n')
	log.close()
	print((time.time() - t))


def tree_to_list(root, M, row, column):
	M[row][column] = root.__str__()
	sum = 0
	for r in root.next:
		tree_to_list(r, M, row + 1, column + sum)
		sum += get_leaf_count(r)


def get_leaf_count(root):
	res = 0
	for r in root.next:
		if len(r.next):
			res += get_leaf_count(r)
		else:
			res += 1
	if not root.next:
		res += 1
	return res


def get_max_length_of_chain(root):
	res = []
	for r in root.next:
		if len(r.next):
			res.append(get_max_length_of_chain(r) + 1)
		else:
			res.append(1)
	return max(res)
