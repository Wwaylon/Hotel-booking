from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, session, abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm, HotelSearchForm, ResetPasswordRequestForm, ResetPasswordForm, ReserveRoomForm, CheckInCheckOutForm, CancelReservationForm, RedeemPointsForm
from app.models import User, Post, Hotel, Room, Reservation
from app.email import send_password_reset_email
from sqlalchemy import func, or_
import csv
from datetime import datetime
from flask_googlemaps import GoogleMaps, Map
import requests
import os
import math
import stripe
basedir = os.path.abspath(os.path.dirname(__file__))
stripe.api_key =  app.config.get('STRIPE_SECRET_KEY')
prev_sort_option = ''




@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


def load_data():
    with open('app/static/hotels.csv', 'r') as file:
        reader = csv.DictReader(file)
        hotels = []
        for row in reader:
            hotel = {
                'id': int(row['id']),
                'name': row['name'].strip(),
                'address': row['address'].strip(),
                'postal_code': int(row['postal_code']),
                'city': row['city'].strip(),
                'state': row['state'].strip(),
                'country': row['country'].strip(),
                'rating': float(row['rating']),
                'hdescript': (row['hdescript']).strip(),
                'img1': row['img1'].strip(),
                'img2': row['img2'].strip(),
                'img3': row['img3'].strip(),
                'website': row['website'].strip(),
                'phone': row['phone number'].strip(),
                'email': row['email'].strip()
            }
            hotels.append(hotel)
    with open('app/static/rooms.csv', 'r') as file:
        reader = csv.DictReader(file)
        rooms = []
        for row in reader:
            room = {
                'id': int(row['id']),
                'pricepn': int(row['pricepn']),
                'wifi': bool(int(row['wifi'])),
                'ac': bool(int(row['ac'])),
                'elevator': bool(int(row['elevator'])),
                'room_type': row['room_type'].strip(),
                'bed_count': int(row['bed_count']),
                'bed': row['bed'].strip(),
                'sqft': int(row['sqft']),
                'hotel_id': int(row['hotel_id'])
            }
            rooms.append(room)
    db.session.bulk_insert_mappings(Hotel, hotels)
    db.session.bulk_insert_mappings(Room, rooms)
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
                          img3=row['img3'].strip(),
                          website = row['website'].strip(),
                          phone = row['phone'].strip(),
                        email = row['email'].strip())
            # Add the new hotel to the database
            db.session.add(hotel)
            # Commit the changes to the database
            db.session.commit()

