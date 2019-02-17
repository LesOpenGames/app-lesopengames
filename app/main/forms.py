import re
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
    sportlevel = RadioField(_l('Sport Level'), coerce=int, choices=[(int(SportLevel.EASY), _l('Easy')), (int(SportLevel.TOUGH), _l('Tough')) ] , validators=[Optional()])
    collsport = RadioField(_l('Collective Sport'), coerce=int, choices=[(int(CollectiveSportType.FLAG), _l('Flag')), (int(CollectiveSportType.HAND), _l('Handball')) ] , validators=[Optional()])
    racksport = RadioField(_l('Racket Sport'), coerce=int, choices=[(int(RacketSportType.PINGPONG), _l('PingPong')), (int(RacketSportType.BADMINGTON), _l('Badmington')) ] , validators=[Optional()])
    submit = SubmitField(_l('Validate'))

class SetAuthForm(FlaskForm):
    health = BooleanField( _l('Health Document'), validators=[Optional()])
    auth = BooleanField(_l('Parent Auth'), validators=[Optional()])
    submit = SubmitField(_l('Validate'))

class EditProfileForm(FlaskForm):
    next_page = HiddenField('NextPage')
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About Me'), validators=[Length(min=0, max=140)])
    firstname = StringField(_l('First Name'), validators=[DataRequired()])
    secondname = StringField(_l('Second Name'), validators=[DataRequired()])
    gender = RadioField(_l('Gender'), coerce=int, choices=[(0, _l('M')), (1, _l('F')) ] , validators=[Optional()])
    birthdate = DateField(_l('Birth Date'), format='%d/%m/%Y', render_kw={'placeholder': '25/09/2003'})
    weight = IntegerField(_l('Weight'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    phonenumberstr =  StringField(_l('Phone Number'), render_kw={'placeholder': '06-18-55-82-33 | 06 18 55 82 33 | 0618558233'}, validators=[Optional()])
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
                raise ValidationError(_l('Please use a different username.'))
    def validate_phonenumberstr(self, phonenumberfield):
        phonenumber = phonenumberfield.data
        if( re.match('\d{10}$', phonenumber)):
            return True
        elif( re.match('\d{10}$', "".join(phonenumber.split('-')))):
            return True
        elif( re.match('\d{10}$', "".join(phonenumber.split(' ')))):
            return True
        else:
            raise ValidationError(_l('Use phone number format: 06-18-55-82-33 | 06 18 55 82 33 | 0618558233'))
#    def validate_birthdate(self, date):
#        raise ValidationError(date.data)
#        if( date is None)
#            raise ValidationError(_l('Birthdate required'))
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=self.email.data).first()
            if user is not None:
                raise ValidationError(_l('Please use a different email'))

