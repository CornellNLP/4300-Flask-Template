import json
import os
from dotenv import load_dotenv
from flask import Flask

load_dotenv()
from flask_cors import CORS
from models import db, Episode, Review
from routes import register_routes

# Get the directory of the current script
current_directory = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

# Configure SQLite database - using 3 slashes for relative path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with app
db.init_app(app)

# Register routes
register_routes(app)

# Function to initialize database (just creating tables if needed)
def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()

init_db()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)