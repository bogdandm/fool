# -*- coding: utf-8 -*-
import hashlib
from json import dumps
from re import search

import gevent
from flask import Flask, Response, make_response, request, redirect, render_template
from gevent.queue import Queue

import server.const as const
import server.email as email_
from server.database import DB
from server.server_classes import RoomPvE, RoomPvP, ServerCache, Session, Logger


# TODO: write session documentation
class Server:
	service_pages = [
		'\/api\/ping(\?data=[0-9]+)?$',
		'\/api\/getRequestPerSec$',
		'\/api\/get_sessions(\?(id=[0-9a-z]+|name=[a-zA-Z0-9_]+))?$',
		'\/api\/get_rooms(\?id=.+)?$'
	]

	def __init__(self, ip, domain=None):
		self.ip = ip
		self.domain = domain if domain != '' else None
		self.app = Flask(__name__)
		self.app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

		self.cache = ServerCache(const.STATIC_FOLDER, const.SERVER_FOLDER)
		res = DB.get_sessions()
		self.sessions = dict()
		self.sessions_by_user_name = dict()
		if res is not None:
			for row in res:
				s = Session(*row)
				self.sessions[row[2]] = s
				self.sessions_by_user_name[s.user] = s
		self.rooms = dict()
		self.logger = Logger()
		self.logger.write_msg('==Server run at %s==' % ip)

		@self.app.after_request
		def after_request(response):
			session = self.get_session(request)
			if session:
				session['ip'] = request.remote_addr
			if const.FILTRATE_REQUEST_FOR_LOG:
				for item in self.service_pages:
					if search(item, request.url):
						break
				else:
					self.logger.write_record(request, response)
			else:
				self.logger.write_record(request, response)
			return response

		@self.app.route('/static_/svg/<path:path>')  # static
		def send_svg(path):
			response = make_response(self.cache.get(const.SERVER_FOLDER + const.STATIC_FOLDER + '/svg/' + path))
			if search('^.*\.html$', path):
				response.headers["Content-type"] = "text/html"
			elif search('^.*\.css$', path):
				response.headers["Content-type"] = "text/css"
			elif search('^.*\.js$', path):
				response.headers["Content-type"] = "text/javascript"
			elif search('^.*\.svg', path):
				response.headers["Content-type"] = "image/svg+xml"
			return response

		@self.app.route('/')  # static
		def send_root():
			session = self.get_session(request)
			if session:
				name = session.user
				return render_template('main_menu.html', user_name=name, admin=bool(session.admin))
			elif session is None:
				return redirect('/static/login.html')
			else:
				session = self.sessions[request.cookies['sessID']]
				session.update_activation_status()
				return redirect('/static/errors/not_activated.html')

		@self.app.route('/api')  # static
		def send_api_methods():
			# TODO: rewrite documentation
			return redirect('/static/api_methods.html')

		@self.app.route('/arena')  # static; need: get@mode
		def send_arena():
			return redirect('/static/arena.html?mode=' + request.args.get('mode'))

		@self.app.route('/static/server_statistic.html')  # static
		def send_server_statistic_file():
			session = self.get_session(request)
			if session:
				if self.get_session(request).admin:
					file = open(const.SERVER_FOLDER + const.STATIC_FOLDER + '/server_statistic.html',
								encoding='utf-8').read()
					response = make_response(file)
					response.headers["Content-type"] = "text/html"
					return response
				else:
					return 'Permission denied'
			else:
				return redirect('/')

		@self.app.route('/activate_account')  # need: get@token
		def activate_account():
			token = request.args.get('token')
			if not search('^[a-zA-Z0-9]+$', token):
				return 'Bad token'
			result = DB.activate_account(token)
			if result is None:
				return 'Bad token'

			session = Session(result[0], result[3])
			self.sessions[session.get_id()] = session
			session['avatar'] = result[2]
			DB.add_session(session, result[1])

			response = redirect('/')
			session.add_cookie_to_resp(response)
			return response

		@self.app.route('/resend_email')  # need: session
		def resend_email():
			if 'sessID' in request.cookies and request.cookies['sessID'] in self.sessions:
				session = self.sessions[request.cookies['sessID']]
			else:
				return make_response('Fail', 400)
			(email, activation_token) = DB.get_email(session.user)
			email_.send_email(
				"Для подтвеждения регистрации пожалуйста перейдите по ссылке "
				"http://{domain}/activate_account?token={token}".format(
					domain=(self.domain if self.domain is not None else self.ip),
					token=activation_token
				),
				"Account activation",
				email
			)
			return 'OK'

		@self.app.route("/api/subscribe")  # need: session
		def subscribe():  # Create queue for updates from server
			def gen(sess_id):
				q = Queue()
				session = self.sessions[sess_id]
				session['msg_queue'] = q

				def notify():
					q.put('init')

				gevent.spawn(notify)

				while True:  # MainLoop for SSE, use threads
					result = q.get()
					if str(result) != 'stop':
						ev = ServerSentEvent(str(result))
						yield ev.encode()
					else:
						break
				del session['msg_queue']

			if not self.get_session(request):
				return 'Fail'
			return Response(gen(request.cookies['sessID']), mimetype="text/event-stream")

		@self.app.route("/api/unsubscribe")  # need: session@msg_queue
		def unsubscribe():
			session = self.get_session(request)
			if not session:
				return 'Fail'

			def notify():
				session['msg_queue'].put('stop')

			gevent.spawn(notify)
			return 'OK'

		@self.app.route("/api/join")  # need: session@msg_queue, get@mode
		def join_room():
			session = self.get_session(request)
			if not self.get_session(request):
				return 'Fail'

			mode = int(request.args.get('mode'))
			if mode == const.MODE_PVE:
				room = RoomPvE(session)
				self.rooms[room.id] = room
				session['cur_room'] = room
				session['player_n'] = const.PLAYER_HAND
				room.send_player_inf()
				room.send_changes()
			elif mode == const.MODE_PVP:
				for _, room in self.rooms.items():
					if room.type == const.MODE_PVP and not room.is_ready():
						break
				else:
					room = RoomPvP()
					self.rooms[room.id] = room

				session['player_n'] = room.add_player(session)
				session['cur_room'] = room
				if room.is_ready():
					room.send_player_inf()
					room.send_changes()
					room.send_msg(dumps({
						'data': [{
							'type': 'wait',
							'player': room.game.turn,
							'card': None,
							'inf': None
						}]
					}))
				else:
					room.send_msg('wait')

			return 'OK'

		@self.app.route("/api/leave")  # need: session@cur_room
		def leave_room():
			session = self.get_session(request)
			if not session:
				return 'Fail'

			room = session['cur_room']
			if room is None: return 'OK'
			room_id = room.id
			if room.type == const.MODE_PVE:
				del self.rooms[room_id]
				del session['cur_room']
				return 'OK'
			elif room.type == const.MODE_PVP:
				if room.is_ready():
					room.remove_player(session['player_n'])
					room.send_msg('wait')
				else:
					del self.rooms[room_id]
				del session['cur_room']
				return 'OK'

		@self.app.route("/api/attack")  # need: session@cur_room, get@card
		def attack():
			session = self.get_session(request)
			if not session:
				return 'Fail'

			room = session['cur_room']
			card = int(request.args.get('card'))
			result = room.attack(session['player_n'], card)
			if result == 'END':
				room_id = room.id
				if room.type == const.MODE_PVE:
					del self.rooms[room_id]
					del session['cur_room']
					return 'OK'
			return result

		@self.app.route("/api/defense", methods=['GET'])  # need: session@cur_room, get@card
		def defense():
			session = self.get_session(request)
			if not session:
				return 'Fail'

			room = session['cur_room']
			card = int(request.args.get('card'))
			result = room.defense(session['player_n'], card)
			if result == 'END':
				room_id = room.id
				if room.type == const.MODE_PVE:
					del self.rooms[room_id]
					del session['cur_room']
					return 'OK'
			return result

		@self.app.route("/api/chat", methods=['POST'])  # need: session@cur_room, post@msg
		def send_msg_to_chat():
			session = self.get_session(request)
			if not session:
				return 'Fail'

			room = session['cur_room']
			msg = request.form.get('msg')

			room.send_msg(dumps({
				'msg': msg,
				'from': session.user,
				'hand': session['player_n']
			}))

			return 'OK'

		@self.app.route("/api/check_user", methods=['POST'])  # -> bool or Error
		# (need: post@user_name; maybe: post@pass) XOR need: post@email
		def check_user():
			password = request.form.get('pass')
			sha256 = hashlib.sha256(bytes(password, encoding='utf-8')).hexdigest() if password is not None else None
			email = request.form.get('email')
			name = request.form.get('name')

			if name is not None:
				result = DB.check_user(name, sha256)[0]
				response = make_response((not result).__str__())
			elif email is not None:
				result = DB.check_email(email)
				response = make_response((not result).__str__())
			else:
				response = make_response('Bad request', 400)
			response.headers["Content-type"] = "text/plain"
			return response

		@self.app.route("/api/avatar", methods=['GET'])
		# need: get@user; maybe: get@source := menu | any
		def get_avatar():
			user = request.args.get('user')
			if user == 'AI':
				return "/static_/svg/ic_computer_24px_white.svg"
			file_ext = DB.check_user(user)[2]
			if file_ext is not None and file_ext != 'None':
				return "/static/avatar/{user_name}{file_ext}".format(user_name=user, file_ext=file_ext)
			else:
				if request.args.get('source') == 'menu':
					return "/static_/svg/ic_person_24px.svg"
				else:
					return "/static_/svg/ic_person_24px_grey_reverse.svg"

		@self.app.route("/api/add_user", methods=['POST'])
		# need: post@user_name, post@pass, post@email; maybe: post@file(image)
		def add_user():
			sha256 = hashlib.sha256(bytes(request.form.get('pass'), encoding='utf-8')).hexdigest()
			name = request.form.get('name')
			email = request.form.get('email')

			result = not DB.check_user(name)[0] and not DB.check_email(email)

			if not (search('^.+@.+\..+$', email) and search('^[a-zA-Z0-9_]+$', name) and result):
				return make_response('Wrong data', 400)

			if request.files:
				file = request.files['file']
				if file.mimetype in const.IMAGES:
					file_ext = const.IMAGES[file.mimetype]
					file.save("./server/static/avatar/{}{}".format(name, file_ext))
				else:
					return make_response('Wrong data', 400)
			else:
				file_ext = None

			(activation_token, result) = DB.add_user(name, sha256, file_ext, email)

			if result:
				response = make_response('OK')

				(result2, uid, file_ext, activated, admin) = DB.check_user(name, sha256)
				if result2:
					session = Session(name, activated)
					self.sessions[session.get_id()] = session
					session['avatar'] = file_ext
					DB.add_session(session, uid)
					session.add_cookie_to_resp(response)

					email_.send_email(
						"Для подтвеждения регистрации пожалуйста перейдите по ссылке "
						"http://{domain}/activate_account?token={token}".format(
							domain=(self.domain if self.domain is not None else self.ip),
							token=activation_token
						),
						"Account activation",
						email)
				else:
					self.logger.write_msg("Something wrong with registration ({})".format(name))

				response.headers["Content-type"] = "text/plain"
				return response
			else:
				return 'Error'

		@self.app.route("/api/init_session", methods=['POST'])
		# need: post@user_name, post@pass
		def init_session():
			if self.get_session(request) is not None:
				response = make_response('OK')
				response.headers["Content-type"] = "text/plain"
				return response

			user_name = request.form.get('user_name')
			password = request.form.get('pass')
			sha256 = hashlib.sha256(bytes(password, encoding='utf-8')).hexdigest() if password is not None else None
			(result, uid, file_ext, activated, admin) = DB.check_user(request.form.get('user_name'), sha256)
			if result:

				if user_name in self.sessions_by_user_name:
					session = self.sessions_by_user_name[user_name]
				else:
					session = Session(user_name, activated, admin=admin)
					self.sessions[session.get_id()] = session
					self.sessions_by_user_name[user_name] = session
					session['avatar'] = file_ext
					DB.add_session(session, uid)
				session['ip'] = request.remote_addr

				response = make_response('True')
				response.headers["Content-type"] = "text/plain"
				session.add_cookie_to_resp(response)
				return response
			else:
				response = make_response('False')
				response.headers["Content-type"] = "text/plain"
				return response

		@self.app.route("/api/destroy_session")
		# need: session
		def destroy_session():
			session = self.get_session(request)
			if not session:
				return 'Fail'

			response = make_response('OK')
			session.delete_cookie(response)
			DB.delete_session(session.id)
			del self.sessions_by_user_name[session.user]
			del self.sessions[session.id]
			return response

		@self.app.route('/api/ping')
		def ping():
			data = request.args.get('data')
			return data if data is not None else 'Pong'

		@self.app.route('/api/getRequestPerSec')
		def get_request_per_sec():
			session = self.get_session(request)
			if session:
				if self.get_session(request).admin:
					return self.logger.time_log[-1].__str__()
				else:
					return 'Permission denied'
			else:
				return redirect('/')

		@self.app.route('/api/get_sessions')
		def get_sessions():
			session = self.get_session(request)
			if session:
				if self.get_session(request).admin:
					result = []
					for sid, session in self.sessions.items():
						result.append(session.to_json())
					return dumps(result)
				else:
					return 'Permission denied'
			else:
				return redirect('/')

		@self.app.route('/api/get_rooms')
		def get_rooms():
			session = self.get_session(request)
			if session:
				if self.get_session(request).admin:
					result = []
					for rid, room in self.rooms.items():
						result.append(room.to_json())
					return dumps(result)
				else:
					return 'Permission denied'
			else:
				return redirect('/')

	def get_session(self, request_) -> Session:  # -> Session | False | None
		if 'sessID' in request_.cookies and request_.cookies['sessID'] in self.sessions:
			session = self.sessions[request_.cookies['sessID']]
			if session.activated:
				return session
			else:
				return False
		else:
			return None


class ServerSentEvent(object):
	def __init__(self, data):
		self.data = data
		self.event = None
		self.id = None
		self.desc_map = {
			self.data: "data",
			self.event: "event",
			self.id: "id"
		}

	def encode(self):
		if not self.data:
			return ""
		lines = ["%s: %s" % (v, k) for k, v in self.desc_map.items() if k]
		return "%s\n\n" % "\n".join(lines)
