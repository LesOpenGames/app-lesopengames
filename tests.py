from datetime import datetime, timedelta
import unittest
from app import db, create_app
from app.models import User, Post, Team, RolesType, CollectiveSportType, RacketSportType, SportLevel

from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

class TeamModelCase(unittest.TestCase):
    def setUp(self):
        # 
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_team_subscribe(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        t1 = Team(teamname='cathares')
        db.session.add_all([u1, u2, u3, u4, t1])
        db.session.commit()

        self.assertEqual(t1.players, [])

        t1.subscribe(u1)
        t1.subscribe(u2)
        t1.subscribe(u3)
        t1.subscribe(u4)

        self.assertEqual(t1.players, [u1, u2, u3, u4])


        self.assertTrue(t1.is_player(u1))
        self.assertTrue(t1.is_player(u2))
        self.assertTrue(t1.is_player(u3))
        self.assertTrue(t1.is_player(u4))

        t2 = Team(teamname='pelutes')
        u5 = User(username='joseph', email='joseph@example.com')
        t2.subscribe(u5)
        db.session.add_all([t2, u5])

        self.assertFalse(t1.is_player(u5))
        self.assertTrue(t2.is_player(u5))

    def test_team_isleader(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='sarah', email='sarah@example.com')
        u3 = User(username='cedric', email='cedric@example.com')
        t1 = Team(teamname='cathares')
        t1.subscribe(u1)
        t1.subscribe(u2)
        db.session.add(t1)
        db.session.commit()
        self.assertTrue(t1.is_leader(u1))
        self.assertFalse(t1.is_leader(u2))
        self.assertFalse(t1.is_leader(u3))

    def test_team_sportstype(self):
        t0 = Team(teamname='pelutes')
        t0.racket_sport_type = RacketSportType.PINGPONG
        t0.collective_sport_type = CollectiveSportType.HAND
        t0.sport_level = SportLevel.EASY

        t1 = Team(teamname='cathares')
        t1.racket_sport_type = RacketSportType.BADMINTON
        t1.collective_sport_type = CollectiveSportType.FLAG
        t1.sport_level = SportLevel.TOUGH

        db.session.add_all([t1, t0])
        db.session.commit()

        s0  = Team.query.filter_by(teamname='pelutes').one()
        self.assertEqual(s0.racket_sport_type, RacketSportType.PINGPONG)
        self.assertEqual(s0.collective_sport_type, CollectiveSportType.HAND)
        self.assertEqual(s0.sport_level, SportLevel.EASY)
        s1  = Team.query.filter_by(teamname='cathares').one()
        self.assertEqual(s1.racket_sport_type, RacketSportType.BADMINTON)
        self.assertEqual(s1.collective_sport_type, CollectiveSportType.FLAG)
        self.assertEqual(s1.sport_level, SportLevel.TOUGH)

    def test_team_noteam_number(self):
        t1 = Team(teamname='cathares')
        t2 = Team(teamname='pelutes')
        db.session.add_all([t1, t2])
        db.session.commit()

        self.assertTrue(t1.team_number is None)
        self.assertTrue(t2.team_number is None)
        
    def test_team_set_team_number(self):
        t1 = Team(teamname='cathares')
        t2 = Team(teamname='pelutes')
        t3 = Team(teamname='chatons')

        db.session.add_all([t1, t2, t3])
        db.session.commit()

        self.assertTrue(t1.team_number is None)
        self.assertTrue(t2.team_number is None)
        self.assertTrue(t3.team_number is None)

        t1.set_team_number()
        t2.set_team_number()
        t3.set_team_number()
        db.session.commit()

        self.assertEqual(t1.team_number , 1 )
        self.assertEqual(t2.team_number , 2 )
        self.assertEqual(t3.team_number , 3 )

        t1.set_team_number()
        t2.unset_team_number()
        t3.unset_team_number()
        t3.set_team_number()
        db.session.commit()

        self.assertEqual(t1.team_number , 1 )
        self.assertEqual(t2.team_number , None )
        self.assertEqual(t3.team_number , 2 )

    def test_team_is_valid(self):
        u1 = User(username='jos', email='jos@example.com', valid_auth = True, valid_health = True, birthdate=datetime(1970, 12, 9))
        u2 = User(username='fab', email='fab@example.com', valid_auth = True, valid_health = True, birthdate=datetime(1970, 12, 9))
        u3 = User(username='luc', email='luc@example.com', valid_auth = True, valid_health = True, birthdate=datetime(1970, 12, 9))
        u4 = User(username='ing', email='ing@example.com', valid_auth = True, valid_health = True, birthdate=datetime(1970, 12, 9))

        t1 = Team(teamname='cathares', is_paid=True)
        t1.subscribe(u1)
        t1.subscribe(u2)
        t1.subscribe(u3)

        # not enough users
        self.assertFalse(t1.is_valid())

        t1.subscribe(u4)
        
        self.assertTrue(t1.is_valid())

    def test_team_is_not_valid(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')

        t1 = Team(teamname='cathares')
        t1.subscribe(u1)
        t1.subscribe(u2)
        t1.subscribe(u3)
        t1.subscribe(u4)
        
        self.assertFalse(t1.is_valid())

    def test_team_get_billing(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')

        v1 = User(username='jos', email='jos@example.com',  birthdate=datetime(1970, 12, 9))
        v2 = User(username='fab', email='fab@example.com',  birthdate=datetime(1970, 12, 9))
        v3 = User(username='luc', email='luc@example.com',  birthdate=datetime(1970, 12, 9))
        v4 = User(username='ing', email='ing@example.com',  birthdate=datetime(1970, 12, 9))

        t1 = Team(teamname='cathares')
        t1.subscribe(u1)
        t1.subscribe(u2)
        t1.subscribe(u3)

        t2 = Team(teamname='clowns')
        t2.subscribe(u1)
        t2.subscribe(u2)
        t2.subscribe(u3)
        t2.subscribe(u4)

        t3 = Team(teamname='peluts')
        t3.subscribe(v1)
        t3.subscribe(v2)
        t3.subscribe(v3)
        t3.subscribe(v4)

        self.assertEqual(t1.get_billing(), 0)
        self.assertEqual(t2.get_billing(), 100)
        self.assertEqual(t3.get_billing(), 120)

    def test_partner_get_billing(self):
        v1 = User(username='jos', email='jos@example.com',  birthdate=datetime(1970, 12, 9))
        v2 = User(username='fab', email='fab@example.com',  birthdate=datetime(1970, 12, 9))
        v3 = User(username='luc', email='luc@example.com',  birthdate=datetime(1970, 12, 9))
        v4 = User(username='ing', email='ing@example.com',  birthdate=datetime(1970, 12, 9))

        t3 = Team(teamname='peluts')
        t3.subscribe(v1)
        t3.subscribe(v2)
        t3.subscribe(v3)
        t3.subscribe(v4)

        self.assertEqual(t3.get_billing(), 120)
        t3.is_partner = True
        self.assertEqual(t3.get_billing(), 60)


class UserModelCase(unittest.TestCase):
    def setUp(self):
        # 
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
                                         'd4c74594d841139328695756648b6bd6'
                                         '?d=identicon&s=128'))

    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'susan')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'john')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_posts(self):
        # create four users
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # create four posts
        now = datetime.utcnow()
        p1 = Post(body="post from john", author=u1,
                  timestamp=now + timedelta(seconds=1))
        p2 = Post(body="post from susan", author=u2,
                  timestamp=now + timedelta(seconds=4))
        p3 = Post(body="post from mary", author=u3,
                  timestamp=now + timedelta(seconds=3))
        p4 = Post(body="post from david", author=u4,
                  timestamp=now + timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # setup the followers
        u1.follow(u2)  # john follows susan
        u1.follow(u4)  # john follows david
        u2.follow(u3)  # susan follows mary
        u3.follow(u4)  # mary follows david
        db.session.commit()

        # check the followed posts of each user
        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()
        self.assertEqual(f1, [p2, p4, p1])
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])

    def test_user_roles(self):
        u0 = User(username='david', email='david@example.com')
        u0.role = RolesType.ADMIN
        u1 = User(username='josette', email='josette@example.com')
        u1.role = RolesType.JUGE
        u2 = User(username='alfred', email='alfred@example.com')
        u2.role = RolesType.PLAYER
        
        db.session.add(u0)
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        v0  = User.query.filter_by(username='david').one()
        v1  = User.query.filter_by(username='josette').one()
        v2  = User.query.filter_by(username='alfred').one()

        self.assertEqual(v0.role, RolesType.ADMIN)
        self.assertEqual(v1.role, RolesType.JUGE)
        self.assertEqual(v2.role, RolesType.PLAYER)

    def test_user_is_admin(self):
        u0 = User(username='david', email='david@example.com')
        u0.role = int(RolesType.ADMIN)
        u1 = User(username='josette', email='josette@example.com')
        u1.role = RolesType.JUGE
        u2 = User(username='alfred', email='alfred@example.com')
        u2.role = RolesType.ADMIN
        u3 = User(username='chabin', email='chabin@example.com')

