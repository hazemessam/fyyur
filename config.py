import os
from platform import system


SECRET_KEY = os.urandom(32)

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
# Set WSL localhost ip
localhost = '172.25.160.1' if system() == 'Linux' else '127.0.0.1'
SQLALCHEMY_DATABASE_URI = f'postgres://root:toor@{localhost}:5432/fyyurdb'

SQLALCHEMY_TRACK_MODIFICATIONS = False