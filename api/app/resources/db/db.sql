-- =========================
-- CORE TABLES
-- =========================
DROP DATABASE IF EXISTS db_dv_dev;
CREATE DATABASE db_dv_dev;
USE db_dv_dev;

CREATE TABLE countries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    spanish_name TEXT,
    english_name TEXT,
    portuguese_name TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE genders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(15) NOT NULL UNIQUE,
    spanish_name TEXT,
    english_name TEXT,
    portuguese_name TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    spanish_name TEXT,
    english_name TEXT,
    portuguese_name TEXT,
    description TEXT,
    created_at DATETIME
);

CREATE TABLE species (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    spanish_name TEXT,
    english_name TEXT,
    portuguese_name TEXT,
    created_at DATETIME
);

CREATE TABLE breeds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    spanish_name TEXT,
    english_name TEXT,
    portuguese_name TEXT,
    species_id INT,
    is_mixed BOOLEAN DEFAULT FALSE,
    created_at DATETIME,
    UNIQUE(name, species_id),
    FOREIGN KEY (species_id) REFERENCES species(id)
);

-- =========================
-- USERS & PROFILES
-- =========================

CREATE TABLE profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(50),
    name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    document_number VARCHAR(50),
    contact_number VARCHAR(15),
    birthdate DATE,
    gender_id INT,
    country_id INT,
    role_id INT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    deleted_at DATETIME,
    FOREIGN KEY (gender_id) REFERENCES genders(id),
    FOREIGN KEY (country_id) REFERENCES countries(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(200),
    email VARCHAR(50) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    deleted_at DATETIME,
    active BOOLEAN,
    status VARCHAR(20),
    profile_id INT,
    FOREIGN KEY (profile_id) REFERENCES profiles(id)
);

-- =========================
-- INSTITUTIONS
-- =========================

CREATE TABLE institutions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    contact_number VARCHAR(20),
    address VARCHAR(255),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    deleted_at DATETIME,
    active BOOLEAN DEFAULT TRUE,
    status VARCHAR(20),
    created_by INT,
    updated_by INT,
    deleted_by INT,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id),
    FOREIGN KEY (deleted_by) REFERENCES users(id)
);

CREATE TABLE users_institutions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    institution_id INT NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    deleted_at DATETIME,
    created_by INT,
    updated_by INT,
    deleted_by INT,
    status VARCHAR(20),
    active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (institution_id) REFERENCES institutions(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- =========================
-- PATIENTS
-- =========================

CREATE TABLE patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    species_id INT,
    breed_id INT,
    age VARCHAR(20),
    gender_id INT,
    is_neutered BOOLEAN,
    owner_id INT,
    institution_id INT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    status VARCHAR(20),
    created_at DATETIME,
    updated_at DATETIME,
    deleted_at DATETIME,
    created_by INT,
    updated_by INT,
    deleted_by INT,
    FOREIGN KEY (species_id) REFERENCES species(id),
    FOREIGN KEY (breed_id) REFERENCES breeds(id),
    FOREIGN KEY (gender_id) REFERENCES genders(id),
    FOREIGN KEY (owner_id) REFERENCES profiles(id),
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);

-- =========================
-- STUDIES
-- =========================

CREATE TABLE veterinarians (
    id INT AUTO_INCREMENT PRIMARY KEY,
    profile_id INT,
    license_number VARCHAR(100),
    FOREIGN KEY (profile_id) REFERENCES profiles(id)
);

CREATE TABLE studies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    veterinarian_id INT,
    uploaded_by INT,
    institution_id INT,
    study_type VARCHAR(50),
    study_date DATETIME,
    observations TEXT,
    diagnosis TEXT,
    recommendations TEXT,
    raw_text TEXT,
    created_at DATETIME,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (veterinarian_id) REFERENCES veterinarians(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);

CREATE TABLE study_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    study_id INT,
    url TEXT,
    description VARCHAR(255),
    FOREIGN KEY (study_id) REFERENCES studies(id)
);

CREATE TABLE study_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    study_id INT,
    `key` VARCHAR(100),
    value VARCHAR(50),
    unit VARCHAR(20),
    reference_range VARCHAR(50),
    FOREIGN KEY (study_id) REFERENCES studies(id)
);
