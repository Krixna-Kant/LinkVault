"""
App factory module
"""
import os
from flask import Flask
from .extensions import db
from .routes.links import links_bp

def create_app(config_object=None):
    app = Flask(__name__)
    
    # Defaults
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///linkvault.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    if config_object:
        app.config.from_object(config_object)
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
    app.register_blueprint(links_bp)
    
    return app
