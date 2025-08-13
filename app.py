import os

from flask import Flask
from flask_migrate import Migrate
from models import db 
from config import config

def create_app(config_name='default'):
    app = Flask(__name__)
    # Determine configuration to use
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    Migrate(app, db)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run()
