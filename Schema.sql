CREATE DATABASE atm_db;
USE atm_db;

CREATE TABLE accounts (
    user_id VARCHAR(20) PRIMARY KEY,
    pin VARCHAR(10) NOT NULL,
    balance DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(20),
    type VARCHAR(50),
    amount DECIMAL(10,2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES accounts(user_id)
);
