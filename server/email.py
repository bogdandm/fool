from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText

SMTPServer = 'smtp.gmail.com'
sender = 'fool.online.server@gmail.com'
USERNAME = "fool.online.server"
PASSWORD = "fool_server"
text_subtype = 'plain'


def send_email(message, subject, to):
	try:
		msg = MIMEText(message, text_subtype)
		msg['Subject'] = subject
		msg['From'] = sender

		conn = SMTP(SMTPServer)
		conn.set_debuglevel(False)
		conn.login(USERNAME, PASSWORD)
		try:
			res = conn.sendmail(sender, to, msg.as_string())
		finally:
			conn.close()

	except Exception as e:
		return e
	return res
