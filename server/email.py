from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText


class Email:
	SMTPServer = 'smtp.gmail.com'
	sender = 'fool.online.server@gmail.com'
	USERNAME = "fool.online.server"
	PASSWORD = "fool_server"
	text_subtype = 'plain'

	@staticmethod
	def send_email(message, subject, to):
		try:
			msg = MIMEText(message, Email.text_subtype)
			msg['Subject'] = subject
			msg['From'] = Email.sender  # some SMTP servers will do this automatically, not all

			conn = SMTP(Email.SMTPServer)
			conn.set_debuglevel(False)
			conn.login(Email.USERNAME, Email.PASSWORD)
			try:
				res = conn.sendmail(Email.sender, to, msg.as_string())
			finally:
				conn.close()

		except Exception as e:
			return e
		return res
