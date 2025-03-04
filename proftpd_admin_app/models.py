from datetime import datetime, timedelta, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import hashlib
import binascii
import random
import string

db = SQLAlchemy()

class AdminLog(db.Model):
    __tablename__ = 'admin_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    change_done = db.Column(db.Text, nullable=False)
    change_made_by = db.Column(db.String(50), db.ForeignKey('trax_users.username'), nullable=False)

    # Relationship to TraxUser
    user = db.relationship('TraxUser', backref='admin_logs')


class TraxUser(db.Model):
    __tablename__ = 'trax_users'

    username = db.Column(db.String(50), primary_key=True, nullable=False)
    f_name = db.Column(db.String(50))
    l_name = db.Column(db.String(50))
    # login_ldap = db.Column(db.Boolean)
    is_enabled = db.Column(db.Boolean)
    user_type = db.Column(db.String(50))
    can_view = db.Column(db.Boolean)
    can_create = db.Column(db.Boolean)
    can_modify = db.Column(db.Boolean)
    # password = db.Column(db.String(128), nullable=False) # should be linked to the trax employee's password na that was predetermined

    # def set_password(self, password):
    #     # Generate salt and hash password
    #     salt = ''.join(random.choice(string.ascii_lowercase) for x in range(2))
    #     self.password = salt + binascii.hexlify(hashlib.md5((salt + password).encode('utf-8')).digest()).decode('utf-8').upper()

    # def check_password(self, password):
    #     # Verify password
    #     salt = self.password[:2]
    #     return self.password == salt + binascii.hexlify(hashlib.md5((salt + password).encode('utf-8')).digest()).decode('utf-8').upper()


class User(db.Model):
    __tablename__ = 'users'

    username = db.Column(db.String(128), primary_key=True)
    password = db.Column(db.String(128), nullable=False)
    uid = db.Column(db.Integer)
    gid = db.Column(db.Integer)
    homedir = db.Column(db.String(255))
    shell = db.Column(db.String(255))
    enabled = db.Column(db.Boolean, default=True)
    name = db.Column(db.String(255))
    phone = db.Column(db.String(45))
    email = db.Column(db.String(255))
    last_accessed = db.Column(db.DateTime)

    # Relationships
    login_history = relationship('LoginHistory', backref='user', cascade='all, delete-orphan')
    user_keys = relationship('UserKey', backref='user', cascade='all, delete-orphan')
    xfer_logs = relationship('XferLog', backref='user', cascade='all, delete-orphan')

    @property
    def computed_status(self):
        # First check if manually disabled
        if not self.enabled:
            return 'Disabled'

        # Check if never accessed
        if self.last_accessed is None:
            return 'Inactive (Never accessed)'

        try:
            # Use timezone-aware datetime
            now = datetime.now(timezone.utc)
            if self.last_accessed.tzinfo is None:
                # Make naive datetime timezone-aware
                last_accessed = self.last_accessed.replace(tzinfo=timezone.utc)
            else:
                last_accessed = self.last_accessed

            days_inactive = (now - last_accessed).days

            if days_inactive > 150:
                return 'Disabled'
            elif days_inactive > 7:
                return f'Inactive ({days_inactive} days)'
            else:
                return 'Active'
        except Exception as e:
            print(f"Error calculating status: {e}")
            return 'Inactive (Error calculating days)'

    def set_password(self, password):
        salt = ''.join(random.choice(string.ascii_lowercase) for x in range(2))
        self.password = salt + binascii.hexlify(hashlib.md5((salt + password).encode('utf-8')).digest()).decode('utf-8').upper()

    def check_password(self, password):
        salt = self.password[:2]
        return self.password == salt + binascii.hexlify(hashlib.md5((salt + password).encode('utf-8')).digest()).decode('utf-8').upper()


class Group(db.Model):
    __tablename__ = 'groups'

    groupname = db.Column(db.String(128), primary_key=True)
    gid = db.Column(db.Integer, nullable=False)
    members = db.Column(db.Text)


class HostKey(db.Model):
    __tablename__ = 'host_keys'

    host = db.Column(db.String(255), primary_key=True)
    public_key = db.Column(db.Text, nullable=False)

class LoginHistory(db.Model):
    __tablename__ = 'login_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), db.ForeignKey('users.username', ondelete='CASCADE', onupdate='CASCADE'))
    client_ip = db.Column(db.String(128), nullable=False)
    server_ip = db.Column(db.String(128), nullable=False)
    protocol = db.Column(db.String(8), nullable=False)
    ts = db.Column(db.DateTime)

class UserKey(db.Model):
    __tablename__ = 'user_keys'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), db.ForeignKey('users.username', ondelete='CASCADE', onupdate='CASCADE'))
    public_key = db.Column(db.Text, nullable=False)

class XferLog(db.Model):
    __tablename__ = 'xferlog'

    # Remove id field since it doesn't exist in database
    username = db.Column(db.String(128), db.ForeignKey('users.username', ondelete='CASCADE', onupdate='CASCADE'))
    filename = db.Column(db.Text)
    size = db.Column(db.BigInteger)
    host = db.Column(db.Text)
    address = db.Column(db.String(128))
    action = db.Column(db.Text)
    duration = db.Column(db.Text)
    localtime = db.Column(db.DateTime)
    success = db.Column(db.Text)

    __mapper_args__ = {
        'primary_key': [username, localtime]  # Using composite key
    }