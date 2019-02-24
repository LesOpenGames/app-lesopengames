from flask import render_template, current_app
from flask_babel import _, lazy_gettext as _l
from app.email import send_email


def send_account_created_email(user):
    send_email(_('[LesOpenGames] Account Created'),
        sender=current_app.config['ADMIN_EMAIL'],
        recipients=[user.email],
        body_text=render_template(_('account_created_email.txt'), user=user),
        body_html=render_template(_('account_created_email.html'), user=user))

def send_password_reset_email(user):
    token = user.get_reset_password_token() # default expires after 600 secs
    send_email(_('[LesOpenGames] Password Reset'),
        sender=current_app.config['ADMIN_EMAIL'],
        recipients=[user.email],
        body_text=render_template(_('reset_password_email.txt'), user=user, token=token),
        body_html=render_template(_('reset_password_email.html'), user=user, token=token))


