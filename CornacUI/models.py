from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer,
                    primary_key=True)
    username = db.Column(db.String(20),
                    nullable=False,
                    unique=True)
    password = db.Column(db.String(20),
                    nullable=False)

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        """Check hashed password."""
        # return check_password_hash(self.password, password) 
        return self.password==password

    def __repr__(self):
        return "<User %r>" % (self.username)