#       u3.role = "admin"
#        with self.assertRaises(ValueError):
#            u3.role = "admin"

        self.assertTrue( u0.is_admin() )
        self.assertFalse( u1.is_admin() )
        self.assertTrue( u2.is_admin() )
        self.assertFalse( u3.is_admin() )

    def test_user_is_valid_age_withnoteam(self):
        u1 = User(username='ing', email='ig@example.com',  birthdate=datetime(1970, 12, 9))
        u2 = User(username='jeune', email='j@example.com', birthdate=datetime(2004, 12, 9))
        
        self.assertTrue( u1.is_valid_age() )
        self.assertFalse( u2.is_valid_age() )

    def test_user_is_valid_age(self):
        u0 = User(username='trestresjeune', email='ttj@example.com', birthdate=datetime(2008, 12, 9))
        u1 = User(username='tresjeune', email='tj@example.com', birthdate=datetime(2007, 12, 9))
        u2 = User(username='jeune', email='j@example.com', birthdate=datetime(2004, 12, 9))
        u3 = User(username='age', email='ag@example.com', birthdate=datetime(1970, 12, 9))
        t0 = Team(teamname='Sportif', sport_level = SportLevel.TOUGH)
        t1 = Team(teamname='Loisir', sport_level = SportLevel.EASY)

        t0.subscribe(u0)
        t0.subscribe(u1)
        t0.subscribe(u2)
        t0.subscribe(u3)

        db.session.add(t0)
        db.session.commit()

        self.assertFalse( u0.is_valid_age() )
        self.assertFalse( u1.is_valid_age() )
        self.assertTrue(  u2.is_valid_age() )
        self.assertTrue(  u3.is_valid_age() )

        t1.subscribe(u0)
        t1.subscribe(u1)
        t1.subscribe(u2)
        t1.subscribe(u3)

        db.session.add(t1)
        db.session.commit()

        self.assertFalse( u0.is_valid_age() )
        self.assertTrue(  u1.is_valid_age() )
        self.assertTrue(  u2.is_valid_age() )
        self.assertTrue(  u3.is_valid_age() )

    def test_user_is_valid_age_withnoage(self):
        u0 = User(username='trestresjeune', email='ttj@example.com')
        t0 = Team(teamname='Sportif', sport_level = SportLevel.TOUGH)
        t0.subscribe(u0)
        db.session.add(t0)
        db.session.commit()

        # should return false as no age set
        self.assertFalse( u0.is_valid_age() )

    def test_user_is_valid(self):
        u1 = User(username='jeune', email='j@example.com', valid_auth = True, valid_health = False)
        u2 = User(username='age', email='ag@example.com', valid_auth = False, valid_health = True)
        u3 = User(username='shon', email='sh@example.com', birthdate=datetime(1970, 12, 9))
        u4 = User(username='ing', email='ig@example.com', valid_auth = True, valid_health = True, birthdate=datetime(1970, 12, 9))

        db.session.add_all([u1, u2, u3, u4])
        db.session.commit()

        self.assertFalse( u1.is_valid() )
        self.assertTrue( u1.is_valid_auth() )

        self.assertFalse( u1.is_valid_health() )
        self.assertFalse( u2.is_valid_auth() )
        self.assertTrue( u2.is_valid_health() )

        # even with valid_auth false, mayor player is_authorized
        self.assertTrue( u1.is_valid_auth() )

        self.assertTrue( u4.is_valid() )

    def test_user_is_mayor(self):
        u1 = User(username='jeune', email='j@example.com', birthdate=datetime(2004, 12, 9))
        u2 = User(username='age', email='ag@example.com', birthdate=datetime(1970, 12, 9))
        u3 = User(username='age', email='ag@example.com')
        self.assertFalse(u1.is_mayor())
        self.assertTrue(u2.is_mayor())
        self.assertFalse(u3.is_mayor())

    def test_user_phonenumberstr(self):
        u1 = User(username='romain', email='r@example.com', phonenumberstr='0644267582')
        u2 = User(username='david', email='d@example.com', phonenumberstr='06 44 26 75 82')
        u3 = User(username='sheila', email='s@example.com', phonenumberstr='06-44-26-75-82')
        db.session.add_all([u1, u2, u3])
        db.session.commit()

    def test_user_isstudent(self):
        u1 = User(username='romain', email='r@example.com', student=True)
        u2 = User(username='david', email='d@example.com', student=False)
        db.session.add_all([u1, u2])
        db.session.commit()

        r  = User.query.filter_by(username='romain').one()
        d  = User.query.filter_by(username='david').one()

        self.assertTrue(r.student)
        self.assertFalse(d.student)

    def test_user_billing(self):
        young = User(username='jeune', email='j@example.com', birthdate=datetime(2004, 12, 9))
        old = User(username='age', email='ag@example.com', birthdate=datetime(1970, 12, 9))
        student = User(username='romain', email='r@example.com', student=True)
        notStudent = User(username='david', email='d@example.com', student=False, birthdate=datetime(1970, 12, 9))

        self.assertEqual(young.get_billing(), 25)
        self.assertEqual(old.get_billing(), 30)
        self.assertEqual(student.get_billing(), 25)
        self.assertEqual(notStudent.get_billing(), 30)

    def test_user_has_team(self):
        t1 = Team(teamname='Sportif', sport_level = SportLevel.TOUGH)
        u1 = User(username='jeune', email='j@example.com', birthdate=datetime(2004, 12, 9))
        db.session.add(t1)
        db.session.add(u1)

        self.assertFalse(u1.has_team())

        t1.subscribe(u1)
        self.assertTrue(u1.has_team())
        self.assertTrue(t1.is_player(u1))

        t1.unsubscribe(u1)
        self.assertFalse(t1.is_player(u1))
        self.assertFalse(u1.has_team())

if __name__ == '__main__':
    unittest.main(verbosity=2)
