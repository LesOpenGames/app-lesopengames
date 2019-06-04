from flask import render_template, flash, redirect, url_for, request, g, current_app
from werkzeug.urls import url_parse
from datetime import datetime
from flask_login import current_user, login_required
from flask_babel import _, get_locale

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from builtins import AttributeError
from app import db
from app.models import User, Post, Team, Challenge, Score
from app.models import RolesType, SportLevel, ChallScoreType, ChallTeamType
from app.models import str2secs
from app.main.forms import EditChallengeForm, EditProfileForm, PostForm, EditTeamForm, SetAuthForm
from app.main import bp

import math
import enum

SortedRanks = [0]*32

SortedRanks[0]=32
SortedRanks[1]=28
SortedRanks[2]=24
SortedRanks[3:4]=[20]*2
SortedRanks[5:8]=[16]*4
SortedRanks[9:15]=[12]*6
SortedRanks[16:23]=[8]*7
SortedRanks[24:31]=[4]*7

TournaRanksTeam =[
    ("non classé", 0),
    ("1er", 32),
    ("2ème", 28),
    ("3ème", 24),
    ("4ème", 20),
    ("5-8ème", 16),
    ("9-12ème", 12),
    ("13-16ème", 8)
        ]

TournaRanksIndiv = [
    ("non classé", 0),
    ("1er", 22),
    ("2ème", 20),
    ("3ème", 18),
    ("4ème", 16),
    ("5-6ème", 14),
    ("7-8ème", 12),
    ("Demi-3T", 10),
    ("Demi-2T", 8),
    ("Demi-1T", 6),
    ("Élim-3T", 4),
    ("Élim-2T", 2),
    ("Élim-1T", 1)
        ]


def set_team_score(challenge_id,
        team_id,
        score,
        chrono=None,
        tourna=None,
        bonus=None,
        distance=None):
    scores = Score.query.filter( Score.challenge_id == challenge_id ).filter( Score.team_id == team_id).all()
    for s in scores:
        s.score=math.ceil(score/4)
        s.chrono=chrono
        s.tourna=tourna
        s.bonus=bonus
        s.distance=distance
    db.session.commit()


def set_user_score(challenge_id,
        player_id,
        score,
        chrono,
        tourna,
        bonus,
        distance):
    try:
        s = Score.query.filter( Score.challenge_id == challenge_id ).filter( Score.player_id == player_id).one()
        s.score=score
        s.chrono=chrono
        s.tourna=tourna
        s.bonus=bonus
        s.distance=distance
    except:
       flash(_('No such score for challenge %(cid)s player %(uid)s', cid=challenge_id, uid=player_id))
    #flash(_('Score changed for challenge %(cid)s player %(uid)s', cid=challenge_id, uid=player_id))
    db.session.commit()


def get_tourna_ranks( challenge_team_type ):
    ranks_tuple   =  []
    if( challenge_team_type == ChallTeamType.INDIV ):
        ranks_tuple = TournaRanksIndiv
    elif( challenge_team_type == ChallTeamType.TEAM ):
        ranks_tuple = TournaRanksTeam
    else:
        return []
    tourna_ranks  = [ {'value': idx, 'name': r[0], 'points': r[1]} for idx, r in enumerate( ranks_tuple ) ]
    return tourna_ranks


def get_categorized_teams( teams):
    categorized_teams={
            'easy_teams':filter( lambda t: t.sport_level == int(SportLevel.EASY), teams),
            'sport_teams':filter( lambda t: t.sport_level == int(SportLevel.TOUGH), teams)
            }
    return categorized_teams

def get_teams_by_challenge(challenge_id):
    teams_by_challenge = [t for t in Team.query.all() if t.is_valid()] 
    teams_by_challenge = sorted(teams_by_challenge,
            key= lambda t: t.get_score_by_challenge(challenge_id),
            reverse=True)
    return teams_by_challenge

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())

