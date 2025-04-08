from flask import Blueprint

encryption = Blueprint('encryption', __name__)

from . import routes