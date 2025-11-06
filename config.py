import os

# Get the base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database in data folder (inventory.db is gitignored, but folder is tracked)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data', 'inventory.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

