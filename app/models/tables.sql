CREATE TABLE IF NOT EXISTS group (
    id SERIAL PRIMARY KEY,
    nom_group VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE ,
    password VARCHAR(100) ,
    role VARCHAR(10) NOT NULL CHECK (role IN ('admin', 'visiteur', 'user')),
    group_id INT REFERENCES group(id)
);

CREATE TABLE IF NOT EXISTS prompt (
    id SERIAL PRIMARY KEY,
    description TEXT NOT NULL,
    prix FLOAT DEFAULT 1000,
    statut VARCHAR(20) NOT NULL DEFAULT 'EN_ATTENTE' CHECK (statut IN ('EN_ATTENTE', 'ACTIVER', 'A_REVOIR', 'RAPPEL', 'A_SUPPRIMER')),
    user_id INT REFERENCES users(id),
    average_rating FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    last_state_change TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

);

CREATE TABLE IF NOT EXISTS vote (
    prompt_id INT REFERENCES prompt(id),
    user_id INT REFERENCES user(id),
    vote_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    prix FLOAT,
    date_achat Date
);
