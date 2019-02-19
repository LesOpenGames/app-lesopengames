import os
import stripe

from flask_login import current_user, login_required
from flask import render_template, request
from flask_babel import _

from app import db
from app.billing import bp
from app.models import Team

stripe_keys = {
  'stripe_secret_key': os.environ['STRIPE_SECRET_KEY'],
  'stripe_publishable_key': os.environ['STRIPE_PUBLISHABLE_KEY']
}

stripe.api_key = stripe_keys['stripe_secret_key']

@bp.route('/stripe_billing')
@login_required
def stripe_billing():
    team_id = request.args.get('team_id')
    amount = request.args.get('amount')
    return render_template('stripe_billing.html', team_id=team_id, amount=amount, key=stripe_keys['stripe_publishable_key'])

@bp.route('/check_billing')
@login_required
def check_billing():
    amount = request.args.get('amount')
    return render_template('check_billing.html', amount=amount)

@bp.route('/charge', methods=['POST'])
@login_required
def charge():
    if( current_user.email  is None ):
        flash(_('Login pb'))
        return redirect(url_for('main.index'))
    user_email = current_user.email

    team_id = request.form['team_id']
    team = Team.query.get(team_id)

    # Amount in cents
    cent_amount = int(float(request.form['cent_amount']))
    eur_amount = int(cent_amount)/100

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

    # remember we paid for that team
    if team is not None:
        team.is_striped = True
        db.session.commit()

    return render_template('stripe_charge.html', title='Team: {}'.format(team.teamname), amount=eur_amount)
