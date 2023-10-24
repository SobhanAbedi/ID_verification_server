from secrets_pkg.mail_secret import *
import requests
import smtplib
from email.mime.text import MIMEText


def send_email_api(mail_addr: str, message: str) -> None:
    print(f"Sending Email to {mail_addr}")
    resp = requests.post(
        MAIL_SERVICE_API_URL,
        auth=("api", MAIL_SERVICE_API_KEY),
        data={"from": f"ID Checker <mailgun@{MAIL_SERVICE_DOMAIN}>",
              "to": [mail_addr],
              "subject": "ID Check",
              "text": message},
        timeout=30).json()
    print(resp)


def send_email_smtp(mail_addr: str, message: str) -> None:
    print(f"Sending Email to {mail_addr}")
    msg = MIMEText(message)
    msg['Subject'] = "ID Check"
    msg['From'] = SMTP_SENDER
    msg['To'] = mail_addr
    with smtplib.SMTP_SSL(SMTP_URL, SMTP_PRT) as smtp_server:
        smtp_server.login(SMTP_SENDER, SMTP_KEY)
        smtp_server.sendmail(msg['From'], msg['To'], msg.as_string())
    print(f"Message Sent")
