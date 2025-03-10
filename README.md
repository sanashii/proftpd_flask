# ProFTPD Management System

A comprehensive web-based management system for ProFTPD, featuring both an admin interface and a user-friendly SFTP client.

## Overview

This project consists of two main applications:

### 1. ProFTPD Admin App
A web-based administration interface for managing ProFTPD users, groups, and server configurations.

### 2. ProFTPD SFTP App
A modern web-based SFTP client interface that allows users to manage their files through a browser.

## Features

### Admin App Features
- User Management
  - Create, edit, and delete users
  - Set user permissions and quotas
  - Import/export user data
- Group Management
  - Create and manage user groups
  - Assign users to groups
- Server Configuration
  - View and modify server settings
  - Monitor server status
- Log Management
  - View transfer logs
  - Monitor user activities

### SFTP App Features
- Modern, responsive interface
- Secure user authentication
- File Operations
  - Upload and download files
  - Create and manage directories
  - Delete files and folders
- Directory Navigation
  - Browse through directories
  - View file details
  - Breadcrumb navigation
- Statistics Dashboard
  - Upload statistics with timespan selection
  - Download statistics with timespan selection
  - File count statistics with timespan selection
- Permission Management
  - Visual indicators for read/write permissions
  - Permission-based access control
- Progress Tracking
  - Real-time upload progress
  - Transfer status updates

## Technologies Used
- Flask (Python web framework)
- SQLAlchemy (Database ORM)
- Bootstrap 5 (Frontend framework)
- MySQL (Database)
- ProFTPD (FTP server)
- LDAP (Authentication system)

## Installation

### Prerequisites
- Python 3.8+
- MySQL Server
- ProFTPD Server
- LDAP Server (for authentication)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/proftpd_flask.git
   cd proftpd_flask
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```bash
   python init_db.py
   ```

5. Configure ProFTPD:
   - Copy `proftpd.conf.example` to `proftpd.conf`
   - Update the configuration with your settings
   - Restart ProFTPD service

6. Configure LDAP:
   - Update LDAP settings in `config.py`
   - Ensure LDAP server is running and accessible

## Running the Applications

### Admin App
```bash
python proftpd_admin_app/app.py
```
Access at: http://localhost:5000

### SFTP App
```bash
python proftpd_sftp_app/app.py
```
Access at: http://localhost:5001

## Usage

### Admin App
1. Log in with admin credentials
2. Navigate to Users or Groups section
3. Manage users and groups as needed
4. Monitor server status and logs

### SFTP App
1. Log in with user credentials
2. Browse directories and manage files
3. View statistics dashboard
4. Upload/download files as needed

## Project Structure
```
proftpd_flask/
├── proftpd_admin_app/
│   ├── app.py
│   ├── models.py
│   ├── forms.py
│   └── templates/
├── proftpd_sftp_app/
│   ├── app.py
│   ├── models.py
│   └── templates/
├── config.py
├── init_db.py
└── requirements.txt
```

## Database Schema
```MySQL
create table trax_users(
    `username` varchar(50) not null,
    `f_name` varchar(50),
    `l_name` varchar(50),
    `login_ldap` boolean,
    `is_enabled` boolean,
    `user_type` varchar(50),
    `password` varchar(128) NOT NULL,
    primary key(username)
);

CREATE TABLE `groups` (
  `groupname` varchar(128) NOT NULL,
  `gid` int(11) NOT NULL,
  `members` text,
  PRIMARY KEY (`groupname`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `host_keys` (
  `host` varchar(255) NOT NULL,
  `public_key` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `login_history` (
  `username` varchar(128) NOT NULL,
  `client_ip` varchar(128) NOT NULL,
  `server_ip` varchar(128) NOT NULL,
  `protocol` varchar(8) NOT NULL,
  `ts` timestamp NULL DEFAULT NULL,
  KEY `fk_login_history_username_idx` (`username`),
  KEY `idx_ts` (`ts`),
  CONSTRAINT `fk_login_history_username` FOREIGN KEY (`username`) REFERENCES `users` (`username`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `user_keys` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(128) NOT NULL,
  `public_key` text NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_user_keys_username_idx` (`username`),
  CONSTRAINT `fk_user_keys_username` FOREIGN KEY (`username`) REFERENCES `users` (`username`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=90 DEFAULT CHARSET=latin1;

CREATE TABLE `users` (
  `username` varchar(128) NOT NULL,
  `password` varchar(128) NOT NULL,
  `uid` int(11) DEFAULT NULL,
  `gid` int(11) DEFAULT NULL, 
  `homedir` varchar(255) DEFAULT NULL,
  `shell` varchar(255) DEFAULT NULL,
  `enabled` tinyint(1) DEFAULT '1',
  `name` varchar(255) DEFAULT NULL,
  `phone` varchar(45) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `last_accessed` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`username`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `xferlog` (
  `username` varchar(128) NOT NULL,
  `filename` text,
  `size` bigint(20) DEFAULT NULL,
  `host` tinytext,
  `address` varchar(128) DEFAULT NULL,
  `action` tinytext,
  `duration` tinytext,
  `localtime` timestamp NULL DEFAULT NULL,
  `success` tinytext,
  KEY `username_idx` (`username`),
  KEY `localtime_idx` (`localtime`),
  CONSTRAINT `username` FOREIGN KEY (`username`) REFERENCES `users` (`username`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE admin_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_time DATETIME NOT NULL,
    change_done TEXT NOT NULL,
    change_made_by VARCHAR(50) NOT NULL,
    FOREIGN KEY (change_made_by) REFERENCES trax_users(username)
);
```

## Security Considerations
- All passwords are hashed using secure algorithms
- Session management with secure cookies
- CSRF protection enabled
- Input validation and sanitization
- LDAP authentication for secure access
- SSL/TLS encryption for all connections

## Contributing
[Previous contributing section remains unchanged]

## License
[Previous license section remains unchanged]

## Acknowledgments
- ProFTPD team for the excellent FTP server
- Flask team for the web framework
- Bootstrap team for the frontend framework
- OpenLDAP team for the authentication system

## Support
[Previous support section remains unchanged]

## Roadmap
### Admin App
- [x] User management
- [x] Group management
- [x] Server configuration
- [x] Log management
- [ ] Advanced server monitoring
- [ ] Backup and restore functionality
- [ ] API endpoints for external integration

### SFTP App
- [x] File upload/download
- [x] Directory navigation
- [x] Permission management
- [x] Statistics dashboard
- [ ] File preview
- [ ] Drag and drop upload
- [ ] File sharing
- [ ] Advanced search
- [ ] Batch operations

## Changelog
### v1.0.0 (Initial Release)
- Basic user and group management
- File operations in SFTP interface
- Statistics dashboard with upload/download tracking
- LDAP authentication support
