-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS product_db;

-- Use the newly created database
USE product_db;

-- Create the products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL
);

-- Insert some sample data
INSERT INTO products (name, description, price, stock) VALUES
('Laptop', 'A powerful and portable computer.', 1200.50, 50),
('Smartphone', 'A device to stay connected on the go.', 799.99, 150),
('Headphones', 'Noise-cancelling over-ear headphones.', 199.00, 300);