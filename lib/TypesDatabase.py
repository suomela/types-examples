import sqlite3

DEFAULT_FILENAME = 'db/types.sqlite'

def open_db(filename=DEFAULT_FILENAME):
    conn = sqlite3.connect(filename)
    conn.execute('''PRAGMA foreign_keys = ON''')
    return conn

def create_if_needed(conn):
    conn.executescript('''

        CREATE TABLE IF NOT EXISTS stat (
            statcode TEXT NOT NULL PRIMARY KEY,
            description TEXT,
            ylabel TEXT,
            xlabel TEXT
        );

        INSERT OR IGNORE INTO stat (statcode, description, ylabel, xlabel)
        VALUES ('type-word', 'Types vs. running words', 'Types', 'Running words');

        INSERT OR IGNORE INTO stat (statcode, description, ylabel, xlabel)
        VALUES ('type-token', 'Types vs. tokens', 'Types', 'Tokens');

        INSERT OR IGNORE INTO stat (statcode, description, ylabel, xlabel)
        VALUES ('hapax-word', 'Hapaxes vs. running words', 'Hapaxes', 'Running words');

        INSERT OR IGNORE INTO stat (statcode, description, ylabel, xlabel)
        VALUES ('hapax-token', 'Hapaxes vs. tokens', 'Hapaxes', 'Tokens');

        INSERT OR IGNORE INTO stat (statcode, description, ylabel, xlabel)
        VALUES ('token-word', 'Tokens vs. running words', 'Tokens', 'Running words');

        CREATE TABLE IF NOT EXISTS defaultstat (
            statcode TEXT NOT NULL PRIMARY KEY REFERENCES stat(statcode)
        );

        INSERT OR IGNORE INTO defaultstat (statcode) VALUES ('type-word');
        INSERT OR IGNORE INTO defaultstat (statcode) VALUES ('type-token');

        CREATE TABLE IF NOT EXISTS defaultlevel (
            level REAL NOT NULL PRIMARY KEY
        );

        INSERT OR IGNORE INTO defaultlevel (level) VALUES (0.0001);
        INSERT OR IGNORE INTO defaultlevel (level) VALUES (0.001);
        INSERT OR IGNORE INTO defaultlevel (level) VALUES (0.01);
        INSERT OR IGNORE INTO defaultlevel (level) VALUES (0.1);

        CREATE TABLE IF NOT EXISTS corpus (
            corpuscode TEXT NOT NULL PRIMARY KEY,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS dataset (
            corpuscode TEXT NOT NULL REFERENCES corpus(corpuscode),
            datasetcode TEXT NOT NULL,
            description TEXT,
            PRIMARY KEY (corpuscode, datasetcode)
        );

        CREATE TABLE IF NOT EXISTS sample (
            corpuscode TEXT NOT NULL REFERENCES corpus(corpuscode),
            samplecode TEXT NOT NULL,
            wordcount INTEGER NOT NULL,
            description TEXT,
            PRIMARY KEY (corpuscode, samplecode)
        );

        CREATE TABLE IF NOT EXISTS collection (
            corpuscode TEXT NOT NULL REFERENCES corpus(corpuscode),
            collectioncode TEXT NOT NULL,
            groupcode TEXT,
            description TEXT,
            PRIMARY KEY (corpuscode, collectioncode)
        );

        CREATE TABLE IF NOT EXISTS sample_collection (
            corpuscode TEXT NOT NULL,
            samplecode TEXT NOT NULL,
            collectioncode TEXT NOT NULL,
            PRIMARY KEY (corpuscode, samplecode, collectioncode),
            FOREIGN KEY (corpuscode, samplecode) REFERENCES sample(corpuscode, samplecode),
            FOREIGN KEY (corpuscode, collectioncode) REFERENCES collection(corpuscode, collectioncode)
        );

        CREATE TABLE IF NOT EXISTS token (
            corpuscode TEXT NOT NULL,
            samplecode TEXT NOT NULL,
            datasetcode TEXT NOT NULL,
            tokencode TEXT NOT NULL,
            tokencount INTEGER NOT NULL,
            PRIMARY KEY (corpuscode, samplecode, datasetcode, tokencode),
            FOREIGN KEY (corpuscode, datasetcode) REFERENCES dataset(corpuscode, datasetcode),
            FOREIGN KEY (corpuscode, samplecode) REFERENCES sample(corpuscode, samplecode)
        );

        CREATE TABLE IF NOT EXISTS log (
            id INTEGER PRIMARY KEY NOT NULL,
            corpuscode TEXT NOT NULL,
            datasetcode TEXT NOT NULL,
            timestamp TEXT,
            description TEXT,
            FOREIGN KEY (corpuscode, datasetcode) REFERENCES dataset(corpuscode, datasetcode)
        );

        CREATE TABLE IF NOT EXISTS result_p (
            id INTEGER PRIMARY KEY NOT NULL,
            corpuscode TEXT NOT NULL,
            datasetcode TEXT NOT NULL,
            collectioncode TEXT NOT NULL,
            statcode TEXT NOT NULL REFERENCES stat(statcode),
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            total INTEGER NOT NULL,
            below INTEGER NOT NULL,
            above INTEGER NOT NULL,
            logid INTEGER NOT NULL REFERENCES log(id),
            UNIQUE (corpuscode, datasetcode, collectioncode, statcode),
            FOREIGN KEY (corpuscode, datasetcode) REFERENCES dataset(corpuscode, datasetcode),
            FOREIGN KEY (corpuscode, collectioncode) REFERENCES collection(corpuscode, collectioncode)
        );

        CREATE TABLE IF NOT EXISTS result_curve (
            id INTEGER PRIMARY KEY NOT NULL,
            corpuscode TEXT NOT NULL,
            datasetcode TEXT NOT NULL,
            statcode TEXT NOT NULL REFERENCES stat(statcode),
            level REAL NOT NULL,
            side TEXT NOT NULL,
            xslots INTEGER NOT NULL,
            yslots INTEGER NOT NULL,
            iterations INTEGER NOT NULL,
            logid INTEGER NOT NULL REFERENCES log(id),
            UNIQUE (corpuscode, datasetcode, statcode, level, side),
            FOREIGN KEY (corpuscode, datasetcode) REFERENCES dataset(corpuscode, datasetcode)
        );

        CREATE TABLE IF NOT EXISTS result_curve_point (
            curveid INTEGER NOT NULL REFERENCES result_curve(id),
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            PRIMARY KEY (curveid, x)
        );

        CREATE VIEW IF NOT EXISTS view_p AS
        SELECT corpuscode, datasetcode, collectioncode, statcode,
            'below' AS side, CAST(below AS REAL)/total AS p
        FROM result_p
        UNION
        SELECT corpuscode, datasetcode, collectioncode, statcode,
            'above' AS side, CAST(above AS REAL)/total AS p
        FROM result_p;

        CREATE VIEW IF NOT EXISTS view_p2 AS
        SELECT *,
            (SELECT COUNT(0) FROM view_p AS x WHERE x.p <= y.p) AS i,
            (SELECT COUNT(0) FROM view_p) AS n
        FROM view_p AS y ORDER BY p;

        CREATE VIEW IF NOT EXISTS view_q AS
        SELECT *,
            CAST(i AS REAL)/CAST(n AS REAL) AS expected,
            p / (CAST(i AS REAL)/CAST(n AS REAL)) AS q
        FROM view_p2;

        CREATE VIEW IF NOT EXISTS view_corpus AS
        SELECT corpuscode,
            SUM(sample.wordcount) AS wordcount, COUNT(0) AS samplecount
        FROM sample
        GROUP BY corpuscode;

        CREATE VIEW IF NOT EXISTS view_dataset AS
        SELECT corpuscode, datasetcode,
            SUM(tokencount) AS tokencount, COUNT(DISTINCT tokencode) AS typecount
        FROM token
        GROUP BY corpuscode, datasetcode;

        CREATE VIEW IF NOT EXISTS view_dataset_full AS
        SELECT corpuscode, datasetcode, tokencount, typecount, wordcount, samplecount
        FROM view_dataset JOIN view_corpus USING(corpuscode);

        CREATE VIEW IF NOT EXISTS view_collection AS
        SELECT corpuscode, collectioncode,
            SUM(sample.wordcount) AS wordcount, COUNT(0) AS samplecount
        FROM sample JOIN sample_collection USING(corpuscode, samplecode)
        GROUP BY corpuscode, collectioncode;

        CREATE VIEW IF NOT EXISTS view_collection_dataset AS
        SELECT corpuscode, collectioncode, datasetcode,
            SUM(tokencount) AS tokencount, COUNT(DISTINCT tokencode) AS typecount
        FROM token JOIN sample_collection USING(corpuscode, samplecode)
        GROUP BY corpuscode, collectioncode, datasetcode;

        CREATE VIEW IF NOT EXISTS view_collection_dataset_full AS
        SELECT corpuscode, collectioncode, datasetcode, tokencount, typecount, wordcount, samplecount
        FROM view_collection_dataset JOIN view_collection USING(corpuscode, collectioncode);

        CREATE VIEW IF NOT EXISTS view_missing_curve AS
        SELECT corpuscode, datasetcode, statcode, level, side
        FROM dataset
        JOIN defaultlevel
        JOIN defaultstat
        JOIN (SELECT 'lower' AS side UNION SELECT 'upper' AS side)
        EXCEPT
        SELECT corpuscode, datasetcode, statcode, level, side
        FROM result_curve;

        CREATE VIEW IF NOT EXISTS view_missing_p AS
        SELECT corpuscode, datasetcode, collectioncode, statcode
        FROM dataset
        JOIN collection USING (corpuscode)
        JOIN defaultstat
        EXCEPT
        SELECT corpuscode, datasetcode, collectioncode, statcode
        FROM result_p;

    ''')

