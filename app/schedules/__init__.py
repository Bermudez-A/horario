from flask import Blueprint

schedules = Blueprint('schedules', __name__)

from . import routes 