def load_room_csv_to_database():
    with open('app/static/rooms.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            print(row['id'])
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
    #load_data()
    #load_hotel_csv_to_database() NOT NEEDED USE  THE LOAD DATA FUNCTION ABOVE> WAY FASTER
    #load_room_csv_to_database()NOT NEEDED USE  THE LOAD DATA FUNCTION ABOVE> WAY FASTER
    if "location" in session:
        session.pop("location", None)
    if "previous_sort_option" in session:
        session.pop("previous_sort_option", None)
    form = HotelSearchForm()
    if form.validate_on_submit():
        #check if checkout date is after checkin date
        if form.check_out.data < form.check_in.data:
            flash('Check-out date must be after check-in date')
            return redirect(url_for('home'))
        session["location"] = form.location.data
        session["check_in"] = form.check_in.data.strftime('%Y-%m-%d')
        session["check_out"] = form.check_out.data.strftime('%Y-%m-%d')
        return redirect(url_for('sresults'))
    
    #read cities.csv into cities without quotes
    with open('app/static/cities.csv', 'r') as f:
        reader = csv.reader(f)
        cities = list(reader)
        #remove ' from each entry
        cities = [x[0].replace("'", "") for x in cities]
    return render_template('home.html', title='LikeHome - Home', form=form, cities=cities)


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

@app.route('/sresults', methods=['GET', 'POST'])
def sresults():
    if "hotel_id" in session:
        session.pop("hotel_id", None)
    if "location" not in session:
        flash('Please enter search criteria again.')
        return redirect(url_for('home'))
    location = session["location"]
    if "check_in" in session and "check_out" in session:
        check_in = datetime.strptime(session["check_in"], "%Y-%m-%d")
        check_out = datetime.strptime(session["check_out"], "%Y-%m-%d")
        form = HotelSearchForm(location=location, check_in=check_in, check_out=check_out)
    else:
        form = HotelSearchForm(location=location)
    #if city contains a , then it is a city, state pair # remove the state and , from the city
    if ',' in location:
        city = location.split(',')[0]
    else:
        city = location
    
    hotels_per_page = 9
    page = request.args.get('page', 1, type=int)
    sort_option = request.args.get('sort')
    # Store previous sort option in a separate variable
    # If the sort option has changed, reset the page number to 1
    if "previous_sort_option" in session:
        if sort_option != session["previous_sort_option"] and sort_option is not None:
            page = 1
    
    if sort_option is None: 
        if "previous_sort_option" in session:
            sort_option = session["previous_sort_option"]
        else: 
            sort_option = "hl"
    print(sort_option)
    results = Hotel.query.filter(func.lower(Hotel.city) == func.lower(city)).order_by(Hotel.rating.asc() if sort_option == "lh" else Hotel.rating.desc()).paginate(page=page, per_page=hotels_per_page)
    #query the lowest cost room for each hotel
    hotel_list = []
    for hotel in results.items:
        hotel_list.append((hotel, Room.query.filter_by(hotel_id=hotel.id).order_by(Room.pricepn).first()))
    # Store the current sort option in the session
    session["previous_sort_option"] = sort_option
    print(session["previous_sort_option"])

    num_pages = results.pages

    if form.validate_on_submit():
        if form.check_out.data < form.check_in.data:
            flash('Check-out date must be after check-in date')
            return redirect(url_for('sresults'))
        session["location"] = form.location.data
        session["check_in"] = form.check_in.data.strftime('%Y-%m-%d')
        session["check_out"] = form.check_out.data.strftime('%Y-%m-%d')
        return redirect(url_for('sresults', page=1))
    
    if request.method == "GET":
        #read cities.csv into cities without quotes
        with open('app/static/cities.csv', 'r') as f:
            reader = csv.reader(f)
            cities = list(reader)
            #remove ' from each entry
            cities = [x[0].replace("'", "") for x in cities]
        return render_template('sresults.html', city=city, hotels=hotel_list, form=form, pagination=results, current_page=page, num_pages=num_pages,  sort_option=sort_option, cities=cities)


@app.route('/hotel/<hotel_id>', methods=['GET', 'POST'])
def hotel(hotel_id):
    if "check_in" not in session or "check_out" not in session:
        flash('Please enter a check-in and check-out date. Before preceding to the hotel page.')
        return redirect(url_for('sresults'))
    check_in_dt = datetime.strptime(session["check_in"], "%Y-%m-%d")
    check_out_dt = datetime.strptime(session["check_out"], "%Y-%m-%d")
    form = CheckInCheckOutForm(check_in=check_in_dt, check_out=check_out_dt)
    if form.validate_on_submit():
        if form.check_out.data < form.check_in.data:
            flash('Check-out date must be after check-in date')
            return redirect(url_for('hotel', hotel_id=hotel_id))
        session["check_in"] = form.check_in.data.strftime('%Y-%m-%d')
        session["check_out"] = form.check_out.data.strftime('%Y-%m-%d')
        return redirect(url_for('hotel', hotel_id=hotel_id))


    # Code to fetch hotel information for the given hotel_id
    hotel_info = Hotel.query.filter_by(id=hotel_id).first()
    #find the rooms for the hotel
    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    #find the reservations the overlap with the checkin and checkout dates
    reservations = Reservation.query.filter(Reservation.room_id.in_([room.id for room in rooms])).all()
    #remove the rooms that are reserved during the checkin and checkout dates
    for reservation in reservations:
        if reservation.check_in <= check_in_dt <= reservation.check_out or reservation.check_in <= check_out_dt <= reservation.check_out:
            #find the room that is reserved and remove it from the list of rooms
            for room in rooms:
                if room.id == reservation.room_id:
                    rooms.remove(room)
    global prev_sort_option
    sort_option = request.args.get('sort')
    page = request.args.get('page', 1, type=int)
    if sort_option != prev_sort_option and sort_option is not None:
        page = 1
    else: 
        sort_option = prev_sort_option
    if sort_option == 'lh':
        rooms.sort(key=lambda x: x.pricepn)
    elif sort_option == 'hl':
        rooms.sort(key=lambda x: x.pricepn, reverse=True)
    else:
        sort_option = prev_sort_option
        if sort_option == 'lh':
            rooms.sort(key=lambda x: x.pricepn)
        elif sort_option == 'hl':
            rooms.sort(key=lambda x: x.pricepn, reverse=True)
    prev_sort_option = sort_option

    rooms_per_page = 10
    num_pages = int(math.ceil(len(rooms) / rooms_per_page))
    start_index = (page - 1) * rooms_per_page
    end_index = start_index + rooms_per_page
    rooms = rooms[start_index:end_index]

    #append address, city, state, postal code, and country to address
    address = hotel_info.address + ', ' + hotel_info.city + ', ' + hotel_info.state + ', ' + str(hotel_info.postal_code) + ', ' + hotel_info.country
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
    "address": address,
    "key": app.config.get('GMAPS_API')  # Replace with your API key
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data["status"] == "OK":
        result = data["results"][0]
        lat = result["geometry"]["location"]["lat"]
        lng = result["geometry"]["location"]["lng"]
        mymap = Map(
            identifier="view-side",
            lat=lat,
            lng=lng,
            markers=[(lat, lng)]
        )
    else:
        print("Geocoding failed. Please check your address and API key.")         
        mymap =None      
    # Code to render the hotel page template with the hotel information
    # ...
    session["hotel_id"] = hotel_id
    return render_template('hotel.html', hotel_info=hotel_info, rooms=rooms, form=form, mymap = mymap, num_pages=num_pages, current_page=page, sort_option=sort_option)

@app.route('/reserve/<room_id>', methods=['GET', 'POST'])
@login_required
def reserve(room_id):
    url =request.referrer
    url_prefix = url.split('?')[0]
    if url_prefix == url_for('login', _external=True):
        return redirect(url_for('hotel', hotel_id=session["hotel_id"]))
    if url_prefix != url_for('hotel', hotel_id=session["hotel_id"], _external=True) and request.referrer != url_for('reserve', room_id=room_id, _external=True) and  request.referrer != url_for('reserve', room_id=room_id, doublebook=True, _external=True):
        flash('You are not allowed to access this page directly. Please reserve a room from the search results page.')
        return redirect(url_for('home'))
    if "check_in" not in session or "check_out" not in session:
        flash('Please enter a check-in and check-out date. Before reserving a room.')
        return redirect(url_for('sresults'))
    check_in = session["check_in"]
    check_out = session["check_out"]
    form = ReserveRoomForm()
    check_in_dt = datetime.strptime(check_in, '%Y-%m-%d')
    check_out_dt = datetime.strptime(check_out, '%Y-%m-%d')
    #check if double booking
    room = Room.query.filter_by(id=room_id).first()
    reservations = Reservation.query.filter_by(user_id=current_user.id).all()
    hotel = Hotel.query.filter_by(id=room.hotel_id).first()
    for reservation in reservations:
        #check if there is overlap
        if reservation.check_in <= check_in_dt < reservation.check_out or reservation.check_in < check_out_dt <= reservation.check_out:
            flash('Your current reservation overlaps with a parts or all of another previous reservation at the current or different hotel. Double booking is not allowed, please select a different check-in and check-out date.')
            return redirect(url_for('hotel', hotel_id=hotel.id))


    #-->Added checkin and checkout date range check
    if check_in_dt.date() < datetime.now().date() or check_out_dt.date() < datetime.now().date():
        flash('Please select a check-in and check-out date in the future.')
        return redirect(url_for('sresults'))
    if check_in_dt.date() == check_out_dt.date():
        flash('Check-out date must be after check-in date')
        return redirect(url_for('sresults'))

    #hotel_info = Hotel.query.filter_by(id=hotel_id).first()
    num_nights = (check_out_dt - check_in_dt).days
    if current_user.reward_points >= 100 and form.reward_point_discount.data == True:
        amount = int(room.pricepn * (num_nights-1) * 100)
        amount_proper= room.pricepn * num_nights-1
        name = f'1 Night Free: {hotel.name} - {room.room_type.capitalize()} - {room.bed_count} {room.bed.capitalize()} - {check_in_dt.date()} - {check_out_dt.date()} - {current_user.id} - {room.id} - f - 0'
    else: 
        amount = int(room.pricepn * num_nights  * 100)
        amount_proper= room.pricepn * num_nights 
        name = f'{hotel.name} - {room.room_type.capitalize()} - {room.bed_count} {room.bed.capitalize()} - {check_in_dt.date()} - {check_out_dt.date()} - {current_user.id} - {room.id} - f - 0'

    if form.validate_on_submit(): 
        cust= stripe.Customer.create()       
        checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
					#-->Added
                    'name': name,
                },
                'unit_amount': amount,
            },
            'quantity': 1,
        }],
        payment_intent_data= {
            'setup_future_usage': 'off_session'
        },
        mode='payment',
        customer = cust.id,
        success_url=request.host_url + 'thank_you',
        cancel_url=request.host_url + 'cancel_order',
    )       
        db.session.commit()
        return redirect(checkout_session.url)
    
    redeemable = False
    if current_user.reward_points >= 100:
        redeemable = True

    reward_points_per_night = 5  
    potential_reward_points = min(100, (num_nights * reward_points_per_night))

    res_info = []
    res_info = {
        'hotel_name': hotel.name,
        'hotel_address': hotel.address,
        'hotel_city': hotel.city,
        'hotel_state': hotel.state,
        'hotel_postal_code': hotel.postal_code,
        'hotel_country': hotel.country,
        'check_in': check_in_dt.date(),
        'room': room.room_type,
        'bed': room.bed,
        'bed_count': room.bed_count,
        'check_out': check_out_dt.date(),
        'img1': hotel.img1
    }
    return render_template('reserve.html', form=form, check_in=check_in, check_out=check_out, res_info =res_info, redeemable=redeemable, potential_reward_points= potential_reward_points, cost=amount_proper)