@bp.route('/apropos')
def apropos():
    return render_template('apropos.html', title=_('A Propos'))

@bp.route('/certificat')
def certificat():
    return render_template('certificat.html', title=_('Health Certificat'))

@bp.route('/autorisation')
def autorisation():
    return render_template('autorisation.html', title=_('Minor Authorisation'))

@bp.route('/rules')
def rules():
    return render_template('rules.html', title=_('Rules'))

@bp.route('/contact')
def contact():
    return render_template('contact.html', title=_('Contact'))

@bp.route('/score_player', methods=['GET', 'POST'])
@bp.route('/score_team', methods=['GET', 'POST'])
@login_required
def score_team():

    if( not ( current_user.is_juge() or current_user.is_admin() )):
        flash( _('Sorry, you cant score team'))
        return redirect(url_for('main.index') )

    #get params
    team_id = request.form.get('team_id', None, type=int)
    player_id = request.form.get('player_id', None, type=int)
    challenge_id = request.form.get('challenge_id', None, type=int)
    score = request.form.get('score', None, type=int)
    chrono = request.form.get('chrono', None, type=str)
    tourna = request.form.get('tourna', None, type=int)
    bonus = request.form.get('bonus', None, type=int)
    distance = request.form.get('distance', None, type=int)

    #sanity checks
    if( challenge_id==None or
            ( player_id == None and team_id == None ) or
            ( score==None and chrono==None and tourna==None and bonus == None and distance==None)):
        flash("wrong team scoring: Teamid = {}, Userid = {}, Challengeid = {}, score = {}, chrono={}, tourna={}, bonus={}, distance={}"
            .format(team_id, player_id, challenge_id, score, chrono, tourna, bonus, distance))
        return redirect(url_for('main.index') )

    if( chrono is not None ):
        try:
            chrono = str2secs( chrono )
        except AttributeError:
            flash(_("Wrong chrono format; use something like 22m12s"))
            return redirect(request.referrer )

    challenge = Challenge.query.get(challenge_id)
    if( challenge is None ):
        flash(_('No such Challenge'))
        return redirect( url_for('main.index'))

    # decide wether we score team or player
    if( "team" in request.path ):
        team = Team.query.get(team_id)
        if( team is None ):
            flash(_('No such Team'))
            return redirect( url_for('main.index'))
        #set each player's score
        if( score is not None ):
            score=math.ceil(score/4)
        for p in team.get_players():
            set_user_score(challenge.id, p.id, score, chrono, tourna, bonus, distance)
        flash(_('Score changed for Team %(teamname)s', teamname=team.teamname))
        anchor='team_{}'.format(team.id)
    elif( "player" in request.path ):
        player = User.query.get(player_id)
        if( player is None ):
            flash(_('No such Player'))
            return redirect( url_for('main.index'))
        #set player's score
        set_user_score(challenge.id, player.id, score, chrono, tourna, bonus, distance)
        flash(_('Score changed for Player %(playername)s', playername=player.username))
        anchor='team_{}'.format(player.team.id)
    else:
        flash(_('Wrong Score Path'))
        return redirect( url_for('main.index'))

    update_ranks( challenge_id )

    return redirect( url_for('main.edit_challenge', challenge_id=challenge_id , _anchor=anchor))

