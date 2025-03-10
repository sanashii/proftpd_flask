import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql://root:root@localhost/proftpd'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session settings
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    
    # LDAP settings
    LDAP_HOST = os.environ.get('LDAP_HOST') or 'ldap://localhost'
    LDAP_PORT = int(os.environ.get('LDAP_PORT') or 389)
    LDAP_USE_SSL = os.environ.get('LDAP_USE_SSL', 'False').lower() == 'true'
    LDAP_BASE_DN = os.environ.get('LDAP_BASE_DN') or 'dc=example,dc=com'
    LDAP_USER_DN = os.environ.get('LDAP_USER_DN') or 'cn=users,dc=example,dc=com'
    LDAP_GROUP_DN = os.environ.get('LDAP_GROUP_DN') or 'cn=groups,dc=example,dc=com'
    LDAP_BIND_DN = os.environ.get('LDAP_BIND_DN') or 'cn=admin,dc=example,dc=com'
    LDAP_BIND_PASSWORD = os.environ.get('LDAP_BIND_PASSWORD') or 'admin'
    
    # LDAP attribute mappings
    LDAP_USER_ATTRIBUTES = {
        'username': 'uid',
        'email': 'mail',
        'full_name': 'cn',
        'groups': 'memberOf'
    }
    
    # LDAP search filters
    LDAP_USER_FILTER = '(uid={username})'
    LDAP_GROUP_FILTER = '(cn={group_name})'
    
    # ProFTPD settings
    PROFTPD_CONFIG_PATH = os.environ.get('PROFTPD_CONFIG_PATH') or '/etc/proftpd/proftpd.conf'
    PROFTPD_USER_HOME = os.environ.get('PROFTPD_USER_HOME') or '/home/ftp' 