@app.route('/edit_reservation_reserve/<room_id>/<reservation_id>', methods=['GET', 'POST'])
@login_required
def edit_reservation_reserve(room_id, reservation_id):
    url =request.referrer
    url_prefix = url.split('?')[0]
    if url_prefix == url_for('login', _external=True):
        return redirect(url_for('edit_reservation', reservation_id=reservation_id))
    if url_prefix != url_for('edit_reservation', reservation_id=reservation_id, _external=True) and request.referrer != url_for('edit_reservation_reserve', room_id=room_id, reservation_id=reservation_id, _external=True) and  request.referrer != url_for('edit_reservation_reserve', room_id=room_id, reservation_id=reservation_id, doublebook=True, _external=True):
        flash('You are not allowed to access this page directly. Please reserve a room from the search results page.')
        return redirect(url_for('home'))
    if "check_in" not in session or "check_out" not in session:
        flash('Please enter a check-in and check-out date. Before reserving a room.')
        return redirect(url_for('home'))
    check_in = session["check_in"]
    check_out = session["check_out"]
    form = ReserveRoomForm()
    check_in_dt = datetime.strptime(check_in, '%Y-%m-%d')
    check_out_dt = datetime.strptime(check_out, '%Y-%m-%d')
    #check if double booking
    room = Room.query.filter_by(id=room_id).first()
    reservations = Reservation.query.filter_by(user_id=current_user.id).all()
    hotel = Hotel.query.filter_by(id=room.hotel_id).first()
    for reservation in reservations:
        #check if there is overlap
        if reservation.id == int(reservation_id):
            reservations.remove(reservation)
            continue
        if reservation.check_in <= check_in_dt < reservation.check_out or reservation.check_in < check_out_dt <= reservation.check_out:
            flash('Your current reservation overlaps with a parts or all of another previous reservation at the current or different hotel. Double booking is not allowed, please select a different check-in and check-out date.')
            return redirect(url_for('edit_reservation', reservation_id=reservation_id))


    #-->Added checkin and checkout date range check
    if check_in_dt.date() < datetime.now().date() or check_out_dt.date() < datetime.now().date():
        flash('Please select a check-in and check-out date in the future.')
        return redirect(url_for('edit_reservation', reservation_id=reservation_id))
    if check_in_dt.date() == check_out_dt.date():
        flash('Check-out date must be after check-in date')
        return redirect(url_for('edit_reservation', reservation_id=reservation_id))

    #hotel_info = Hotel.query.filter_by(id=hotel_id).first()
    num_nights = (check_out_dt - check_in_dt).days
    amount = int(room.pricepn * num_nights  * 100)
    amount_proper= room.pricepn * num_nights 
    name = f'{hotel.name} - {room.room_type.capitalize()} - {room.bed_count} {room.bed.capitalize()} - {check_in_dt.date()} - {check_out_dt.date()} - {current_user.id} - {room.id} - t - {reservation_id}'

    if form.validate_on_submit(): 
        cust= stripe.Customer.create()       
        checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
					#-->Added
                    'name': name,
                },
                'unit_amount': amount,
            },
            'quantity': 1,
        }],
        payment_intent_data= {
            'setup_future_usage': 'off_session'
        },
        mode='payment',
        customer = cust.id,
        success_url=request.host_url + 'thank_you',
        cancel_url=request.host_url + 'cancel_order',
    )       
        db.session.commit()
        return redirect(checkout_session.url)
    
    redeemable = False

    reward_points_per_night = 5  
    potential_reward_points = min(100, (num_nights * reward_points_per_night))

    res_info = []
    res_info = {
        'hotel_name': hotel.name,
        'hotel_address': hotel.address,
        'hotel_city': hotel.city,
        'hotel_state': hotel.state,
        'hotel_postal_code': hotel.postal_code,
        'hotel_country': hotel.country,
        'check_in': check_in_dt.date(),
        'room': room.room_type,
        'bed': room.bed,
        'bed_count': room.bed_count,
        'check_out': check_out_dt.date(),
        'img1': hotel.img1
    }
    return render_template('edit_reservation_reserve.html', form=form, check_in=check_in, check_out=check_out, res_info =res_info, redeemable=redeemable, potential_reward_points= potential_reward_points, cost=amount_proper, reservation_id=reservation_id)

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/cancel_order')
def cancel_order():
    return render_template('cancel_order.html')

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
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
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
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, f_name=form.f_name.data, l_name=form.l_name.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

