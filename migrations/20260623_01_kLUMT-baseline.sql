-- baseline
-- depends: 

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunk (
	id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	snippet TEXT NOT NULL,
	embedding halfvec(300) NOT NULL
);
