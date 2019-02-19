from flask import Blueprint

bp = Blueprint('billing', __name__ , template_folder='templates')

from app.billing import routes