"""
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
"""
@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    #ensure that the user is not trying to access a user that is not them
    if user != current_user:
        abort(403)

    #query user's reservations
    reservations = Reservation.query.filter_by(user_id=current_user.id).all()
    current_date = datetime.utcnow()
    res_list = []
    active_reservations = []
    past_reservations = []
    for reservation in reservations:
        room = Room.query.filter_by(id=reservation.room_id).first()
        hotel = Hotel.query.filter_by(id=room.hotel_id).first()
        res_list.append({
            'reservation_id': reservation.id,
            'hotel_name': hotel.name,
            'hotel_address': hotel.address,
            'hotel_city': hotel.city,
            'hotel_state': hotel.state,
            'hotel_postal_code': hotel.postal_code,
            'hotel_country': hotel.country,
            'check_in': reservation.check_in,
            'room': room.room_type,
            'bed': room.bed,
            'bed_count': room.bed_count,
            'check_out': reservation.check_out,
            'img1': hotel.img1
        })
    for res in res_list:
        check_out_date = res['check_out']
        if check_out_date.date() >= current_date.date():
            # Reservation is active if check_out date is greater than or equal to current date
            active_reservations.append(res)
        else:
            # Reservation is past if check_out date is less than current date
            past_reservations.append(res)

    len_active = len(active_reservations)
    len_past = len(past_reservations)

    page_active = request.args.get('page_a', 1, type=int)
    entries_per_page = 4
    num_pages_active = int(math.ceil(len(active_reservations) / entries_per_page))
    start_index = (page_active - 1) * entries_per_page
    end_index = start_index + entries_per_page
    active_reservations = sorted(active_reservations, key=lambda k: k['check_in'])
    active_reservations = active_reservations[start_index:end_index]

    page_past = request.args.get('page_p', 1, type=int)
    num_pages_past = int(math.ceil(len(past_reservations) / entries_per_page))
    start_index = (page_past - 1) * entries_per_page
    end_index = start_index + entries_per_page
    past_reservations = sorted(past_reservations, key=lambda k: k['check_in'])
    past_reservations = past_reservations[start_index:end_index]

    show = request.args.get('show', 'active', type=str)

    
    return render_template('user.html', user=user, active_reservations=active_reservations, past_reservations=past_reservations, num_pages_active=num_pages_active, current_page_active=page_active, num_pages_past=num_pages_past, current_page_past=page_past, show=show, len_active=len_active, len_past=len_past, reward_points=current_user.reward_points)