def drop_views(conn):
    conn.executescript('''
        DROP VIEW IF EXISTS view_missing_p;
        DROP VIEW IF EXISTS view_missing_curve;
        DROP VIEW IF EXISTS view_collection_dataset_full;
        DROP VIEW IF EXISTS view_collection_dataset;
        DROP VIEW IF EXISTS view_collection;
        DROP VIEW IF EXISTS view_dataset_full;
        DROP VIEW IF EXISTS view_dataset;
        DROP VIEW IF EXISTS view_corpus;
        DROP VIEW IF EXISTS view_p;
    ''')

def delete_corpus(conn, corpuscode):
    conn.execute('DELETE FROM result_curve_point WHERE curveid IN (SELECT id FROM result_curve WHERE corpuscode = ?)', (corpuscode,))
    conn.execute('DELETE FROM result_curve WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM result_p WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM log WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM token WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM sample_collection WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM collection WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM sample WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM dataset WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM corpus WHERE corpuscode = ?', (corpuscode,))

def create_corpus(conn, corpuscode, description):
    conn.execute(
        'INSERT INTO corpus (corpuscode, description) VALUES (?, ?)',
        ( corpuscode, description )
    )

def delete_collection(conn, corpuscode, collectioncode):
    conn.execute('DELETE FROM result_p WHERE corpuscode = ? AND collectioncode = ?', (corpuscode, collectioncode))
    conn.execute('DELETE FROM sample_collection WHERE corpuscode = ? AND collectioncode = ?', (corpuscode, collectioncode))
    conn.execute('DELETE FROM collection WHERE corpuscode = ? AND collectioncode = ?', (corpuscode, collectioncode))

def create_collection(conn, corpuscode, groupcode, collectioncode, description):
    conn.execute(
        'INSERT INTO collection (corpuscode, groupcode, collectioncode, description) VALUES (?, ?, ?, ?)',
        (corpuscode, groupcode, collectioncode, description)
    )
