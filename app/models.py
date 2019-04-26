import jwt
import enum

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.orderinglist import ordering_list
from flask import current_app
from flask_login import UserMixin
from datetime import datetime, date, timedelta
from hashlib import md5
from time import time

from flask_babel import _, lazy_gettext as _l


from app import db, login

class ChallScoreType(enum.IntEnum):
    POINTS = 0
    CHRONO = 1
    TOURNAMENT = 2

class ChallTeamType(enum.IntEnum):
    INDIV = 0
    TEAM = 1

class RolesType(enum.IntEnum):
    ADMIN = 0
    JUGE = 1
    PLAYER = 2

class RacketSportType(enum.IntEnum):
    PINGPONG = 0
    BADMINTON = 1

class CollectiveSportType(enum.IntEnum):
    HAND = 0
    FLAG = 1

class SportLevel(enum.IntEnum):
    EASY = 0
    TOUGH = 1

# simple relation as table, not class
#
followers = db.Table('followers',
        db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
        db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
        )

# used by the flask_login extension for db interaction
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True )
    challenge_name = db.Column(db.String(64), index=True, unique=True)
    score_type = db.Column(db.Integer)
    team_type = db.Column(db.Integer)
    juge_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def set_juge(self, juge):
        self.juge_id = juge.id

    def get_juge(self):
        if( self.juge_id is None):
            return None
        juge = User.query.get(self.juge_id)
        return  juge

    def score_type_name(self):
        score_types = [_("Points"), _("Chrono"), _("Tournament")]
        return _("none") if self.score_type is None else score_types[self.score_type]

    def team_type_name(self):
        team_types = [_("Individual"), _("Team")]
        return _("none") if self.team_type is None else team_types[self.team_type]

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True )
    username = db.Column(db.String(64), index=True, unique=True)
    secondname = db.Column(db.String(64))
    firstname = db.Column(db.String(64))
    birthdate = db.Column(db.DateTime)
    weight = db.Column(db.Integer)
    gender = db.Column(db.Integer)
    email = db.Column(db.String(120), index=True, unique=True)
    phonenumberstr = db.Column( db.String(32) )
    password_hash = db.Column(db.String(128))
    role = db.Column(db.Integer)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    player_rank = db.Column(db.Integer)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    valid_health = db.Column(db.Boolean, default=False)
    valid_auth = db.Column(db.Boolean, default=False)
    student = db.Column(db.Boolean, default=False)
    is_striped = db.Column(db.Boolean, default=False)
    # see before, the followers relationshup
    followed = db.relationship(
            'User', secondary=followers,
            primaryjoin=(followers.c.follower_id == id ),
            secondaryjoin=(followers.c.followed_id == id ),
            backref=db.backref('followers', lazy='dynamic'), lazy='dynamic') # this name is the new User.fieldname

    def __repr__(self):
        return '<Player {} {}, rank {}>'.format(self.id, self.username, self.player_rank)

    def has_team(self):
        return self.team is not None

    def get_billing(self):
        if( ( not self.is_mayor() ) or self.student  ):
            return 25
        else:
            return 30

    def gender_str(self):
        gender = [_("M"), _("F")]
        return "none" if self.gender is None else gender[self.gender]

    def is_valid(self):
        return self.is_valid_health() and self.is_valid_auth() and self.is_valid_age()

    def is_valid_health(self):
        return self.valid_health

    def is_valid_auth(self):
        return self.is_mayor() or self.valid_auth

    def is_valid_age(self):
        if ( self.birthdate is None ):
            return False
        elif( self.is_mayor() ):
            return True
        elif ( self.team ):
            if( self.team.sport_level == int( SportLevel.EASY) ):
                return self.birthdate.year <= 2007
            elif( self.team.sport_level == int( SportLevel.TOUGH) ):
                return self.birthdate.year <= 2004
        return False

    def is_mayor(self):
        if( self.birthdate is None ):
            return False
        age = ( datetime.today() - self.birthdate ) / timedelta(days=365.2425)
        return age >= 18.0

    def is_juge(self):
        return self.role is not None and RolesType(self.role) == RolesType.JUGE

    def is_admin(self):
        return self.role is not None and RolesType(self.role) == RolesType.ADMIN

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash( self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
                followers.c.followed_id == user.id).count()>0

    def followed_posts(self):
        followed_posts = Post.query.join( followers,
                                ( followers.c.followed_id == Post.user_id )
                              ).filter( followers.c.follower_id == self.id )
        own_posts = Post.query.filter_by( user_id = self.id)
        return followed_posts.union(own_posts).order_by( Post.timestamp.desc() )

    def get_reset_password_token(self, expires=600):
        return jwt.encode({'id_to_reset': self.id, 'exp': time() + expires},
                current_app.config['SECRET_KEY'],
                algorithm = 'HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithm='HS256')['id_to_reset']
        except:
            return
        return User.query.get(int(id))

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True ) 
    teamname =  db.Column(db.String(80), unique=True, nullable=False)
    team_number = db.Column(db.Integer, unique=True)
    players = db.relationship("User", backref='team', order_by="User.player_rank", collection_class=ordering_list('player_rank'))
    racket_sport_type = db.Column(db.Integer )
    collective_sport_type = db.Column(db.Integer )
    sport_level = db.Column(db.Integer )
    is_partner = db.Column(db.Boolean, default=False)
    is_paid = db.Column(db.Boolean, default=False)
    is_striped = db.Column(db.Boolean, default=False)
    is_open = db.Column(db.Boolean, default=False)
    
    def get_billing(self):
        team_players = self.get_players()
        bill = 0
        if len( team_players ) == 4:
            for p in team_players:
                bill = bill + p.get_billing()
        if self.is_partner:
            bill = bill/2
        return bill

    def is_valid(self):
        team_players = self.get_players()
        if(  len( team_players ) == 4):
            return  ( self.is_paid  and
                    team_players[0].is_valid() and
                    team_players[1].is_valid() and
                    team_players[2].is_valid() and
                    team_players[3].is_valid() )
        else:
            return False

    def get_team_number(self):
        if( self.is_valid() ):
            return self.team_number
        else:
            return None

    def unset_team_number(self):
        self.team_number = None

    def set_team_number(self):
        if ( self.team_number is not None):
            return 0
        # get all team_numbers
        team_numbers = [ tn for tn, in db.session.query(Team.team_number).all() if tn is not None]
        # set to 1 if no numbered teams
        if( len(team_numbers) == 0):
            self.team_number = 1
            return 0
        # or get the smallest available number
        team_numbers.sort()
        i = 0
        for n in team_numbers:
            i = i+1
            if( n == i ):
                continue
            elif( n > i):
                self.team_number = i
                return 0
            else:
                raise RunTimeError("Wrong team number")
        # if list was complete, we exited for loop without finding smallest available
        # set to last + 1
        self.team_number = i+1

    def racket_sport_name(self):
        racket_sports = [_("PingPong"), _("Badminton")]
        return "none" if self.racket_sport_type is None else racket_sports[self.racket_sport_type]
    def collective_sport_name(self):
        collective_sports = [_("Handball"), _("Flag")]
        return "none" if self.collective_sport_type is None else collective_sports[self.collective_sport_type]
    def sport_level_name(self):
        levels = [_("Easy"), _("Sport")]
        #return "none" if self.sport_level is None else SportLevel(self.sport_level)
        return "none" if self.sport_level is None else levels[self.sport_level]

    def get_players(self):
        return self.players
	
    def is_leader(self, player):
        return self.is_player(player) and (player.player_rank == 0 )

    def is_player(self, player):
        #return False if ( player.team == None ) else ( player.team.id == self.id )
        #return self.players.count( player ) == 1 # wont work if User.id isnt udpated with session add and commit
        #return db.session.query(Team).join(Team.players).filter(User.id==player.id .filter(Team.id==self.id).count() == 1
        return Team.query.filter( Team.players.any( User.id == player.id ) ).filter(Team.id==self.id).count() == 1

#   def move_to_leader(self, player):
#   def move_to_rank(self, player, rank):

    def subscribe(self, player):
        if not self.is_player( player ):
            self.players.append(player)
        self.players.reorder()

    def unsubscribe(self, player):
        if self.is_player( player ):
            self.players.remove(player)

    def __repr__(self):
        return '<Team: {}, Players: {} >'.format( self.teamname, self.players)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True )
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column( db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)

# vim: tw=0
