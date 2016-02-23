from os import listdir
from os.path import isfile, join, splitext

ignore = [
	'.git', 'kcachegrind', 'settings', '.idea',
	'documentation', 'extra', '__pycache__', 'unit_tests',

	'highcharts.js'
]

extensions = ['.py', '.html', '.js', '.css']


def get_files_list(l: list, path):
	for file in listdir(path):
		if file in ignore or file.find('jquery') != -1:
			continue
		path2 = join(path, file)
		if isfile(path2):
			if splitext(file)[1] in extensions:
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
# open('text.txt', 'w').write(dumps(l, separators=(', \n', ': ')))

results = {ext: 0 for ext in extensions}
results['all']=0

for file in l:
	print(file)
	filename, file_extension = splitext(file)
	n = file_len(file)
	if file_extension in results:
		results[file_extension] += n
	results['all'] += n

print(results)
