USE atm_db;

-- Insert test accounts
INSERT INTO accounts (user_id, pin, balance) VALUES
('12345678', '1234', 5000.00),
('87654321', '5678', 10000.00);

-- Insert test transactions
INSERT INTO transactions (user_id, type, amount) VALUES
('12345678', 'Deposit', 5000.00),
('87654321', 'Deposit', 10000.00),
('12345678', 'Withdraw', 1000.00);
