from flask import render_template, flash, redirect, url_for, request, g
from werkzeug.urls import url_parse
from datetime import datetime
from flask_login import current_user, login_required
from flask_babel import _, get_locale

from app import app, db
from app.models import User, Post

from app.main.forms import EditProfileForm, PostForm
from app.main import bp

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash( _('Post published'))
        return redirect(url_for('main.index'))
    page_num = request.args.get('page_num', 1, type=int)
    posts = current_user.followed_posts().paginate(
            page_num, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page_num=posts.next_num)\
            if posts.has_next else None
    prev_url = url_for('main.index', page_num=posts.prev_num)\
            if posts.has_prev else None
    return  render_template('index.html', title='Home Page', form=form, posts=posts.items,
            next_url=next_url, prev_url=prev_url)

@bp.route('/explore', methods=['GET', 'POST'])
def explore():
    page_num = request.args.get('page_num', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
            page_num, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page_num=posts.next_num)\
            if posts.has_next else None
    prev_url = url_for('main.explore', page_num=posts.prev_num)\
            if posts.has_prev else None
    return  render_template('index.html', title='Explore', posts=posts.items,
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
    return render_template('posts.html', title='All Posts', posts=posts)
@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page_num = request.args.get('page_num', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
            page_num, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page_num=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page_num=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Sucessfully updated your profile'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='User Profile', form=form)

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