@app.route('/load_session/<reservation_id>', methods=['GET', 'POST'])
@login_required
def load_session(reservation_id):
    reservation = Reservation.query.filter_by(id=reservation_id).first()
    session["check_in"] = reservation.check_in.strftime('%Y-%m-%d')
    session["check_out"] = reservation.check_out.strftime('%Y-%m-%d')
    return redirect(url_for('edit_reservation', reservation_id=reservation_id))

@app.route('/edit_reservation/<reservation_id>', methods=['GET', 'POST'])
@login_required
def edit_reservation(reservation_id):
    #query reservation
    reservation = Reservation.query.filter_by(id=reservation_id).first()
    room = Room.query.filter_by(id=reservation.room_id).first()
    hotel_id = room.hotel_id
    check_in_dt = datetime.strptime(session["check_in"], '%Y-%m-%d')
    check_out_dt = datetime.strptime(session["check_out"], '%Y-%m-%d')
    form = CheckInCheckOutForm(check_in=check_in_dt, check_out=check_out_dt)
    if form.validate_on_submit():
        if form.check_out.data < form.check_in.data:
            flash('Check-out date must be after check-in date')
            return redirect(url_for('edit_reservation', reservation_id=reservation_id))
        session["check_in"] = form.check_in.data.strftime('%Y-%m-%d')
        session["check_out"] = form.check_out.data.strftime('%Y-%m-%d')
        return redirect(url_for('edit_reservation', reservation_id=reservation_id))


    # Code to fetch hotel information for the given hotel_id
    hotel_info = Hotel.query.filter_by(id=hotel_id).first()
    #find the rooms for the hotel
    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    #find the reservations the overlap with the checkin and checkout dates
    reservations = Reservation.query.filter(Reservation.room_id.in_([room.id for room in rooms])).all()
    #remove the rooms that are reserved during the checkin and checkout dates
    for reservation in reservations:
        if reservation.check_in <= check_in_dt <= reservation.check_out or reservation.check_in <= check_out_dt <= reservation.check_out:
            #find the room that is reserved and remove it from the list of rooms
            for room in rooms:
                if room.id == reservation.room_id:
                    rooms.remove(room)
    global prev_sort_option
    sort_option = request.args.get('sort')
    page = request.args.get('page', 1, type=int)
    if sort_option != prev_sort_option and sort_option is not None:
        page = 1
    else: 
        sort_option = prev_sort_option
    if sort_option == 'lh':
        rooms.sort(key=lambda x: x.pricepn)
    elif sort_option == 'hl':
        rooms.sort(key=lambda x: x.pricepn, reverse=True)
    else:
        sort_option = prev_sort_option
        if sort_option == 'lh':
            rooms.sort(key=lambda x: x.pricepn)
        elif sort_option == 'hl':
            rooms.sort(key=lambda x: x.pricepn, reverse=True)
    prev_sort_option = sort_option

    rooms_per_page = 10
    num_pages = int(math.ceil(len(rooms) / rooms_per_page))
    start_index = (page - 1) * rooms_per_page
    end_index = start_index + rooms_per_page
    rooms = rooms[start_index:end_index]

    #append address, city, state, postal code, and country to address
    address = hotel_info.address + ', ' + hotel_info.city + ', ' + hotel_info.state + ', ' + str(hotel_info.postal_code) + ', ' + hotel_info.country
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
    "address": address,
    "key": app.config.get('GMAPS_API')  # Replace with your API key
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data["status"] == "OK":
        result = data["results"][0]
        lat = result["geometry"]["location"]["lat"]
        lng = result["geometry"]["location"]["lng"]
        mymap = Map(
            identifier="view-side",
            lat=lat,
            lng=lng,
            markers=[(lat, lng)]
        )
    else:
        print("Geocoding failed. Please check your address and API key.")         
        mymap =None      
    # Code to render the hotel page template with the hotel information
    # ...
    session["hotel_id"] = hotel_id
    return render_template('edit_reservation.html', hotel_info=hotel_info, rooms=rooms, form=form, mymap = mymap, num_pages=num_pages, current_page=page, sort_option=sort_option, reservation_id=reservation_id, current_reservation_room_id=reservation.room_id)


