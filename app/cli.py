import os
import click
from app.models import User, Post, Team, Challenge, Score
from app.models import RolesType, ChallScoreType, ChallTeamType, SportLevel
from app import db
from sqlalchemy import func

challenges=[
        #tournament team
           { "challenge_name":'Badminton/Tournoi', "score_type":int(ChallScoreType.TOURNAMENT), "team_type":int(ChallTeamType.TEAM) },
           { "challenge_name":'Tennis de Table/Tournoi', "score_type":int(ChallScoreType.TOURNAMENT), "team_type":int(ChallTeamType.TEAM) },
           { "challenge_name":'Flag/Tournoi', "score_type":int(ChallScoreType.TOURNAMENT), "team_type":int(ChallTeamType.TEAM) },
           { "challenge_name":'HandBall/Tournoi', "score_type":int(ChallScoreType.TOURNAMENT), "team_type":int(ChallTeamType.TEAM) },
        #tournament indiv
           { "challenge_name":'Athlétisme/Tournoi', "score_type":int(ChallScoreType.TOURNAMENT), "team_type":int(ChallTeamType.INDIV) },
        #chrono team
           { "challenge_name":'Judo/Chrono', "score_type":int(ChallScoreType.CHRONO), "team_type":int(ChallTeamType.TEAM) },
           { "challenge_name":'Athlétisme/Chrono', "score_type":int(ChallScoreType.CHRONO), "team_type":int(ChallTeamType.TEAM) },
           { "challenge_name":'Orientation 1/Chrono', "score_type":int(ChallScoreType.CHRONO), "team_type":int(ChallTeamType.TEAM) },
           { "challenge_name":'Orientation 2/Chrono', "score_type":int(ChallScoreType.CHRONO), "team_type":int(ChallTeamType.TEAM) },
           { "challenge_name":'Jeux Gonflables/Chrono', "score_type":int(ChallScoreType.CHRONO), "team_type":int(ChallTeamType.TEAM) },
           { "challenge_name":'Finale/Chrono', "score_type":int(ChallScoreType.CHRONO), "team_type":int(ChallTeamType.TEAM) },
        #chrono indiv
            #none
        #points team
           { "challenge_name":'Noeuds/Points', "score_type":int(ChallScoreType.POINTS), "team_type":int(ChallTeamType.TEAM) },
        #points indiv
           { "challenge_name":'Badminton/Points', "score_type":int(ChallScoreType.POINTS), "team_type":int(ChallTeamType.INDIV) },
           { "challenge_name":'Judo/Points', "score_type":int(ChallScoreType.POINTS), "team_type":int(ChallTeamType.INDIV) },
           { "challenge_name":'Tennis de Table/Points', "score_type":int(ChallScoreType.POINTS), "team_type":int(ChallTeamType.INDIV) },
           { "challenge_name":'HandBall/Points', "score_type":int(ChallScoreType.POINTS), "team_type":int(ChallTeamType.INDIV) },
           { "challenge_name":'Jeux Gonflables/Points', "score_type":int(ChallScoreType.POINTS), "team_type":int(ChallTeamType.INDIV) },
        #distance indiv
           { "challenge_name":'Athlétisme/Distance', "score_type":int(ChallScoreType.DISTANCE), "team_type":int(ChallTeamType.TEAM) },
        #score team
           { "challenge_name":'Vote Supporter/Bonus', "score_type":int(ChallScoreType.BONUS), "team_type":int(ChallTeamType.TEAM) },
           { "challenge_name":'Jeux Gonflables/Bonus', "score_type":int(ChallScoreType.BONUS), "team_type":int(ChallTeamType.TEAM) },
           ]

def c2j(c_name):
    """Change the challenge name into jugename"""
    j_name = c_name.replace(" ", "_")
    j_name = j_name.replace("/", "_")
    return j_name

