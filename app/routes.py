from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm, HotelSearchForm, ResetPasswordRequestForm, ResetPasswordForm, ReserveRoomForm
from app.models import User, Post, Hotel, Room, Reservation
from app.email import send_password_reset_email
from sqlalchemy import func
import csv
from datetime import datetime


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


def load_hotel_csv_to_database():
    with open('app/static/hotels.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Create a new Hotel object from the row data
            print(row['id'])
            hotel = Hotel(id = int(row['id']),
                          name=row['name'].strip(),
                          address=row['address'].strip(),
                          postal_code=int(row['postal_code']),
                          city=row['city'].strip(),
                          state=row['state'].strip(),
                          country=row['country'].strip(),
                          rating=float(row['rating']),
                          hdescript=(row['hdescript']).strip(),
                          img1=row['img1'].strip(),
                          img2=row['img2'].strip(),
                          img3=row['img3'].strip())
            # Add the new hotel to the database
            db.session.add(hotel)
            # Commit the changes to the database
            db.session.commit()

def load_room_csv_to_database():
    with open('app/static/rooms.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Find the hotel associated with the room
            hotel = Hotel.query.filter_by(id=int(row['hotel_id'])).first()

            if hotel:
                # Create a new Room object from the row data
                room = Room(id=int(row['id']),
                            pricepn=int(row['pricepn']),
                            wifi=bool(int(row['wifi'])),
                            pool=bool(int(row['pool'])),
                            htub=bool(int(row['htub'])),
                            petfr=bool(int(row['petfr'])),
                            ac=bool(int(row['ac'])),
                            elevator=bool(int(row['elevator'])),
                            room_type=row['room_type'].strip(),
                            hotel_id=int(row['hotel_id']))
                # Add the new room to the database
                db.session.add(room)
                # Commit the changes to the database
                db.session.commit()


@app.route('/', methods=['GET', 'POST'])
def home():
    #load_hotel_csv_to_database()
    #load_room_csv_to_database()
    form = HotelSearchForm()
    if form.validate_on_submit():
        #check if checkout date is after checkin date
        if form.check_out.data < form.check_in.data:
            flash('Check-out date must be after check-in date')
            return redirect(url_for('home'))
        return redirect(url_for('sresults', city=str(form.location.data), check_in=str(form.check_in.data), check_out=str(form.check_out.data)))
    
    if request.method == "GET":
        #read cities.csv into cities without quotes
        with open('app/static/cities.csv', 'r') as f:
            reader = csv.reader(f)
            cities = list(reader)
            #remove ' from each entry
            cities = [x[0].replace("'", "") for x in cities]
        return render_template('home.html', title='Innkeeper - Home', form=form, cities=cities)


@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)

@app.route('/sresults/<city>/<check_in>/<check_out>', methods=['GET', 'POST'])
def sresults(city, check_in, check_out):
    #if city contains a , then it is a city, state pair # remove the state and , from the city
    if ',' in city:
        city = city.split(',')[0]
    results = Hotel.query.filter(func.lower(Hotel.city) == func.lower(city)).all()
    return render_template('sresults.html', city=city, hotels=results, check_in_date=check_in, check_out_date=check_out)

@app.route('/hotel/<hotel_id>/<check_in>/<check_out>')
def hotel(hotel_id, check_in, check_out):

    check_in_dt = datetime.strptime(check_in, '%Y-%m-%d')
    check_out_dt = datetime.strptime(check_out, '%Y-%m-%d')
    # Code to fetch hotel information for the given hotel_id
    hotel_info = Hotel.query.filter_by(id=hotel_id).first()
    #find the rooms for the hotel
    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    print(rooms)
    #find the reservations the overlap with the checkin and checkout dates
    reservations = Reservation.query.filter(Reservation.room_id.in_([room.id for room in rooms])).all()
    print(reservations)
    for res in reservations:
        print(res.room_id)
        print(res.check_in)
        print(res.check_out)
    #remove the rooms that are reserved during the checkin and checkout dates
    for reservation in reservations:
        if reservation.check_in <= check_in_dt <= reservation.check_out or reservation.check_in <= check_out_dt <= reservation.check_out:
            print("trigger")
            #find the room that is reserved and remove it from the list of rooms
            for room in rooms:
                if room.id == reservation.room_id:
                    rooms.remove(room)
    print(rooms)

    # Code to render the hotel page template with the hotel information
    # ...

    return render_template('hotel.html', hotel_info=hotel_info, rooms=rooms, check_in=check_in, check_out=check_out)

@app.route('/reserve/<room_id>/<check_in>/<check_out>', methods=['GET', 'POST'])
@login_required
def reserve(room_id, check_in, check_out):
    form = ReserveRoomForm()
    check_in_dt = datetime.strptime(check_in, '%Y-%m-%d')
    check_out_dt = datetime.strptime(check_out, '%Y-%m-%d')
    if form.validate_on_submit():
        # Code to reserve the room for the given room_id
        # ...

        reservation_obj = Reservation(room_id=room_id, check_in=check_in_dt, check_out=check_out_dt, user_id=current_user.id)
        print (reservation_obj.room_id, reservation_obj.check_in, reservation_obj.check_out, reservation_obj.user_id)
        db.session.add(reservation_obj)
        db.session.commit()
        return redirect(url_for('thank_you'))
    return render_template('reserve.html', form=form, check_in=check_in, check_out=check_out)

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))
    
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)