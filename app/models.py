import jwt
import enum

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.orderinglist import ordering_list
from flask import current_app
from flask_login import UserMixin
from datetime import datetime
from hashlib import md5
from time import time


from app import db, login

class RolesType(enum.Enum):
    ADMIN = 0
    JUGE = 1
    PLAYER = 2



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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True )
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.Enum(RolesType))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    player_rank = db.Column(db.Integer)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    # see before, the followers relationshup
    followed = db.relationship(
            'User', secondary=followers,
            primaryjoin=(followers.c.follower_id == id ),
            secondaryjoin=(followers.c.followed_id == id ),
            backref=db.backref('followers', lazy='dynamic'), lazy='dynamic') # this name is the new User.fieldname

    def __repr__(self):
        return '<Player {} {}, rank {}>'.format(self.id, self.username, self.player_rank)

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
    players = db.relationship("User", backref='team', order_by="User.player_rank", collection_class=ordering_list('player_rank'))


    def get_players(self):
        return self.players
	
    def is_leader(self, player):
        return self.is_player(player) and (player.player_rank == 0 )
        #try:
        #    index = self.players.index(user)
        #except:
        #    return False
        #return index == 0

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
