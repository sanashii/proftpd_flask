# ProFTPD Management System

## Overview

The ProFTPD Management System is a web application designed to manage users, groups, and their associated data for a ProFTPD server. It provides functionalities for creating, updating, deleting, and bulk managing users, as well as importing and exporting user data.

## Features

- User Management: Create, update, delete, and manage users.
- Group Management: Assign users to groups and manage group memberships.
- Bulk Operations: Perform bulk enable, disable, delete, and group assignment operations.
- Import/Export: Import users from a CSV file and export user data to a CSV file.
- Password Management: Generate and validate passwords with a built-in password generator.
- User Status: View active, inactive, and disabled users.
- **Admin Logs**: Track and display admin actions such as creating, updating, and deleting profiles.
- **Profile Management**: Create, update, and disable profiles with radio buttons for enabling/disabling users.
- **Dynamic Table Updates**: Refresh and dynamically update tables without reloading the page.
- **Color-coded Logs**: Color-code admin logs based on action type (e.g., green for created, yellow for updated, red for deleted).

## Technologies Used

- Flask: Web framework for Python.
- SQLAlchemy: ORM for database interactions.
- Bootstrap: Frontend framework for responsive design.
- JavaScript: For dynamic interactions and AJAX requests.
- MySQL: Database for storing user and group data.

## Installation

### Prerequisites

- Python 3.x
- MySQL

### Steps

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/proftpd_flask.git
    cd proftpd_flask
    ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up the database:
    ```bash
    flask db init
    flask db migrate
    flask db upgrade
    ```

5. Run the application:
    ```bash
    flask run
    ```


## Usage

### User Management

- Navigate to the home page to view the list of users.
- Use the "Create User" button to add a new user.
- Click on a user row to manage the user's details.
- Use the bulk actions toolbar to perform bulk operations on selected users.

### Group Management

- Assign users to groups using the "Assign Group" dropdown in the bulk actions toolbar.

### Importing

- Use the "Import Users" button in the navigation bar to import users from a CSV file.
<br><strong>NOTE:</strong> importing users via csv should have a structure of:<br>

```csv
username, uid, gid, homedir, shell, enabled, name, phone, email, last_accessed
```

- the `username` column should not be empty
- the password is automatically generated upon every user in the csv file
- optional fields (may be left empty): <br>
`uid - Defaults to 1000 if empty`<br>
`gid - Defaults to 1000 if empty`<br>
`homedir - Sets to NULL if empty`<br>
`shell - Sets to NULL if empty`<br>
`enabled - Defaults to True if empty`<br>
`name - Sets to NULL if empty`<br>
`phone - Sets to NULL if empty`<br>
`email - Sets to NULL if empty `<br>

### Exporting

- Use the "Export Selected" button in the bulk actions toolbar to export selected users to a CSV file.

### Password Management

- Use the password generator in the user creation and management forms to generate strong passwords.

### Table Structures

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
