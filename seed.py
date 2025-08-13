from app import create_app
from models import db
from models import Sacco, Location, Route  # import your actual models
from datetime import datetime

# Create app in the correct config (change "development" if needed)
app = create_app("development")

# Use the app context so db.session works
with app.app_context():
    print("🌱 Seeding database...")
    
    Route.query.delete()
    Sacco.query.delete()

    
