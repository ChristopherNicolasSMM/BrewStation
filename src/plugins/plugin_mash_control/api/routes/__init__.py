"""
Rotas API do plugin mash_control.
"""

from .mash_routes import mash_bp
from .recipe_routes import recipe_bp

all_blueprints = [mash_bp, recipe_bp]
