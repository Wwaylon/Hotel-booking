from datetime import datetime
from hashlib import md5
from app import db, login, app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from time import time
import jwt


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reward_points = db.Column(db.Integer, default = 0)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    f_name = db.Column(db.String(64))
    l_name = db.Column(db.String(64))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=mp&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)
    


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)
    


class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    name = db.Column(db.String)
    address = db.Column(db.String)
    postal_code = db.Column(db.Integer)
    city = db.Column(db.String)
    state = db.Column(db.String)
    country = db.Column(db.String)
    rooms = db.relationship('Room', backref='hotel', lazy='dynamic')
    rating = db.Column(db.Float)
    website = db.Column(db.String)
    phone = db.Column(db.String)
    email = db.Column(db.String)
    hdescript = db.Column(db.Integer)

    img1 = db.Column(db.String)
    img2 = db.Column(db.String)
    img3 = db.Column(db.String)

    def __repr__(self):
        return '<Hotel {}>'.format(self.name)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    pricepn = db.Column(db.Integer)
    wifi = db.Column(db.Boolean)
    htub = db.Column(db.Boolean)
    ac = db.Column(db.Boolean)
    elevator = db.Column(db.Boolean)
    room_type = db.Column(db.String)
    bed_count = db.Column(db.Integer)
    bed = db.Column(db.String)
    sqft = db.Column(db.Integer)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'))


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))