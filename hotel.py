from app import app, db
from app.models import User, Post, Hotel, Room, Reservation

@app.shell_context_processor
def make_shell_context(): #flask shell config. use 'flask shell' to run this. Useful for debugging via the command line without having to manually import app every time
    return {'db': db, 'User': User, 'Post': Post, 'Hotel': Hotel, 'Room': Room, 'Reservation': Reservation}