import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import getpass

login = getpass.getuser()
password = getpass.getpass(prompt='Password for Mail: ')
print(login)
print(password)

def send_mail(login, password):
    server = smtplib.SMTP("mail.urz.uni-heidelberg.de", 587)

    #Next, log in to the server
    server.login(login, password)

    fromaddr = "chrisb@mathphys.stura.uni-heidelberg.de"
    toaddr = "chris-blattgerste@gmx.de"

    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Python test email"
    body = "Python test mail"
    msg.attach(MIMEText(body, 'plain'))

    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
