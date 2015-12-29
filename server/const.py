SERVER_FOLDER = './server'
STATIC_FOLDER = '/static'

PLAYER_HAND = 0  # use in PvE
MODE_PVE = 0
MODE_PVP = 1

ENABLE_GAME_LOGGING = True
LOG_MAX_LENGTH = 1000
MAX_LOG_LENGTH_AFTER_CLEANING = 200

IMAGES = {'image/jpeg': '.jpg', 'image/gif': '.gif', 'image/png': '.png'}

FILTRATE_REQUEST_FOR_LOG = True

class Dummy(object):
	pass