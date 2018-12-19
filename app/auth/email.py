from flask import render_template, current_app
from flask_babel import _
from app.email import send_email


def send_password_reset_email(user):
    token = user.get_reset_password_token() # default expires after 600 secs
    send_email(_('[Microblog] Password Reset'),
        sender=current_app.config['ADMINS'][0],
        recipients=[user.email],
        body_text=render_template('reset_password_email.txt', user=user, token=token),
        body_html=render_template('reset_password_email.html', user=user, token=token))