@app.route('/cancel_reservation/<reservation_id>', methods=['GET', 'POST'])
@login_required
def cancel_reservation(reservation_id):
    form = CancelReservationForm()
    reservation = Reservation.query.filter_by(id=reservation_id).first()
    room = Room.query.filter_by(id=reservation.room_id).first()
    hotel = Hotel.query.filter_by(id=room.hotel_id).first()
    res_info = {
        'reservation_id': reservation.id,
        'hotel_name': hotel.name,
        'hotel_address': hotel.address,
        'hotel_city': hotel.city,
        'hotel_state': hotel.state,
        'hotel_postal_code': hotel.postal_code,
        'hotel_country': hotel.country,
        'check_in': datetime(reservation.check_in.year, reservation.check_in.month, reservation.check_in.day, 0, 0, 0),
        'room': room.room_type,
        'bed': room.bed,
        'bed_count': room.bed_count,
        'check_out': reservation.check_out,
        'img1': hotel.img1
    }
    session = stripe.checkout.Session.retrieve(reservation.checkout_session, expand=['payment_intent'])
    payment_method = session.payment_intent.payment_method
    customer_id = session.customer
    stripe.PaymentMethod.attach(payment_method, customer=customer_id)


    if form.validate_on_submit():
        payment = stripe.PaymentIntent.create(customer=customer_id, payment_method=payment_method, amount=50*100, currency='usd', payment_method_types=['card'], confirm=True)
        refund = stripe.Refund.create(charge=session.payment_intent.latest_charge)
         #-->Calculate the number of nights for the reservation
        num_nights = (reservation.check_out - reservation.check_in).days
        db.session.delete(reservation)
        
        #-->Deduct reward points from the user
        reward_points_per_night = 5  # You can change this value as needed
        current_user.reward_points = max(current_user.reward_points - (num_nights * reward_points_per_night), 0)

        
        db.session.commit()
        flash('Reservation cancelled')
        return redirect(url_for('user', username=current_user.username))
    return render_template('cancel_reservation.html', title='Cancel Reservation', form=form, reservation=res_info)

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


