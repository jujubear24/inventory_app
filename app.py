from flask import Flask # type: ignore
from models import db

app = Flask(__name__) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'  # Database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

db.init_app(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
