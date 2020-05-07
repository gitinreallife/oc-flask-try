from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import current_user, login_required
from app import db
from app.main.forms import EditProfileForm, PostForm
from app.models import User
from app.main import bp


# The @before_request decorator from Flask register the decorated
# function to be executed right before the view function
@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def indexes():
    nairobi = User.query.filter_by(username='nairobi').first()
    nairobii = User.query.filter_by(username='nairobi2').first()
    posts = [
        {
            'author': nairobi,
            'body': ''''C'est trop jolly!'''
        },
        {
            'author': nairobii,
            'body': 'Sod off'
        }
    ]
    return render_template('index.html', title='Index', posts=posts)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    # dummy posts
    posts = [
        {
            'author': user,
            'body': ''''C'est trop jolly!'''
        },
        {
            'author': user,
            'body': 'Sod off'
        }
    ]
    return render_template('user.html', user=user, posts=posts)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('main.user', username=username))
