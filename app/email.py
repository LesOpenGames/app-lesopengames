from flask import render_template, current_app
from flask_mail import Message
from flask_babel import _

from app import mail
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, body_text, body_html):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = body_text
    msg.html = body_html
    Thread(target=send_async_email,
            args=(current_app._get_current_object(), msg)).start()
