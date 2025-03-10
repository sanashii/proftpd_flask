import ldap
from flask import current_app
from typing import Dict, Optional, List

class LDAPAuth:
    def __init__(self):
        self.ldap_uri = current_app.config['LDAP_HOST']
        self.port = current_app.config['LDAP_PORT']
        self.use_ssl = current_app.config['LDAP_USE_SSL']
        self.base_dn = current_app.config['LDAP_BASE_DN']
        self.user_dn = current_app.config['LDAP_USER_DN']
        self.group_dn = current_app.config['LDAP_GROUP_DN']
        self.bind_dn = current_app.config['LDAP_BIND_DN']
        self.bind_password = current_app.config['LDAP_BIND_PASSWORD']
        self.user_attributes = current_app.config['LDAP_USER_ATTRIBUTES']
        self.user_filter = current_app.config['LDAP_USER_FILTER']
        self.group_filter = current_app.config['LDAP_GROUP_FILTER']

    def _get_connection(self) -> ldap.ldapobject.LDAPObject:
        """Create and return an LDAP connection."""
        if self.use_ssl:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            conn = ldap.initialize(f'ldaps://{self.ldap_uri}:{self.port}')
        else:
            conn = ldap.initialize(f'ldap://{self.ldap_uri}:{self.port}')
        
        conn.simple_bind_s(self.bind_dn, self.bind_password)
        return conn

    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate a user against LDAP.
        
        Args:
            username: The username to authenticate
            password: The password to verify
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            conn = self._get_connection()
            user_filter = self.user_filter.format(username=username)
            result = conn.search_s(self.user_dn, ldap.SCOPE_SUBTREE, user_filter)
            
            if not result:
                return False
                
            user_dn = result[0][0]
            conn.simple_bind_s(user_dn, password)
            return True
            
        except ldap.INVALID_CREDENTIALS:
            return False
        except ldap.LDAPError as e:
            current_app.logger.error(f"LDAP authentication error: {str(e)}")
            return False
        finally:
            if 'conn' in locals():
                conn.unbind_s()

    def get_user_info(self, username: str) -> Optional[Dict]:
        """
        Get user information from LDAP.
        
        Args:
            username: The username to look up
            
        Returns:
            Dict: User information or None if not found
        """
        try:
            conn = self._get_connection()
            user_filter = self.user_filter.format(username=username)
            result = conn.search_s(self.user_dn, ldap.SCOPE_SUBTREE, user_filter)
            
            if not result:
                return None
                
            attrs = result[0][1]
            return {
                'username': attrs.get(self.user_attributes['username'], [b''])[0].decode('utf-8'),
                'email': attrs.get(self.user_attributes['email'], [b''])[0].decode('utf-8'),
                'full_name': attrs.get(self.user_attributes['full_name'], [b''])[0].decode('utf-8'),
                'groups': [g.decode('utf-8') for g in attrs.get(self.user_attributes['groups'], [])]
            }
            
        except ldap.LDAPError as e:
            current_app.logger.error(f"LDAP user info error: {str(e)}")
            return None
        finally:
            if 'conn' in locals():
                conn.unbind_s()

    def get_user_groups(self, username: str) -> List[str]:
        """
        Get user's groups from LDAP.
        
        Args:
            username: The username to look up
            
        Returns:
            List[str]: List of group names
        """
        user_info = self.get_user_info(username)
        return user_info['groups'] if user_info else []

    def is_user_in_group(self, username: str, group_name: str) -> bool:
        """
        Check if a user is a member of a specific group.
        
        Args:
            username: The username to check
            group_name: The group name to check against
            
        Returns:
            bool: True if user is in group, False otherwise
        """
        groups = self.get_user_groups(username)
        return group_name in groups 