from configparser import ConfigParser


class Dummy(object):
	pass


PLAYER_HAND = 0  # use in PvE
MODE_PVE = 0
MODE_PVP = 1
MODE_FRIEND = 2
IMAGES = {'image/jpeg': '.jpg', 'image/gif': '.gif', 'image/png': '.png'}

INICONFIG = ConfigParser()
INICONFIG.read('server/configs/settings.ini')
# INICONFIG = INICONFIG['DEFAULT']

if 'SERVER_FOLDER' not in INICONFIG['DEFAULT']:
	SERVER_FOLDER = './server'
else:
	SERVER_FOLDER = INICONFIG['DEFAULT']['SERVER_FOLDER']

if 'STATIC_FOLDER' not in INICONFIG['DEFAULT']:
	STATIC_FOLDER = '/static'
else:
	STATIC_FOLDER = INICONFIG['DEFAULT']['STATIC_FOLDER']

if 'MAX_AVATAR_SIZE' not in INICONFIG['LOG']:
	MAX_AVATAR_SIZE = 200
else:
	MAX_AVATAR_SIZE = int(INICONFIG['DEFAULT']['MAX_AVATAR_SIZE'])

# ===========================================
if 'ENABLE_GAME_LOGGING' not in INICONFIG['LOG']:
	ENABLE_GAME_LOGGING = True
else:
	ENABLE_GAME_LOGGING = INICONFIG['LOG']['ENABLE_GAME_LOGGING'] == 'True'

if 'FILTRATE_REQUEST_FOR_LOG' not in INICONFIG['LOG']:
	FILTRATE_REQUEST_FOR_LOG = True
else:
	FILTRATE_REQUEST_FOR_LOG = INICONFIG['LOG']['FILTRATE_REQUEST_FOR_LOG'] == 'True'

if 'LOG_MAX_LENGTH' not in INICONFIG['LOG']:
	LOG_MAX_LENGTH = 1000
else:
	LOG_MAX_LENGTH = int(INICONFIG['LOG']['LOG_MAX_LENGTH'])

if 'MAX_LOG_LENGTH_AFTER_CLEANING' not in INICONFIG['LOG']:
	MAX_LOG_LENGTH_AFTER_CLEANING = 200
else:
	MAX_LOG_LENGTH_AFTER_CLEANING = int(INICONFIG['LOG']['MAX_LOG_LENGTH_AFTER_CLEANING'])
# ===========================================
if 'SMTPServer' not in INICONFIG['EMAIL']:
	SMTPServer = 'smtp.gmail.com'
else:
	SMTPServer = INICONFIG['EMAIL']['SMTPServer']

if 'SENDER' not in INICONFIG['EMAIL']:
	SENDER = 'smtp.gmail.com'
else:
	SENDER = INICONFIG['EMAIL']['SENDER']

if 'USERNAME' not in INICONFIG['EMAIL']:
	USERNAME = 'smtp.gmail.com'
else:
	USERNAME = INICONFIG['EMAIL']['USERNAME']

if 'PASSWORD' not in INICONFIG['EMAIL']:
	PASSWORD = 'smtp.gmail.com'
else:
	PASSWORD = INICONFIG['EMAIL']['PASSWORD']
# ===========================================
if 'USER' not in INICONFIG['DB']:
	DB_USER = 'python_flask'
else:
	DB_USER = INICONFIG['DB']['USER']

if 'PASS' not in INICONFIG['DB']:
	DB_PASS = '11061995'
else:
	DB_PASS = INICONFIG['DB']['PASS']

if 'USERNAME' not in INICONFIG['DB']:
	DB_HOST = '127.0.0.1'
else:
	DB_HOST = INICONFIG['DB']['HOST']

if 'DB' not in INICONFIG['DB']:
	DB_NAME = 'fool_db'
else:
	DB_NAME = INICONFIG['DB']['DB']

del INICONFIG
