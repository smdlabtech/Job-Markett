DROP TABLE IF EXISTS job_offers_log CASCADE;

-- Création de la table des sources
CREATE TABLE sources (
    source_id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Création de la table des entreprises
CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE
);

-- Création de la table des localisations
CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    location VARCHAR(255),
    code_postal VARCHAR(10),
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    country VARCHAR(255)
);

-- Création de la table principale des offres d'emploi
CREATE TABLE job_offers (
    job_id SERIAL PRIMARY KEY,
    source_id INT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    external_id VARCHAR(255) NOT NULL,
    company_id INT REFERENCES companies(company_id) ON DELETE CASCADE,
    location_id INT NOT NULL REFERENCES locations(location_id) ON DELETE CASCADE,
    salary_min INT,
    salary_max INT,
    created_at TIMESTAMP NOT NULL,
    status TEXT,
    CONSTRAINT unique_external_source UNIQUE (external_id, source_id)
);

-- Table spécifique pour Adzuna
CREATE TABLE adzuna_offers (
    job_id INT PRIMARY KEY REFERENCES job_offers(job_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    contract_type VARCHAR(50),
    sector VARCHAR(255),
    description TEXT,
    apply_url TEXT
);

-- Table spécifique pour France Travail
CREATE TABLE france_travail_offers (
    job_id INT PRIMARY KEY REFERENCES job_offers(job_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    contract_type VARCHAR(50),
    sector VARCHAR(255),
    description TEXT,
    apply_url TEXT
);

-- Table spécifique pour JSearch
CREATE TABLE jsearch_offers (
    job_id INT PRIMARY KEY REFERENCES job_offers(job_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    contract_type VARCHAR(50),
    sector VARCHAR(255),
    description TEXT,
    apply_url TEXT
);

-- Table spécifique aux logs
CREATE TABLE job_offers_log (
    log_id SERIAL PRIMARY KEY,
    job_id INT REFERENCES job_offers(job_id) ON DELETE CASCADE,
    action VARCHAR(255) NOT NULL,  -- 'insert', 'update', 'delete'
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
    log_timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);
