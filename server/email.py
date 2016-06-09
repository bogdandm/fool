from email.mime.text import MIMEText
from smtplib import SMTP_SSL as SMTP

from server.const import SENDER, USERNAME, PASSWORD, SMTPServer

text_subtype = 'plain'


def send_email(message, subject, to):
	try:
		msg = MIMEText(message, text_subtype)
		msg['Subject'] = subject
		msg['From'] = SENDER

		conn = SMTP(SMTPServer)
		conn.set_debuglevel(False)
		conn.login(USERNAME, PASSWORD)
		try:
			res = conn.sendmail(SENDER, to, msg.as_string())
		finally:
			conn.close()

	except Exception as e:
		return e
	return res
