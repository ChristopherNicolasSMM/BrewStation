"""
Compat shim: re-export core (plugin_integ_bFather) models under top-level `model.*`.

Several parts of the app and plugin routes import `from model.config import ...`.
The real implementation currently lives inside the core plugin package.
"""

from plugins.plugin_integ_bFather.model.config import *  # noqa: F401,F403



