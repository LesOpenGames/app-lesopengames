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
        user.set_password(passwd)
        db.session.commit()

    @og_adm.command()
    @click.argument('user_id')
    def set_admin(user_id):
        """Set admin rights to user by id"""
        user = User.query.get(user_id)
        if( user == None ):
            print("no such user")
            return
        user.role=int(RolesType.ADMIN)
        db.session.commit()

    @og_adm.command()
    @click.argument('team_id')
    def del_team(team_id):
        """Del team by id"""
        team = Team.query.get(team_id)
        if( team == None ):
            print("no such team")
            return
        db.session.delete(team)
        db.session.commit()
        print("Team {} deleted".format(team.teamname))

    @og_adm.command()
    def show_teams():
        """List all teams in base"""
        for t in Team.query.order_by(Team.id).all():
            print ("{0:4} {1:4} {2:14}".format(
                str(t.id or '---'),
                str(t.team_number or '---'),
                str(t.teamname or '---')
                ))

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
        print ("{0:4} {1:14} {3:20} {2:30} {4:4} {5:4}".format(
                'id', 
                'username', 
                'email', 
                'role', 
                'team', 
                'rank', 
                ))
        for u in User.query.order_by(User.id).all():
            print ("{0:4} {1:14} {3:20} {2:30} {4:4} {5:4}".format(
                str(u.id or '---'),
                str(u.username or '---'),
                str(u.email or '---'),
                str('---' if u.role is None  else  RolesType(u.role)),
                str('---' if u.team_id is None  else  u.team_id),
                str('---' if u.player_rank is None  else  u.player_rank)))

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
