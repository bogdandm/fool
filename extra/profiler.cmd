set File=test_end_game_ai
cd ./..
python -m cProfile -o ./logs/%File%.pyprof %File%.py
python pyprof2calltree.py -i ./logs/%File%.pyprof -o ./logs/%File%.out
cd ./kcachegrind
kcachegrind.exe "./../logs/%File%.out"
exit