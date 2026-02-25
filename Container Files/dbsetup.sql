DROP TABLE IF EXISTS notebooks;
CREATE TABLE notebooks (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    notebook_name TEXT,
    pdf_path TEXT,
    output_path TEXT
)