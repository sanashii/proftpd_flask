# ProFTPD Management System

A comprehensive web-based management system for ProFTPD, featuring an admin interface and a user-friendly SFTP client.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Applications](#running-the-applications)
- [Usage Instructions](#usage-instructions)
- [Database Schema](#database-schema)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Support](#support)

---

## Overview

This project provides a web-based management system for ProFTPD, allowing administrators to manage users, groups, and server configurations through a modern interface. It also includes a secure SFTP client for end users to manage their files. The system is designed for ease of use, security, and extensibility.

---

## Features

### Admin App

- **User Management:** Create, edit, delete, and disable users. Assign users to groups and set home directories.
- **Group Management:** Create and manage user groups for easier permission handling.
- **Permission & Quota Management:** Set storage quotas and permissions for users and groups.
- **Import/Export:** Bulk import/export user data via CSV.
- **Server Configuration:** Update ProFTPD settings directly from the web interface.
- **Log Management:** View and filter server logs, user activity, and file transfer history.
- **Dashboard:** Overview of system status, active users, and recent activity.

### SFTP App

- **Secure Authentication:** LDAP-based login for users.
- **File Management:** Upload, download, rename, move, and delete files and directories.
- **Directory Navigation:** Browse and manage files in a user-friendly interface.
- **Statistics:** View usage statistics, such as storage used and recent activity.
- **Permission Enforcement:** Access controls based on user/group permissions.

---

## Technologies Used

- **Backend:** Python 3.8+, Flask, SQLAlchemy
- **Frontend:** Bootstrap 5, JavaScript, HTML5
- **Database:** MySQL
- **FTP Server:** ProFTPD
- **Authentication:** LDAP
- **Other:** Gunicorn (optional for production), Docker (optional for deployment)

---

## System Requirements

- **Operating System:** Linux, macOS, or Windows (Linux recommended for production)
- **Python:** Version 3.8 or higher
- **MySQL:** Version 5.7 or higher
- **ProFTPD:** Version 1.3 or higher
- **LDAP Server:** OpenLDAP or compatible
- **Git:** For source code management

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/sanashii/proftpd_flask.git
cd proftpd_flask
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up the Database

- Create a MySQL database and user.
- Update the database connection string in `config.py`.
- Initialize the schema:

```bash
python init_db.py
```

### 5. Configure ProFTPD

- Copy `proftpd.conf.example` to your ProFTPD config directory as `proftpd.conf`.
- Edit the configuration to match your environment (database connection, LDAP, etc.).
- Restart ProFTPD:

```bash
sudo systemctl restart proftpd
```

### 6. Configure LDAP

- Update LDAP settings in `proftpd_sftp_app/config.py`.
- Ensure the LDAP server is running and accessible.

---

## Configuration

- **Database:**  
  Edit `config.py` to set your MySQL host, database, user, and password.
- **LDAP:**  
  Set LDAP server URL, base DN, and bind credentials in `config.py`.
- **ProFTPD:**  
  Ensure ProFTPD is configured to use SQL and/or LDAP authentication as needed.
- **Environment Variables:**  
  You may use a `.env` file for sensitive settings (see `.env.example`).

---

## Running the Applications

### Admin App

```bash
python proftpd_admin_app/app.py
```
- Default URL: [http://localhost:5000](http://localhost:5000)

### SFTP App

```bash
python proftpd_sftp_app/app.py
```
- Default URL: [http://localhost:5001](http://localhost:5001)

**Production:**  
For production deployments, use Gunicorn or a WSGI server and a reverse proxy (e.g., Nginx).

---

## Usage Instructions

### For Administrators

1. **Login** to the Admin App using your admin credentials.
2. **User Management:**  
   - Add new users, assign them to groups, and set their home directories.
   - Edit or disable users as needed.
3. **Group Management:**  
   - Create groups and assign users.
   - Set group-level permissions and quotas.
4. **Server Configuration:**  
   - Update ProFTPD settings from the web interface.
   - Restart or reload the server as needed.
5. **Monitor Logs:**  
   - View user activity, file transfers, and server events.
   - Filter logs by user, date, or event type.

### For End Users

1. **Login** to the SFTP App with your LDAP credentials.
2. **File Operations:**  
   - Upload, download, rename, move, and delete files.
   - Create and manage directories.
3. **Statistics:**  
   - View your storage usage and recent activity.
4. **Logout** when finished.

---

## Database Schema
Overall database scheme
```sql
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

Below are the table breakdowns used by the ProFTPD Management System.

### `users` Table

```sql
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
  PRIMARY KEY (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
```

---

### `groups` Table

```sql
CREATE TABLE `groups` (
  `groupname` varchar(128) NOT NULL,
  `gid` int(11) DEFAULT NULL,
  PRIMARY KEY (`groupname`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
```

---

### `user_groups` Table

```sql
CREATE TABLE `user_groups` (
  `username` varchar(128) NOT NULL,
  `groupname` varchar(128) NOT NULL,
  PRIMARY KEY (`username`, `groupname`),
  FOREIGN KEY (`username`) REFERENCES `users` (`username`) ON DELETE CASCADE,
  FOREIGN KEY (`groupname`) REFERENCES `groups` (`groupname`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
```

---

### `logs` Table

```sql
CREATE TABLE `logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(128) DEFAULT NULL,
  `action` varchar(255) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `details` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
```

---

### `quotas` Table (if using quotas)

```sql
CREATE TABLE `quotas` (
  `username` varchar(128) NOT NULL,
  `quota_type` varchar(32) NOT NULL, -- e.g., 'user', 'group'
  `bytes_in_avail` bigint(20) DEFAULT NULL,
  `bytes_out_avail` bigint(20) DEFAULT NULL,
  `files_in_avail` int(11) DEFAULT NULL,
  `files_out_avail` int(11) DEFAULT NULL,
  PRIMARY KEY (`username`, `quota_type`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
```

---

**Note:**  
- You may have additional tables for advanced features (e.g., password reset tokens, audit logs, etc.).
- Adjust field types and constraints as needed for your environment.

---

## Security Considerations

- **Password Security:** Passwords are hashed using industry-standard algorithms.
- **Session Management:** Secure cookies and session timeouts are enforced.
- **CSRF/XSS Protection:** All forms are protected against CSRF; input is sanitized.
- **LDAP Authentication:** Ensures only authorized users can access the system.
- **SSL/TLS:** Strongly recommended for all web and FTP connections.
- **Access Controls:** Role-based access for admin and user functions.

---

## Troubleshooting

- **Database Connection Errors:**  
  - Check your database credentials and ensure MySQL is running.
  - Verify the database user has the correct permissions.
- **LDAP Authentication Fails:**  
  - Confirm LDAP server address and credentials in `config.py`.
  - Test LDAP connectivity using `ldapsearch`.
- **ProFTPD Issues:**  
  - Review ProFTPD logs (`/var/log/proftpd/`).
  - Check configuration syntax and permissions.
- **Web App Errors:**  
  - Check logs in the `logs/` directory.
  - Ensure all dependencies are installed and environment variables are set.

---

## Contributing

We welcome contributions!

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make your changes and commit them.
4. Push to your fork and submit a pull request.
5. Please follow the existing code style and include tests where appropriate.

---

## Acknowledgments

- [ProFTPD](https://www.proftpd.org/)
- [Flask](https://flask.palletsprojects.com/)
- [Bootstrap](https://getbootstrap.com/)
- [OpenLDAP](https://www.openldap.org/)
- All contributors and open-source libraries used.