def register(app):
    @app.cli.group()
    def og_seed():
        pass

    @og_seed.command()
    @click.pass_context
    def init_jcs(ctx):
        """Initialize juges, challenges and scores"""
        ctx.forward(init_juges)
        ctx.forward(init_challenges)
        ctx.forward(init_scores)

    @og_seed.command()
    @click.pass_context
    def rm_jcs(ctx):
        """Remove juges, challenges and scores (reverse order)"""
        ctx.forward(rm_scores)
        ctx.forward(rm_challenges)
        ctx.forward(rm_juges)

    @og_seed.command()
    def init_scores():
        """Populate the scores table with all players (init challenges first) """
        with db.session.no_autoflush:
            for c in Challenge.query.all():
                valid_teams = [t for t in Team.query.all() if t.is_valid() ]
                for t in valid_teams:
                    for p in t.get_players():
                        s = Score(score=0, distance=0, chrono=0, bonus=0, tourna=0)
                        s.player = p
                        s.team = t
                        c.players.append(s)
        db.session.commit()

    @og_seed.command()
    def rm_scores():
        """Remove all scores"""
        for s in Score.query.filter():
            db.session.delete(s)
        db.session.commit()

    @og_seed.command()
    def init_juges():
        """Add all juges (from challenges list)""" 
        for c in challenges:
            j_first_name=c2j(c["challenge_name"])
            j_username = "Arbitre_"+j_first_name
            j_email = j_username+"@og.fr"
            db.session.add(
                User(username=j_username,
                    role=int(RolesType.JUGE),
                    email=j_email,
                    secondname='Arbitre',
                    firstname=j_first_name),
                )
        db.session.commit()

    @og_seed.command()
    def rm_juges():
        """Remove all juges"""
        for j in User.query.filter(User.role==int(RolesType.JUGE)).all():
            db.session.delete(j)
        db.session.commit()

    @og_seed.command()
    def rm_challenges():
        """Remove all challenges (remove scores and juges first)"""
        for c in Challenge.query.all():
            db.session.delete(c)
        db.session.commit()

    @og_seed.command()
    def init_challenges():
        """Add all challenges (init juges first)"""
        for c in challenges:
            j = User.query.filter(User.firstname==c2j(c["challenge_name"]) ).one()
            challenge = Challenge( juge_id=j.id, challenge_name=c["challenge_name"], score_type=c["score_type"], team_type=c["team_type"] ) 
            db.session.add(challenge)
        db.session.commit()

    @app.cli.group()
    def og_adm():
        """Administration for opengames app"""
        pass

    @og_adm.command()
    def show_tourna_teams():
        """Show team tournoi scores by challenge"""
        for c in Challenge.query.filter(Challenge.team_type == int(ChallTeamType.TEAM)):
            print("\n"+c.challenge_name)
            print('-'*34)
            stmt = db.session.query(Score.team_id, func.max(Score.tourna).label('tourna') ).\
                    filter(Score.challenge_id == c.id).\
                    group_by(Score.team_id).subquery()
            joined = db.session.query(Team.teamname, stmt.c.tourna).\
                    outerjoin(stmt, stmt.c.team_id == Team.id)
            for t_name, tourna in joined.all():
                print( "{0:5} {1:25} {2:4}".format(str(' '), str(t_name), str(tourna)) )

    @og_adm.command()
    def show_scores_byteams():
        """Show team scores by team_id"""
        for t in Team.query.all():
            print("\n"+t.teamname)
            print('-'*34)
            stmt = db.session.query(Score.challenge_id, func.sum(Score.score).label('score_total') ).\
                    filter(Score.team_id == t.id).\
                    group_by(Score.challenge_id).subquery()
            joined = db.session.query(Challenge.challenge_name, stmt.c.score_total).\
                    outerjoin(stmt, stmt.c.challenge_id == Challenge.id)
            for name, total in joined.all():
                print( "{0:5} {1:25} {2:4}".format(str(' '), str(name), str(total)) )

    @og_adm.command()
    @click.argument('challenge_id')
    def show_scores_distance(challenge_id):
        stmt = db.session.query(Score.team_id, func.max(Score.distance).label('distance') ).\
                filter(Score.challenge_id == challenge_id).\
                group_by(Score.team_id).subquery()
        print( "{0:5} {1:5}".format("id", "dist.") )
        print( "{0:5} {1:5}".format("-"*5, "-"*5) )
        for sport_level in (int(SportLevel.EASY), int(SportLevel.TOUGH) ):
            print( "   "+("easy", "tough")[sport_level])
            sorted_teams = db.session.query(Team, stmt.c.distance).\
                    order_by( stmt.c.distance.desc() ).\
                    filter(Team.sport_level == sport_level).\
                    filter(stmt.c.distance.isnot(None) ).\
                    outerjoin(stmt, stmt.c.team_id == Team.id)
            for team, value in sorted_teams.all():
                print( "{0:5} {1:5}".format(str(team.id), str(value)) )

    @og_adm.command()
    @click.argument('challenge_id')
    def show_scores_chrono(challenge_id):
        stmt = db.session.query(Score.team_id, func.max(Score.chrono).label('chrono') ).\
                filter(Score.challenge_id == challenge_id).\
                group_by(Score.team_id).subquery()
        sorted_teams = db.session.query(Team, stmt.c.chrono).\
                order_by( stmt.c.chrono.asc() ).\
                outerjoin(stmt, stmt.c.team_id == Team.id)
        for team, value in sorted_teams.all():
            print( team.id, value)

    @og_adm.command()
    def show_scores_all():
        """Show all scores"""
        # iterate through child objects via association, including association
        # attributes
        print("{3:2} {0:30} {4:15} {1:15} {2:5} {5:5} {6:5} {7:5} {8:5}".format("Challenge", "Player", "Score", "Id", "Team", "Chrono", "Tourna", "Bonus", "Distance"))
        print("{3:2} {0:30} {4:15} {1:15} {2:5} {5:5} {6:5} {7:5} {8:5}".format('-'*30, '-'*15, '-'*5, '-'*2, '-'*15, '-'*5, '-'*5, '-'*5, '-'*5))
        for score in Score.query.order_by(Score.challenge_id, Score.team_id).all():
            print("{3:2} {0:30} {4:15} {1:15} {2:5} {5:5} {6:5} {7:5} {8:5}".format(score.challenge.challenge_name,
                                score.player.username,
                                score.score,
                                score.challenge.id,
                                score.team.teamname,
                                score.chrono,
                                score.tourna,
                                score.bonus,
                                score.distance,
                                ))

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
