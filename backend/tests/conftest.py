"""
Pytest configuration — in-memory SQLite for all tests.
"""

import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture
def app():
    app = create_app(
        config={
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "TESTING": True,
        }
    )
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db
