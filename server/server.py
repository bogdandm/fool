# -*- coding: utf-8 -*-
import hashlib
from re import search
from json import dumps

import gevent
from gevent.queue import Queue
from flask import Flask, Response, make_response, request, redirect, render_template

import server.const as const
from server.server_classes import RoomPvE, RoomPvP, ServerCache, Session, Logger
from server.database import DB
import server.email as Email


# TODO: write session documentation
class Server:
	def __init__(self, ip, domain=None):
		self.ip = ip
		self.domain = domain
		self.app = Flask(__name__)
		self.app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

		self.cache = ServerCache(const.STATIC_FOLDER, const.SERVER_FOLDER)
		res = DB.get_sessions()
		self.sessions = dict()
		if res is not None:
			for row in res:
				self.sessions[row[2]] = Session(*row)
		self.rooms = dict()
		self.logger = Logger()
		self.logger.write_msg('==Server run at %s==' % ip)

		@self.app.after_request
		def after_request(response):
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
				return render_template('main_menu.html', user_name=name)
			elif session is None:
				return redirect('/static/login.html')
			else:
				session = self.sessions[request.cookies['sessID']]
				session.update_activation_status()
				return redirect('/static/errors/not_activated.html')

		@self.app.route('/api')  # static
		def send_api_methods():
			return redirect('/static/api_methods.html')  # TODO: rewrite documentation

		@self.app.route('/arena')  # need: get@mode
		def send_arena():
			return redirect('/static/arena.html?mode=' + request.args['mode'])

		@self.app.route('/activate_account')  # need: -
		def activate_account():
			token = request.args.get('token')
			if not search('^[a-zA-Z0-9]+$', token):
				return 'Bad token'
			result = DB.activate_account(token)
			if result is None:
				return 'Bad token'

			s = Session(result[0], result[3])
			self.sessions[s.get_id()] = s
			s['avatar'] = result[2]
			DB.add_session(s, result[1])

			response = redirect('/')
			s.add_cookie_to_resp(response)
			return response

		@self.app.route('/resend_email')  # need: session
		def resend_email():
			if 'sessID' in request.cookies and request.cookies['sessID'] in self.sessions:
				session = self.sessions[request.cookies['sessID']]
			else:
				return make_response('Fail', 400)
			(email, activation_token) = DB.get_email(session.user)
			Email.send_email(
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

		@self.app.route("/api/unsubscribe")  # need: session
		def unsubscribe():
			session = self.get_session(request)
			if not session:
				return 'Fail'

			def notify():
				session['msg_queue'].put('stop')

			gevent.spawn(notify)
			return 'OK'

		@self.app.route("/api/join")  # need: session@queue, get@mode
		def join_room():
			session = self.get_session(request)
			if not self.get_session(request):
				return 'Fail'

			mode = int(request.args['mode'])
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
			card = int(request.args['card'])
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
			card = int(request.args['card'])
			result = room.defense(session['player_n'], card)
			if result == 'END':
				room_id = room.id
				if room.type == const.MODE_PVE:
					del self.rooms[room_id]
					del session['cur_room']
					return 'OK'
			return result

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
		# need: get@user; maybe: get@source = menu | any
		def get_avatar():
			user = request.args.get('user')
			if user == 'AI':
				return "/static_/svg/ic_computer_24px_white.svg"
			file_ext = DB.check_user(user)[2]
			if file_ext is not None:
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

				(result2, uid, file_ext, activated) = DB.check_user(name, sha256)
				if result2:
					s = Session(name, activated)
					self.sessions[s.get_id()] = s
					s['avatar'] = file_ext
					DB.add_session(s, uid)
					s.add_cookie_to_resp(response)

					Email.send_email(
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
				pass  # TODO

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
			(result, uid, file_ext, activated) = DB.check_user(request.form.get('user_name'), sha256)
			if result:
				s = Session(user_name, activated)
				self.sessions[s.get_id()] = s
				s['avatar'] = file_ext
				DB.add_session(s, uid)

				response = make_response('True')
				response.headers["Content-type"] = "text/plain"
				s.add_cookie_to_resp(response)
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
			del self.sessions[request.cookies['sessID']]
			return response

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
