from flask import Flask
import time 
from models import db
from routes import routes_blueprint 

app = Flask(__name__) 
app.config['CACHE_BUSTER'] = int(time.time())
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'  # Database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

db.init_app(app)

app.register_blueprint(routes_blueprint) # Register the blueprint

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
