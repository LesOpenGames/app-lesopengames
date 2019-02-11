from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, RadioField
from wtforms import IntegerField, DateField, HiddenField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Optional
from app.models import User, SportLevel, CollectiveSportType, RacketSportType, RolesType

class PostForm(FlaskForm):
    post = TextAreaField(_l('Post Body'), validators=[DataRequired(), Length(min=0, max=140)])
    submit = SubmitField(_l('Publish'))

class EditTeamForm(FlaskForm):
    teamname = StringField(_l('Team Name'), validators=[DataRequired()])
    #sportlevel = RadioField(_('Sport Level'), coerce=int, choices=[(0, _('Easy')), (1, _('Tough')) ] )
    #collsport = RadioField(_('Racket Sport'), coerce=int, choices=[(0, _('Flag')), (1, _('Handball')) ] )
    #racksport = RadioField(_('Collective Sport'), coerce=int, choices=[(0, _('PingPong')), (1, _('Badmington')) ] )
    sportlevel = RadioField(_('Sport Level'), coerce=int, choices=[(int(SportLevel.EASY), _('Easy')), (int(SportLevel.TOUGH), _('Tough')) ] , validators=[Optional()])
    collsport = RadioField(_('Collective Sport'), coerce=int, choices=[(int(CollectiveSportType.FLAG), _('Flag')), (int(CollectiveSportType.HAND), _('Handball')) ] , validators=[Optional()])
    racksport = RadioField(_('Racket Sport'), coerce=int, choices=[(int(RacketSportType.PINGPONG), _('PingPong')), (int(RacketSportType.BADMINGTON), _('Badmington')) ] , validators=[Optional()])
    submit = SubmitField(_l('Validate'))

class EditProfileForm(FlaskForm):
    next_page = HiddenField('NextPage')
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About Me'), validators=[Length(min=0, max=140)])
    firstname = StringField(_l('First Name'), validators=[DataRequired()])
    secondname = StringField(_l('Second Name'), validators=[DataRequired()])
    gender = RadioField(_('Gender'), coerce=int, choices=[(0, _('M')), (1, _('F')) ] )
    birthdate = DateField(_l('Birth Date'), format='%d/%m/%Y', render_kw={'placeholder': '25/09/2003'})
    weight = IntegerField(_l('Weight'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    phonenumber =  IntegerField(_l('Phone Number'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))
    # New constructor with param, called in routes.py       
    def __init__(self, original_username='', *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = ''
        self.original_email = ''
        if( kwargs.get('obj') is not None ):
            self.original_username = kwargs.get('obj').username
            self.original_email = kwargs.get('obj').email
    # Username validator, preventing allready used username
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))
#    def validate_birthdate(self, date):
#        raise ValidationError(date.data)
#        if( date is None)
#            raise ValidationError(_('Birthdate required'))
#    def validate_email(self, email):
#        if email.data != self.
#        email = User.query.filter

