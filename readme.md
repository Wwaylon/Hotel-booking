# Hotel Booking Website

Steps to build and run

1. git clone https://github.com/Wwaylon/Hotel-booking.git

2. cd Hotel-booking
3. setup virtual environment. "python -m venv ven"
4. activate virtual env. "venv\Scripts\activate"
5. "pip install -r requirements.txt" 
6. "pip install git+https://github.com/flask-extensions/Flask-GoogleMaps"  b/c version installed by "pip install flask-googlemaps" is old and broken
7. Create a .env in the "Hotel" directory folder level.
8. Set "GMAIL", "PASSWORD", "GMAPS_API" values in your .env file 
9. initialize database.  "flask db migrate"
10. "flask db upgrade"
11. "flask run"


To get email reset working, add a .env file to your project with your email and password


