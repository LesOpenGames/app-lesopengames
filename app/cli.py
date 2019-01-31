import os
import click
from app.models import User, Post, Team, RolesType
from app import db



def register(app):
    @app.cli.group()
    def og_adm():
        """Administration for opengames app"""
        pass

    @og_adm.command()
    @click.argument('user_id')
    @click.argument('passwd')
    def set_pwd(user_id, passwd):
        """Set password for user by id"""
        user = User.query.get(user_id)
        if( user == None ):
            print("no such user")
            return
        use.set_password(passwd)

    @og_adm.command()
    @click.argument('user_id')
    def set_admin(user_id):
        """Set admin rights to user by id"""
        user = User.query.get(user_id)
        if( user == None ):
            print("no such user")
            return
        user.role=RolesType.ADMIN
        db.session.commit()

    @og_adm.command()
    @click.argument('user_id')
    def del_user(user_id):
        """Del user by id"""
        user = User.query.get(user_id)
        if( user == None ):
            print("no such user")
            return
        db.session.delete(user)
        db.session.commit()
        print("User {} deleted".format(user.username))

    @og_adm.command()
    def show_users():
        """List all users in base"""
        for u in User.query.all():
            print ("{0:4} {1:14} {3:20} {2:30} ".format(
                str(u.id or '---'),
                str(u.username or '---'),
                str(u.email or '---'),
                str(u.role  or '---')))

    @app.cli.group()
    def translate():
        """Translate and localization commands"""
        pass

    @translate.command()
    @click.argument('lang')
    def init(lang):
        """Initialize a new language"""
        if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
            raise RuntimeError('extract command failed')
        if os.system('pybabel init -i messages.pot -d app/translations -l ' + lang ):
            raise RuntimeError('init command failed')
        os.remove('messages.pot')

    @translate.command()
    def update():
        """Update all languages"""
        if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
            raise RuntimeError('extract command failed')
        if os.system('pybabel update -i messages.pot -d app/translations'):
            raise RuntimeError('update command failed')
        os.remove('messages.pot')

    @translate.command()
    def compile():
        """Compile all languages"""
        if os.system('pybabel compile -d app/translations/'):
            raise RuntimeError('compile command failed')
