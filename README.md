# ProFTPD Management System

## Overview

The ProFTPD Management System consists of two web applications:

1. **ProFTPD Admin App**: A comprehensive management interface for administrators to manage users, groups, and server configurations.
2. **ProFTPD SFTP App**: A user-friendly web interface for SFTP users to manage their files and directories.

## Features

### Admin App Features
- User Management: Create, update, delete, and manage users
- Group Management: Assign users to groups and manage group memberships
- Bulk Operations: Perform bulk enable, disable, delete, and group assignment operations
- Import/Export: Import users from CSV and export user data
- Password Management: Generate and validate passwords
- User Status: View active, inactive, and disabled users
- Admin Logs: Track and display admin actions
- Profile Management: Create, update, and disable profiles
- Dynamic Table Updates: Refresh tables without page reload
- Color-coded Logs: Visual indicators for different action types

### SFTP App Features
- 🔐 Secure user authentication
- 📁 Directory navigation with breadcrumb support
- 📤 File upload with drag-and-drop support
- 📥 File download functionality
- 🗑️ File deletion (with permission checks)
- 🔒 Role-based access control
- 📱 Responsive design
- 🎨 Modern UI with Bootstrap 5 and Font Awesome icons

## Technologies Used

- Flask: Web framework for Python
- SQLAlchemy: ORM for database interactions
- Bootstrap: Frontend framework for responsive design
- JavaScript: For dynamic interactions and AJAX requests
- MySQL: Database for storing user and group data
- Flask-Session: For session management
- Werkzeug: For utilities and security features

## Installation

### Prerequisites

- Python 3.8 or higher
- MySQL
- pip (Python package installer)
- Virtual environment (recommended)

### Steps

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/proftpd_flask.git
    cd proftpd_flask
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create necessary directories:
    ```bash
    mkdir -p proftpd_admin_app/flask_session proftpd_sftp_app/flask_session
    ```

5. Set up the database:
    ```bash
    flask db init
    flask db migrate
    flask db upgrade
    ```

## Running the Applications

### Admin App
```bash
python run.py admin
```
Access at: `http://localhost:5000`

### SFTP App
```bash
python run.py sftp
```
Access at: `http://localhost:5001`

## Usage

### Admin App Usage

#### User Management
- Navigate to the home page to view the list of users
- Use the "Create User" button to add a new user
- Click on a user row to manage the user's details
- Use the bulk actions toolbar for multiple operations

#### Group Management
- Assign users to groups using the "Assign Group" dropdown
- Manage group memberships through the interface

#### Import/Export
- Import users from CSV using the "Import Users" button
- Export selected users to CSV using the "Export Selected" button

### SFTP App Usage

#### File Management
- Login with your SFTP credentials
- Navigate through directories using the breadcrumb navigation
- Upload files using drag-and-drop or the upload button
- Download files using the download button
- Delete files (if you have write permissions)

#### Demo Users
For testing purposes, the following demo users are available:

- **user1**
  - Documents (Read/Write)
  - Downloads (Read Only)
  - Public (Read/Write)

- **user2**
  - Projects (Read/Write)
  - Shared (Read Only)

## Project Structure

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
