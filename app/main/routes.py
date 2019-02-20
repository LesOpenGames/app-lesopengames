from flask import render_template, flash, redirect, url_for, request, g, current_app
from werkzeug.urls import url_parse
from datetime import datetime
from flask_login import current_user, login_required
from flask_babel import _, get_locale

from sqlalchemy.exc import IntegrityError
from app import db
from app.models import User, Post, Team, RolesType

from app.main.forms import EditProfileForm, PostForm, EditTeamForm, SetAuthForm
from app.main import bp

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())

@bp.route('/documents')
def documents():
    return render_template('documents.html', title=_('Mandatory documents'))

@bp.route('/rules')
def rules():
    return render_template('rules.html', title=_('Rules'))

@bp.route('/contact')
def contact():
    return render_template('contact.html', title=_('Contact'))

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    teams = Team.query.all()
    return render_template('index.html', title=_('Home Page'), teams=teams)

def old_index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash( _('Post published'))
        return redirect(url_for('main.index'))
    page_num = request.args.get('page_num', 1, type=int)
    posts = current_user.followed_posts().paginate(
            page_num, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page_num=posts.next_num)\
            if posts.has_next else None
    prev_url = url_for('main.index', page_num=posts.prev_num)\
            if posts.has_prev else None
    return  render_template('index.html', title=_('Home Page'), form=form, posts=posts.items,
            next_url=next_url, prev_url=prev_url)

@bp.route('/explore', methods=['GET', 'POST'])
def explore():
    page_num = request.args.get('page_num', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
            page_num, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page_num=posts.next_num)\
            if posts.has_next else None
    prev_url = url_for('main.explore', page_num=posts.prev_num)\
            if posts.has_prev else None
    return  render_template('index.html', title=_('Explore'), posts=posts.items,
            next_url=next_url, prev_url=prev_url)

@bp.route('/notitle')
def notitle():
    return  render_template('index.html')

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
    if( not ( current_user.is_admin() or user.team.is_leader(current_user) or current_user.id == user_id ) ):
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

@bp.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if( not current_user.is_admin() ):
        flash( _('You dont have access to such page'))
        return redirect(url_for('main.index'))
    user = User.query.get(user_id)
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
    users = User.query.all()
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
    # Check valid players  or Unvalidate team
    if( team.get_team_number() is None ):
        if ( team.is_valid() ):
            team.set_team_number()
            db.session.commit()
    else:
        if ( not team.is_valid() ):
            team.unset_team_number()
            db.session.commit()
    return render_template('edit_team.html', title=_('Edit Team'), form=form, team=team)

@bp.route('/teams', methods=['GET', 'POST'])
@login_required
def teams():
    if( current_user.role  != RolesType.ADMIN ):
        flash( _('You dont have access to such page'))
        return redirect(url_for('main.index') )
    teams = Team.query.all()
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
