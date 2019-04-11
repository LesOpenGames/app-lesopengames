import stripe

from flask_login import current_user, login_required
from flask import render_template, request, current_app, flash, redirect, url_for
from flask_babel import _

from app import db
from app.billing import bp
from app.models import Team, User


@bp.route('/stripe_billing')
@login_required
def stripe_billing():
    team_id = request.args.get('team_id')
    user_id = request.args.get('user_id')
    amount = request.args.get('amount')
    return render_template('stripe_billing.html', team_id=team_id, user_id=user_id, amount=amount, key=current_app.config['STRIPE_PUBLISHABLE_KEY'])

@bp.route('/check_billing')
@login_required
def check_billing():
    amount = request.args.get('amount')
    return render_template('check_billing.html', amount=amount)

@bp.route('/charge', methods=['POST'])
@login_required
def charge():

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    if( current_user.email  is None ):
        flash(_('Login pb'))
        return redirect(url_for('main.index'))
    user_email = current_user.email

    team=None
    team_id = request.form['team_id']
    if( team_id is not None and team_id != 'None'):
        team = Team.query.get(team_id)

    user=None
    user_id = request.form['user_id']
    if( user_id is not None and user_id != 'None'):
        user = User.query.get(user_id)

    # Amount in cents
    cent_amount = int(float(request.form['cent_amount']))
    eur_amount = int(cent_amount)/100

    try:
        customer = stripe.Customer.create(
            email=user_email,
            source=request.form['stripeToken']
        )

        charge = stripe.Charge.create(
            customer=customer.id,
            amount=cent_amount,
            currency='eur',
            receipt_email=user_email,
            description='Les Open Games'
        )
    except stripe.error.InvalidRequestError as err:
        flash(_("Error in stripe request, please contact admins"))
        redirect(url_for('main.index'))

    # remember we paid for that user
    if user is not None:
        user.is_striped = True
        db.session.commit()
    # or for the whole team
    elif team is not None:
        team.is_striped = True
        db.session.commit()

    return render_template('stripe_charge.html', title='Team: {}'.format(team.teamname), amount=eur_amount)
