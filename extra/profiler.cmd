set File=test_end_game_ai
cd ./..
python -m cProfile -o ./engine/logs/%File%.pyprof test/%File%.py
python pyprof2calltree.py -i ./engine/logs/%File%.pyprof -o ./engine/logs/%File%.out
cd ./kcachegrind
kcachegrind.exe "./../engine/logs/%File%.out"
exit