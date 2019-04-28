import os
import click
from app.models import User, Post, Team, Challenge, Score
from app.models import RolesType, ChallScoreType, ChallTeamType
from app import db



def register(app):
    @app.cli.group()
    def og_seed():
        """Database seeding"""

    @og_seed.command()
    def rm_challenges():
        """Remove all challenges"""
        for c in Challenge.query.all():
            db.session.delete(c)
        db.session.commit()

    @og_seed.command()
    def init_challenges():
        """Add all challenges"""
        db.session.add_all(
                [
                Challenge(challenge_name='Badminton/Tournoi', score_type=int(ChallScoreType.TOURNAMENT), team_type=int(ChallTeamType.TEAM)) ,
                Challenge(challenge_name='Badminton/Points', score_type=int(ChallScoreType.POINTS), team_type=int(ChallTeamType.INDIV)) ,
                Challenge(challenge_name='Judo/Points', score_type=int(ChallScoreType.POINTS), team_type=int(ChallTeamType.INDIV)) ,
                Challenge(challenge_name='Judo/Chrono', score_type=int(ChallScoreType.CHRONO), team_type=int(ChallTeamType.TEAM)) ,
                Challenge(challenge_name='Tennis de Table/Points', score_type=int(ChallScoreType.POINTS), team_type=int(ChallTeamType.INDIV)) ,
                Challenge(challenge_name='Tennis de Table/Tournoi', score_type=int(ChallScoreType.TOURNAMENT), team_type=int(ChallTeamType.TEAM)) 
                ]
            )
        db.session.commit()

    @app.cli.group()
    def og_adm():
        """Administration for opengames app"""
        pass

    @og_adm.command()
    def update_scores():
        """Populate the scores table with all players"""
        with db.session.no_autoflush:
            for c in Challenge.query.all():
                valid_teams = [t for t in Team.query.all() if t.is_valid() ]
                for t in valid_teams:
                    for p in t.get_players():
                        s = Score(score=0)
                        s.player = p
                        c.players.append(s)
        db.session.commit()

    @og_adm.command()
    def show_scores():
        # iterate through child objects via association, including association
        # attributes
        print("{3:2} {0:30} {1:15} {2:5}".format("Challenge", "Player", "Score", "Id"))
        print("{3:2} {0:30} {1:15} {2:5}".format('-'*30, '-'*15, '-'*5, '-'*2))
        for score in Score.query.all():
            print("{3:2} {0:30} {1:15} {2:5}".format(score.challenge.challenge_name,
                                score.player.username,
                                score.score,
                                score.challenge.id))

    @og_adm.command()
    def rm_scores():
        """Remove all scores"""
        for s in Score.query.filter():
            db.session.delete(s)
        db.session.commit()

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
        print ("{0:4} {1:4} {4:6} {2:14} {5:10} {3:6}".format(
            str('id'),
            str('num.'),
            str('name'),
            str('players'),
            str('open'),
            str('level'),
            ))
        for t in Team.query.order_by(Team.id).all():
            print ("{0:4} {1:4} {4:6} {2:14} {5:10} {3:6}".format(
                str(t.id or '---'),
                str(t.get_team_number() or '---'),
                str(t.teamname or '---'),
                str(t.get_players()),
                str("open" if t.is_open else "closed"),
                str(t.sport_level_name()),
                ))

    @og_adm.command()
    def show_challenges():
        """List all challenges"""
        for c in Challenge.query.order_by(Challenge.id).all():
            print("{0:4} {1:32} {2:32} {3:4}".format(
            str(c.id),
            str(c.challenge_name),
            str(ChallScoreType(c.score_type)),
            str(c.juge_id),
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
