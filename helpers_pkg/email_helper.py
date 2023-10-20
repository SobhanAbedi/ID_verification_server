from secrets_pkg.mail_secret import *
import requests


def send_email(mail_addr: str, msg: str) -> None:
    print(f"Sending Email to {mail_addr}")
    print(requests.post(
        MAIL_SERVICE_API_URL,
        auth=("api", MAIL_SERVICE_API_KEY),
        data={"from": f"ID Checker <mailgun@{MAIL_SERVICE_DOMAIN}>",
              "to": [mail_addr],
              "subject": "ID Check",
              "text": msg}).json())