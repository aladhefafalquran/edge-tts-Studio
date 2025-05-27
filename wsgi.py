#!/usr/bin/python3
import sys
import os

# Add your project directory to sys.path
project_home = '/home/yourusername/mysite'  # Replace 'yourusername' with your actual username
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

from flask_app import app as application

if __name__ == "__main__":
    application.run()