@bp.route('/edit_challenge/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def edit_challenge(challenge_id):
    #sanity checks
    challenge = Challenge.query.get(challenge_id)
    if( challenge is None):
        flash(_('No such challenge for id %(id)s', id=challenge_id))
        return redirect(url_for('main.index'))
    if( not ( current_user.is_admin() )):
        flash( _('Sorry, you cant modify challenge %(name)s', name=challenge.name))
        return redirect(url_for('main.index') )
    form = EditChallengeForm(meta={'csrf': False})
    juges = User.query.filter(User.role==int(RolesType.JUGE)).filter( User.firstname!=None).filter( User.secondname!=None)
    juges_list = [(int(j.id), j.firstname+" "+j.secondname) for j in juges ]
    form.juge_id.choices=juges_list
    if form.validate_on_submit():
        challenge.set_juge(User.query.get(form.juge_id.data))
        #challenge.score_type=form.score_type.data
        db.session.commit()
        flash( _('Challenge successfully changed') )
        return redirect( url_for('main.challenge', challenge_id=challenge.id) )
    form.juge_id.data=challenge.get_juge().id if challenge.get_juge() else 1
    #challenged_teams=get_teams_by_challenge(challenge.id)
    #easy_teams = challenged_teams.filter( lambda x : x.sport_level == int(Sport
    categorized_teams = get_categorized_teams( get_teams_by_challenge( challenge.id ))
    tourna_ranks = get_tourna_ranks( challenge.team_type )
    return render_template('edit_challenge.html',
            title=_('Edit Challenge'),
            form=form,
            challenge=challenge,
            tourna_ranks = tourna_ranks,
            categorized_teams=categorized_teams)

@bp.route('/challenge/<int:challenge_id>')
def challenge(challenge_id):
    challenge = Challenge.query.filter_by(id=challenge_id).first_or_404()
    categorized_teams = get_categorized_teams( get_teams_by_challenge( challenge.id ))
    tourna_ranks = get_tourna_ranks( challenge.team_type )
    return render_template('challenge.html',
            title=_('Challenge'),
            challenge=challenge,
            tourna_ranks = tourna_ranks,
            categorized_teams=categorized_teams)

@bp.route('/challenges')
def challenges():
    challenges=Challenge.query.all()
    return render_template('challenges.html', title=_('Challenges'), challenges=challenges)

@bp.route('/update_ranks/<int:challenge_id>')
def update_ranks(challenge_id):
    challenge = Challenge.query.filter_by(id=challenge_id).first_or_404()
    # Update rank for all challenges types except points one which is already scored
    if( challenge.is_points_type() ):
        return redirect( url_for('main.challenge', challenge_id=challenge.id) )
    if( challenge.score_type == ChallScoreType.TOURNAMENT ):
        challenge_team_scores = Score.query.filter( Score.challenge_id == challenge_id )
        for s in challenge_team_scores:
            tourna = s.tourna
            tourna_ranks = get_tourna_ranks( challenge.team_type)

            if( tourna is not None ):
                score = tourna_ranks[tourna]['points']
            else:
                score = 0

            if( challenge.team_type == ChallTeamType.TEAM):
                s.score = math.ceil(  score / 4)
            else:
                s.score = score
            set_user_score(challenge_id, s.player_id, s.score, s.chrono, s.tourna, s.bonus, s.distance)
    elif( challenge.team_type == ChallTeamType.TEAM ):
        for sport_level in (int(SportLevel.EASY), int(SportLevel.TOUGH)): 
            if( challenge.is_chrono_type() ):
                stmt = db.session.query(Score.team_id, func.max(Score.chrono).label('chrono') ).\
                        filter(Score.challenge_id == challenge.id).\
                        group_by(Score.team_id).subquery()
                sorted_teams = db.session.query(Team, stmt.c.chrono).\
                        order_by( stmt.c.chrono.asc() ).\
                        filter(Team.sport_level == sport_level).\
                        filter(stmt.c.chrono.isnot(None) ).\
                        filter(stmt.c.chrono !=0 ).\
                        outerjoin(stmt, stmt.c.team_id == Team.id)
            elif( challenge.is_distance_type() ):
                stmt = db.session.query(Score.team_id, func.max(Score.distance).label('distance') ).\
                        filter(Score.challenge_id == challenge.id).\
                        group_by(Score.team_id).subquery()
                sorted_teams = db.session.query(Team, stmt.c.distance).\
                        order_by( stmt.c.distance.desc() ).\
                        filter(Team.sport_level == sport_level).\
                        filter(stmt.c.distance.isnot(None) ).\
                        filter(stmt.c.distance !=0 ).\
                        outerjoin(stmt, stmt.c.team_id == Team.id)
            elif( challenge.is_bonus_type() ):
                stmt = db.session.query(Score.team_id, func.max(Score.bonus).label('bonus') ).\
                        filter(Score.challenge_id == challenge.id).\
                        group_by(Score.team_id).subquery()
                sorted_teams = db.session.query(Team, stmt.c.bonus).\
                        order_by( stmt.c.bonus.desc() ).\
                        filter(Team.sport_level == sport_level).\
                        filter(stmt.c.bonus.isnot(None) ).\
                        filter(stmt.c.bonus !=0 ).\
                        outerjoin(stmt, stmt.c.team_id == Team.id)
            sorted_teams_list = sorted_teams.all()
            for idx, (team, value) in enumerate(sorted_teams_list):
                # or deal with equality
                while idx > 0 and value == sorted_teams_list[idx-1][1]:
                    idx = idx -1
                score = SortedRanks[ idx ] 
                if( challenge.is_chrono_type() ):
                    set_team_score(challenge.id, team.id, score, chrono=value)
                elif( challenge.is_distance_type() ):
                    set_team_score(challenge.id, team.id, score, distance=value)
                elif( challenge.is_bonus_type() ):
                    set_team_score(challenge.id, team.id, score, bonus=value)
    db.session.commit()
    return redirect( url_for('main.challenge', challenge_id=challenge.id) )

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    teams = sorted(Team.query.all(),
            key= lambda t: t.get_team_number() if t.get_team_number() else 2000)
    return render_template('index.html', title=_('Home Page'), teams=teams)

@bp.route('/rating', methods=['GET', 'POST'])
def rating():
    all_teams = sorted( Team.query.all() , key=lambda t: t.get_score_total() , reverse=True)
    categorized_teams = get_categorized_teams( all_teams )
    return render_template('rating.html', title=_('General Rating'), categorized_teams=categorized_teams, is_scoring=True)

@bp.route('/posts')
@login_required
def posts():
    all_users = User.query.all()
    posts = []
    for u in all_users:
        posts.append( { 'author': u, 'body': 'This is my body' })
    return render_template('posts.html', title=_('All Posts'), posts=posts)

@bp.route('/user/<int:user_id>')
@login_required
def user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    if( not ( current_user.is_admin()
              or ( user.team is not None and user.team.is_leader(current_user) )
              or current_user.id == user_id ) ):
        flash( _('Sorry, you cant view user') )
        return redirect(url_for('main.index'))

    page_num = request.args.get('page_num', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
            page_num, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page_num=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page_num=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', title=_('User Profile'), user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

#TODO: merge some code between create_profile and edit_profile

@bp.route('/create_profile', methods=['GET', 'POST'])
@login_required
def create_profile():
    # manage the 'from edit_team' scenario
    team = None
    team_id = request.args.get('team_id')
    form = EditProfileForm()
    if( team_id is not None ):
        team = Team.query.get(team_id)
        if ( team is None ):
            flash( _('No such team'))
            return render_template('index.html', title=_('Home Page'))
    if form.validate_on_submit():
        user = User()
        user.role = int(RolesType.PLAYER)
        form2user(form, user)
        db.session.add(user)
        if ( team is not None ):
            team.subscribe( user )
        db.session.commit()
        if( team is not None):
            flash(_('Sucessfully added player to team'))
            if( not user.is_valid_age() ):
                flash(_('Warning: age is to low for this team level'))
            return redirect( url_for('main.edit_team', team_id=team.id) )
        else:
            flash(_('Sucessfully created user'))
            return redirect( url_for('main.user', user_id=user.id) )
    return render_template('edit_profile.html', title=_('Create User'), form=form)

@bp.route('/check_docs/<int:user_id>', methods=['GET', 'POST'])
@login_required
def check_docs(user_id):
    if( not current_user.is_admin() ):
        flash( _('Sorry, you cant check players docs') )
        return redirect(url_for('main.index') )
    form = SetAuthForm(meta={'csrf': False})
    user = User.query.get(user_id)
    if( user is None ):
        flash(_('No such User'))
        return redirect(url_for('main.index'))
    if form.validate_on_submit():
        user.valid_auth=form.auth.data
        user.valid_health=True
        db.session.commit()
        anchor='player_{}'.format(user.id)
        return redirect( url_for('main.edit_team', team_id=user.team.id, _anchor=anchor) )
        #return redirect(url_for('main.index') )
    flash(_('You cant call that page'))
    return redirect(url_for('main.index') )

@bp.route('/edit_profile', methods=['GET', 'POST'])
@bp.route('/edit_profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id=-1):
    if( user_id == -1 or current_user.id == user_id ): # url called with no arg or ourself
        user = current_user
    else: # trying to edit other user than us
        user = User.query.get(user_id)
        # Is there such id in base ?
        if( user is None ):
            flash(_('No such User'))
            return redirect(url_for('main.index'))
        # Do we have auth to edit ?
        current_is_leader = ( user.team is not None and user.team.is_leader(current_user) )
        current_is_admin  = current_user.role  == RolesType.ADMIN
        if not ( current_is_leader or current_is_admin ):
            flash(_('Unable to edit such User '))
            return redirect(url_for('main.index'))
    # else ... well, go on
    form = EditProfileForm(obj=user)
    if form.validate_on_submit():
        form2user(form, user)
        db.session.commit()
        flash(_('Sucessfully updated your profile'))
        # where do we come from ?
        next_page = form.next_page.data or 'index'
        if ( 'edit_team' in next_page ):
            if( not user.is_valid_age() ):
                flash(_('Warning: age is to low for this team level'))
            return redirect( url_for('main.edit_team', team_id=user.team_id) )
        elif ( 'users' in next_page ):
            return redirect( url_for('main.users') )
        else:
            return redirect(url_for('main.user', user_id=user.id))
    form.next_page.data = request.referrer # store for redirect after validation
    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)

def form2user(form, user):
    user.username = form.username.data
    user.firstname = form.firstname.data
    user.secondname = form.secondname.data
    user.gender = form.gender.data
    user.birthdate = form.birthdate.data
    user.weight = form.weight.data
    user.email = form.email.data
    user.phonenumberstr = form.phonenumberstr.data
    user.student = form.student.data

@bp.route('/leave_team/<int:user_id>')
def leave_team(user_id):
    user = User.query.get(user_id)
    if( user is None ):
        flash( _('No such user') )
        return redirect(url_for('main.index'))
    if( not current_user.is_admin() 
              and ( current_user.id != user_id ) ):
        flash( _('You dont have access to such page'))
        return redirect(url_for('main.index'))
    if( not user.has_team() ):
        flash( _('You have no team to leave'))
        return redirect(url_for('main.index'))

    user.team.unsubscribe(user)
    db.session.commit()
    flash( _('Sucessfully quitted team'))
    return redirect(url_for('main.index'))

@bp.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if( not current_user.is_admin() ):
        flash( _('You dont have access to such page'))
        return redirect(url_for('main.index'))
    user = User.query.get(user_ie)
    if( user is None ):
        flash( _('No such user') )
        return redirect(url_for('main.index'))
    db.session.delete(user)
    db.session.commit()
    flash( _('User %(username)s deleted', username=user.username))
    return redirect(url_for('main.index'))

@bp.route('/users')
@login_required
def users():
    if( current_user.role  != RolesType.ADMIN ):
        flash( _('You dont have access to such page'))
        return redirect(url_for('main.index') )
    users = User.query.order_by(User.secondname.asc()).all()
    return render_template('users.html', title=_('Users Admin List'), users=users, admin=True)

@bp.route('/team/<team_id>')
@login_required
def team(team_id):
    team = Team.query.filter_by(id=team_id).first_or_404()
    if( not ( current_user.is_admin() or
        (( current_user.team is not None) and  current_user.team.id != team_id ) )):
        flash( _('Sorry, you cant see team %(name)s', name=team.teamname))
        return redirect(url_for('main.index') )
    return render_template('team.html', title=_('Team'), team=team)

@bp.route('/team_scores/<team_id>')
def team_scores(team_id):
    team = Team.query.filter_by(id=team_id).first_or_404()
    stmt = db.session.query(Score.challenge_id, func.sum(Score.score).label('score_total') ).\
	    filter(Score.team_id == team.id).\
	    group_by(Score.challenge_id).subquery()
    joined = db.session.query(Challenge.challenge_name, stmt.c.score_total).\
	    outerjoin(stmt, stmt.c.challenge_id == Challenge.id)
    team_scores = [{'name': name, 'total': total} for name, total in joined.all()]
    return render_template('team_scores.html', title=_('Team Scores'), team_scores=team_scores, team=team)

def flash_team_non_valid(team):
    if team.is_valid():
        return
    message=""
    if not team.is_paid:
        if team.is_striped:
            flash(_('Paiment striped, waiting for validation'), 'warning')
        else:
            flash(_('Waiting for Paiment'), 'warning')
    for u in team.get_players():
        if not u.is_valid():
            if not u.is_valid_age():
                flash(_('Wrong birthdate for %(username)s', username=u.username), 'warning')
            if not u.is_valid_health():
                flash(_('Missing health doc for %(username)s', username=u.username), 'warning')
            if not u.is_valid_auth():
                flash(_('Missing parent auth doc for %(username)s', username=u.username), 'warning')

##
# First create team with name and level
#  (later fill it with editing )
@bp.route('/create_team', methods=['GET', 'POST'])
@login_required
def create_team():
    if( current_user.team is not None):
        flash( _('Sorry, you already belong to team %(name)s', name=current_user.team.teamname))
        return redirect( url_for('main.index') )
    form = EditTeamForm()
    if form.validate_on_submit():
        teamname=form.teamname.data
        team = Team(teamname=teamname)
        team.sport_level = form.sportlevel.data
        # set role if no role
        if( current_user.role is None ):
            current_user.role = int(RolesType.PLAYER)
        # subscribe to team only if is player
        if( current_user.role == RolesType.PLAYER ):
            team.subscribe(current_user)
        db.session.add(team)
        try:
            db.session.commit()
        except IntegrityError as err:
            if "duplicate key value violates unique constraint" in str(err):
                flash( _('Name %(newteamname)s already exist', newteamname=teamname))
                return redirect( url_for('main.create_team') )
            else:
                flash( _('Problem Occured with creating team')  )
                flash ( str(err) )
                return redirect(url_for('main.index') )
        flash( _('Team %(teamname)s created', teamname=teamname))
        return redirect( url_for('main.edit_team', team_id=team.id) )
    return render_template('create_team.html', title=_('Create Team'), form=form)

@bp.route('/join_team')
@bp.route('/join_team/<int:team_id>')
@login_required
def join_team(team_id=-1):
    if( team_id == -1 ):
        teams = Team.query.filter_by(is_open=True).all()
        if( len( teams ) == 0 ):
            flash(_('Sorry, no open team available') )
        return render_template('join_team.html', title=_('Join Team'), teams=teams)
    else:
        team = Team.query.get(team_id)
        if( team is None ):
            flash(_('No such Team'))
            return redirect( url_for('main.join_team'))
        elif( current_user.has_team() ):
            flash(_('You cant join a team as you already have one'))
            return redirect( url_for('main.join_team'))
        elif( len( team.get_players() ) >= 4 ):
            flash(_('You cant join team as it is already full'))
            return redirect( url_for('main.join_team'))
        elif( not team.is_open ):
            flash(_('You cant join team as it is not open to subscribing'))
            return redirect( url_for('main.join_team'))
        else:
            team.subscribe(current_user)
            db.session.commit()
            flash(_('Successfully joined team'))
            return redirect(url_for('main.team', team_id=team_id) )

@bp.route('/delete_team/<int:team_id>', methods=['GET', 'POST'])
@bp.route('/edit_team/<int:team_id>', methods=['GET', 'POST'])
@login_required
def edit_team(team_id):
    # check security
    team=Team.query.filter_by(id=team_id).first()
    if( team is None ):
        flash( _('No such team for id %(team_id)s', team_id=team_id))
        return redirect(url_for('main.index') )
    if( not ( current_user.is_admin() or
        (( current_user.team is not None) and  current_user.team.id == team_id ) )):
        flash( _('Sorry, you cant modify team %(name)s', name=team.teamname))
        return redirect(url_for('main.index') )
    # did we ask for delete ?
    if( "delete" in request.path ):
        db.session.delete(team)
        db.session.commit()
        flash( _('Team %(teamname)s deleted', teamname=team.teamname))
        return redirect( url_for('main.teams') )
    # or we just want to modify ?
    form = EditTeamForm(obj=team)
    if form.validate_on_submit():
        newteamname = form.teamname.data
        team.teamname= newteamname
        #team.sport_level = form.sportlevel.data
        team.racket_sport_type = form.racksport.data
        team.collective_sport_type = form.collsport.data
        team.is_paid = form.is_paid.data
        team.is_partner = form.is_partner.data
        team.is_open = form.is_open.data
        try:
            db.session.commit()
        except IntegrityError as err:
            if "UNIQUE constraint failed: team.teamname" in str(err):
                flash( _('Name %(newteamname)s already exist', newteamname=newteamname))
                return redirect( url_for('main.edit_team', team_id=team_id) )
            else:
                flash( _('Problem Occured with modifying team') )
                return redirect(url_for('main.index') )
        flash( _('Team %(teamname)s modified', teamname=team.teamname))
        return redirect(url_for('main.team', team_id=team_id) )
    elif request.method == 'GET':
        form.sportlevel.data = team.sport_level
        form.racksport.data = team.racket_sport_type
        form.collsport.data = team.collective_sport_type
        form.is_paid.data = team.is_paid
        form.is_partner.data = team.is_partner
        form.is_open.data = team.is_open
    # Check valid players  or Unvalidate team
    if( team.get_team_number() is None ):
        if ( team.is_valid() ):
            team.set_team_number()
            db.session.commit()
    else:
        if ( not team.is_valid() ):
            team.unset_team_number()
            db.session.commit()
    #flash_team_non_valid(team)
    return render_template('edit_team.html', title=_('Edit Team'), form=form, team=team)

@bp.route('/teams', methods=['GET', 'POST'])
@login_required
def teams():
    if( current_user.role  != RolesType.ADMIN ):
        flash( _('You dont have access to such page'))
        return redirect(url_for('main.index') )
    teams = sorted(Team.query.all(),
            key= lambda t: t.get_team_number() if t.get_team_number() else 2000)
    return render_template('index.html', title=_('Teams Admin List'), teams=teams, admin=True)

@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash( _('User %(username)s not found', username=username))
        return redirect(url_for('main.index'))
    if user == current_user.username:
        flash( _('Cannot follow yourself'))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash( _('You are following %(username)s', username=username))
    return redirect(url_for('main.user', username=username))

@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash( _('User %(username)s not found', username=username))
        return redirect(url_for('main.index'))
    if user == current_user.username:
        flash( _('Cannot unfollow yourself'))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash( _('You have unfollowed %(username)s', username=username))
    return redirect(url_for('main.user', username=username))
