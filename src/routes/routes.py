from flask import Blueprint
from .products import products_bp
from .commands import commands_bp

bp = Blueprint("api", __name__)

bp.register_blueprint(products_bp)
bp.register_blueprint(commands_bp)
