from flask import render_template, flash, redirect, url_for, request, g, current_app
from werkzeug.urls import url_parse
from datetime import datetime
from flask_login import current_user, login_required
from flask_babel import _, get_locale

from sqlalchemy.exc import IntegrityError
from app import db
from app.models import User, Post, Team, Challenge, Score
from app.models import RolesType, SportLevel
from app.main.forms import EditChallengeForm, EditProfileForm, PostForm, EditTeamForm, SetAuthForm
from app.main import bp

import math

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

def get_teams_by_challenge(challenge_id):
    teams_by_challenge = [t for t in Team.query.all() if t.is_valid()] 
    teams_by_challenge = sorted(teams_by_challenge,
            key= lambda t: t.get_score_by_challenge(challenge_id),
            reverse=True)
    return teams_by_challenge

@bp.route('/score_team', methods=['GET', 'POST'])
@login_required
def score_team():
    if( not ( current_user.is_juge() or current_user.is_admin() )):
        flash( _('Sorry, you cant score team'))
        return redirect(url_for('main.index') )
    #get params
    team_id = request.form.get('team_id', None, type=int)
    challenge_id = request.form.get('challenge_id', None, type=int)
    score = request.form.get('score', None, type=int)
    #return "Teamid: {}, Challengeid: {}, score: {}".format(team_id, challenge_id, score)
    #sanity checks
    if( challenge_id==None or team_id == None or score==None):
        flash("wrong team scoring: Teamid = {}, Challengeid = {}, score = {}".format(team_id, challenge_id, score))
        return redirect(url_for('main.index') )
    challenge = Challenge.query.get(challenge_id)
    team = Team.query.get(team_id)
    if( team is None ):
        flash(_('No such Team'))
        return redirect( url_for('main.index'))
    if( challenge is None ):
        flash(_('No such Challenge'))
        return redirect( url_for('main.index'))
    #set each player score
    for p in team.get_players():
        try:
            s = Score.query.filter( Score.challenge_id == challenge_id ).filter( Score.player_id == p.id).one()
            s.score=math.ceil(score/4)
        except:
            flash(_('No such score for challenge %(cid)s player %(uid)s', cid=challenge_id, uid=p.id))
    db.session.commit()
    return redirect( url_for('main.edit_challenge', challenge_id=challenge_id) )

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
        flash( _('Juge successfully changed') )
        return redirect( url_for('main.challenge', challenge_id=challenge.id) )
    form.juge_id.data=challenge.get_juge().id if challenge.get_juge() else 1
    return render_template('edit_challenge.html',
            title=_('Edit Challenge'),
            form=form,
            challenge=challenge,
            teams=get_teams_by_challenge(challenge.id))

@bp.route('/challenge/<int:challenge_id>')
@login_required
def challenge(challenge_id):
    challenge = Challenge.query.filter_by(id=challenge_id).first_or_404()
    if( not ( current_user.is_admin()
        or ( challenge.juge_id == current_user.id ) ) ):
        flash( _('Sorry, you cant view challenge') )
        return redirect(url_for('main.index'))
    return render_template('challenge.html',
            title=_('Challenge'),
            challenge=challenge,
            teams=get_teams_by_challenge(challenge.id))

@bp.route('/challenges')
def challenges():
    challenges=Challenge.query.all()
    return render_template('challenges.html', title=_('Challenges'), challenges=challenges)

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    teams = sorted(Team.query.all(),
            key= lambda t: t.get_team_number() if t.get_team_number() else 2000)
    return render_template('index.html', title=_('Home Page'), teams=teams)

@bp.route('/rating', methods=['GET', 'POST'])
def rating():
    sport_teams = sorted(Team.query.filter(Team.sport_level==int(SportLevel.TOUGH)).all(),
            key= lambda t: t.get_score_total(), reverse=True)
    easy_teams = sorted(Team.query.filter(Team.sport_level==int(SportLevel.EASY)).all(),
            key= lambda t: t.get_score_total(), reverse=True)
    return render_template('rating.html', title=_('General Rating'), easy_teams=easy_teams, sport_teams=sport_teams, is_scoring=True)

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
        user.valid_health=form.health.data
        db.session.commit()
        return redirect ( request.referrer )
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
