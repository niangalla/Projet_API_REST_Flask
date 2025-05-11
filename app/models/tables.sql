CREATE TABLE IF NOT EXISTS groupe (
    id SERIAL PRIMARY KEY,
    nom_groupe VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE ,
    prenom VARCHAR(50),
    nom VARCHAR(50),
    password VARCHAR(100) ,
    role VARCHAR(50) NOT NULL CHECK (role IN ('Administrateur', 'Utilisateur')),
    group_id INT REFERENCES group(id)
);

CREATE TABLE IF NOT EXISTS prompt (
    id SERIAL PRIMARY KEY,
    description TEXT NOT NULL,
    prix INT DEFAULT 1000,
    statut VARCHAR(20) NOT NULL DEFAULT 'EN_ATTENTE' CHECK (statut IN ('EN_ATTENTE', 'ACTIVER', 'A_REVOIR', 'RAPPEL', 'A_SUPPRIMER')),
    user_id INT REFERENCES users(id),
    moyenne_note FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vote (
    prompt_id INT REFERENCES prompt(id),
    user_id INT REFERENCES user(id),
    vote_date Date,
    points INT NOT NULL,
    PRIMARY KEY (prompt_id, user_id)
);

CREATE TABLE IF NOT EXISTS notation (
    prompt_id INT REFERENCES prompt(id),
    user_id INT REFERENCES user(id),
    valeur_note INT CHECK (rating_value BETWEEN 0 AND 5),
    date_note Date,
    PRIMARY KEY (prompt_id, user_id)
);

CREATE TABLE IF NOT EXISTS achat (
    id SERIAL PRIMARY KEY,
    prompt_id INT REFERENCES prompt(id),
    prix INT,
    date_achat Date,
    source VARCHAR(50)
);

INSERT INTO users (username,prenom, nom, password, role, group_id) VALUES
('admin@plateforme.sn','John','Doe', 'admin123', 'Administrateur', 1);

