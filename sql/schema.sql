CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS aeroplanes (
    id SERIAL PRIMARY KEY,
    icao24 VARCHAR(10),
    callsign VARCHAR(20),
    origin_country VARCHAR(100),
    velocity REAL,
    country_id INTEGER REFERENCES countries(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_aeroplanes_country ON aeroplanes(country_id);
CREATE INDEX IF NOT EXISTS idx_aeroplanes_velocity ON aeroplanes(velocity);
CREATE INDEX IF NOT EXISTS idx_aeroplanes_callsign ON aeroplanes(callsign);