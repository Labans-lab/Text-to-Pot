-- Create DB and tables for TEXT TO POT
CREATE DATABASE IF NOT EXISTS texttopot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE texttopot;

-- users table (simple starter)
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NULL,
  email VARCHAR(255) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- recipes table
CREATE TABLE IF NOT EXISTS recipes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  ingredients TEXT NOT NULL,
  instructions TEXT NOT NULL,
  source VARCHAR(255) DEFAULT 'texttopot',
  created_by INT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- optional: logs
CREATE TABLE IF NOT EXISTS request_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  endpoint VARCHAR(255),
  payload TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
