`Table Structures`

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
