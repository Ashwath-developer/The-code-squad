INSERT OR IGNORE INTO admin_users(id,name,email,password_hash) VALUES
(1,'System Administrator','admin@quickfire.local','$2b$12$v5p9fQy7xR8qGm3uC1nDqO4nJwJ8pX1aYgXbXJ1W2V3Z4A5B6C7D');
INSERT OR IGNORE INTO registered_users(id,name,phone,latitude,longitude,consent_sms) VALUES
(1,'Aarav Kumar','+919876543210',12.9730,77.5960,1),
(2,'Meera Singh','+919876543211',12.9725,77.5955,1),
(3,'Rahul Nair','+919876543212',12.9690,77.5940,1),
(4,'Priya Das','+919876543213',12.9650,77.5900,1),
(5,'Test Retry User','+919876543214',12.9720,77.5945,1);
INSERT OR IGNORE INTO system_settings(key,value) VALUES('sms_mode','simulation'),('max_retries','2');
