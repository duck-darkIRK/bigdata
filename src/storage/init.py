from cassandra.cluster import Cluster

print("⏳ Connecting to Cassandra...")
cluster = Cluster(["cassandra"])
session = cluster.connect()
print("✅ Connected")

# =============================
# Keyspace
# =============================
session.execute("""
CREATE KEYSPACE IF NOT EXISTS reviews_ks
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
""")
session.set_keyspace("reviews_ks")

# =============================
# Tables
# =============================
session.execute("DROP TABLE IF EXISTS reviews_raw")
session.execute("DROP TABLE IF EXISTS reviews_cleaned")
session.execute("DROP TABLE IF EXISTS reviews_labels")
session.execute("DROP TABLE IF EXISTS reviews_features")  # thêm mới
session.execute("DROP TABLE IF EXISTS model_predictions")
session.execute("DROP TABLE IF EXISTS model_metrics")

# -----------------------------
# reviews_raw
# -----------------------------
session.execute("""
CREATE TABLE reviews_raw (
    id int PRIMARY KEY,
    score int,
    helpfulnessnumerator int,
    helpfulnessdenominator int,
    text text,
    text_length int
)
""")

# -----------------------------
# reviews_cleaned
# -----------------------------
session.execute("""
CREATE TABLE IF NOT EXISTS reviews_cleaned (
    id int PRIMARY KEY,
    score int,
    clean_text text,
    clean_text_length int,
    length_bucket text
)
""")

# -----------------------------
# reviews_labels
# -----------------------------
session.execute("""
CREATE TABLE IF NOT EXISTS reviews_labels (
    id int PRIMARY KEY,
    rating_label int,
    sentiment_text text
)
""")

# -----------------------------
# reviews_features
# -----------------------------
# reviews_features
session.execute("""
CREATE TABLE IF NOT EXISTS reviews_features (
    id int,
    data_type text,      -- 'raw' hoặc 'clean'
    features blob,
    text_field text,     -- raw_text hoặc clean_text
    PRIMARY KEY (id, data_type)
)
""")


# -----------------------------
# model_predictions
# -----------------------------
session.execute("""
CREATE TABLE IF NOT EXISTS model_predictions (
    model_name text,
    data_type text,
    id int,
    prediction int,
    probability float,
    PRIMARY KEY ((model_name, data_type), id)
)
""")

# -----------------------------
# model_metrics
# -----------------------------
session.execute("""
CREATE TABLE IF NOT EXISTS model_metrics (
    model_name text,
    data_type text,
    length_bucket text,
    accuracy float,
    precision float,
    recall float,
    f1_score float,
    PRIMARY KEY ((model_name, data_type), length_bucket)
)
""")

print("✅ Cassandra schema initialized successfully")
