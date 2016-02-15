from json import dumps
from os import listdir
from os.path import isfile, join, splitext

ignore = [
	'.git', 'kcachegrind', 'settings', 'log', 'logs', '.idea',
	'documentation', 'extra', '__pycache__', 'avatar', 'svg', 'unit_tests',

	'highcharts.js', 'text.txt'
]


def get_files_list(l: list, path):
	for file in listdir(path):
		if file in ignore or file.find('jquery') != -1 or file.find('favicon') != -1:
			continue
		path2 = join(path, file)
		if isfile(path2):
			l.append(path2)
		else:
			get_files_list(l, path2)


def file_len(fname):
	i = 0
	with open(fname, encoding='utf-8') as f:
		for i, l in enumerate(f):
			pass
	return i + 1


l = []
get_files_list(l, ".")
#open('text.txt', 'w').write(dumps(l, separators=(', \n', ': ')))

results = {
	'.py': 0,
	'.html': 0,
	'.js': 0,
	'.css': 0,
	'all': 0
}

for file in l:
	print(file)
	filename, file_extension = splitext(file)
	n = file_len(file)
	if file_extension in results:
		results[file_extension] += n
	results['all'] += n

print(results)
