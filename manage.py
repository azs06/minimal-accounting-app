from flask.cli import FlaskGroup
from src.main import app
from src.extensions import db

cli = FlaskGroup(app)

if __name__ == '__main__':
    cli()