@app.route('/submit/<city>', methods=['GET'])
def submit(city):
    if city == 'la':
        session["location"] = "Los Angeles, California"
        return redirect(url_for('sresults'))
    elif city == 'sf':
        session["location"] = "San Francisco, California"
        return redirect(url_for('sresults'))
    elif city == 'ny':
        session["location"] = "New York, New York"
        return redirect(url_for('sresults'))
    else :
        return redirect(url_for('home'))
    

@app.route('/event', methods=['POST'])
def new_event():
    event = None
    payload = request.data
    signature = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, signature, app.config.get('STRIPE_WEBHOOK_SECRET'))
    except Exception as e:
        # the payload could not be verified
        abort(400)

    if event['type'] == 'checkout.session.completed':
        session = stripe.checkout.Session.retrieve(
            event['data']['object'].id, expand=['line_items'])
        print(f'Sale to {session.customer_details.email}:')
        for item in session.line_items.data:
            print(f'  - {item.quantity} {item.description} '
                    f'${item.amount_total/100:.02f} {item.currency.upper()}')
        #from the item.description get the room id and the check in and check out dates and current user id
        #create a reservation object and save it to the database
            description_parts = item.description.split(" - ")
            desc = description_parts[0]
            check_in = description_parts[3]
            check_out = description_parts[4]
            user_id = int(description_parts[5])
            room_id = int(description_parts[6])
            edit_reservation_flag= description_parts[7]
            old_reservation = description_parts[8]
        payment_intent = event["data"]["object"]["payment_intent"]
        #if  desc has the word '1 night free' in it, then add 1 night to the reservation
        check_in =  datetime.strptime(check_in, "%Y-%m-%d")
        check_out =  datetime.strptime(check_out, "%Y-%m-%d")
        num_nights = (check_out - check_in).days
        user = User.query.filter_by(id=user_id).first()
        if edit_reservation_flag == 'f':
            if (user.reward_points + min(num_nights * 5, 100)) > 100:
                user.reward_points = 100
            else:
                user.reward_points += min(num_nights * 5, 100)
            if '1 Night Free' in desc:
                user.reward_points = 0    
        elif edit_reservation_flag == 't':
            #delete the old reservation
            old_reservation = Reservation.query.filter_by(id=old_reservation).first()
            #refund the user
            session = stripe.checkout.Session.retrieve(old_reservation.checkout_session, expand=['payment_intent'])
            payment_method = session.payment_intent.payment_method
            customer_id = session.customer
            stripe.PaymentMethod.attach(payment_method, customer=customer_id)
            refund = stripe.Refund.create(charge=session.payment_intent.latest_charge)
            db.session.delete(old_reservation)
        reservation = Reservation(check_in=check_in, check_out=check_out, user_id=user_id, room_id=room_id, checkout_session=event['data']['object'].id)
        db.session.add(reservation)
        db.session.commit()
    return {'success': True}