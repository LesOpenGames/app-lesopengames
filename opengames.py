from app import create_app, db, cli
from app.models import User, Post

opengamesapp = create_app()
cli.register(opengamesapp)

@opengamesapp.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}
