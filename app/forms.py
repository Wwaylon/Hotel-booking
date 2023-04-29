from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, DateField, IntegerField, SelectField, RadioField, FloatField, DecimalRangeField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Optional, NumberRange
from app.models import User


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    f_name = StringField('First Name', validators=[DataRequired()])
    l_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[DataRequired()])
    submit = SubmitField('Submit')

class HotelSearchForm(FlaskForm):
    location = StringField('Location', validators=[DataRequired()], render_kw=dict(class_='location-form', placeholder='Where to?'))
    check_in = DateField('Check-in Date', format='%Y-%m-%d', validators=[DataRequired()])
    check_out = DateField('Check-out Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Search')

class CheckInCheckOutForm(FlaskForm):
    check_in = DateField('Check-in Date', format='%Y-%m-%d', validators=[DataRequired()])
    check_out = DateField('Check-out Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Update')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw=dict(class_='email-form', placeholder='email@placeholder.com'))
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class ReserveRoomForm(FlaskForm):
    reward_point_discount = BooleanField('Redeem 100 points for 10% of your next reservation', validators=[Optional()])
    reserve = SubmitField('Reserve')

class SeeAvailableRoomsForm(FlaskForm):
    submit = SubmitField('See Available Rooms')

class CancelReservationForm(FlaskForm):
    submit = SubmitField('Confirm Cancellation')

class RedeemPointsForm(FlaskForm):
    redeem = BooleanField('Redeem 100 points for a free night stay', validators=[DataRequired(message='You must check this box to confirm redemption.')])
    submit = SubmitField('Redeem Points')

class FilterForm(FlaskForm):
    wifi = BooleanField('Wifi', validators=[Optional()])
    pool = BooleanField('Pool', validators=[Optional()])
    hot_tub = BooleanField('Hot Tub', validators=[Optional()])
    gym = BooleanField('Gym', validators=[Optional()])
    spa = BooleanField('Spa', validators=[Optional()])
    parking = BooleanField('Parking', validators=[Optional()])
    elevator = BooleanField('Elevator', validators=[Optional()]) 
    wheelchair = BooleanField('Wheelchair-accessible parking', validators=[Optional()])
    min_rating = DecimalRangeField('Minimum Rating', validators=[Optional()], default=0, places=1, render_kw=dict(step=0.1))
    max_rating = DecimalRangeField('Maximum Rating', validators=[Optional()], default=5, places=1, render_kw=dict(step=0.1))
    filter = SubmitField('Filter')