import csv
import time
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement

# =============================
# Connect Cassandra
# =============================
print("⏳ Connecting to Cassandra...")
cluster = Cluster(["cassandra"])
session = cluster.connect("reviews_ks")
print("✅ Connected")

# =============================
# Prepared statement
# =============================
insert_stmt = session.prepare("""
INSERT INTO reviews_raw (
    id,
    score,
    helpfulnessnumerator,
    helpfulnessdenominator,
    text,
    text_length
) VALUES (?, ?, ?, ?, ?, ?)
""")

def safe_int(x):
    try:
        return int(x)
    except:
        return 0

# =============================
# Import CSV
# =============================
BATCH_SIZE = 20
MAX_ROWS = 50000
batch = BatchStatement()
count = 0
start_time = time.time()

print("📦 Start importing CSV...")

with open("data/amazon-food-reviews-dataset.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if count >= MAX_ROWS:
            break  # stop at 50k rows

        text = row["Text"]

        data = (
            safe_int(row["Id"]),
            safe_int(row["Score"]),
            safe_int(row["HelpfulnessNumerator"]),
            safe_int(row["HelpfulnessDenominator"]),
            text,
            len(text)
        )

        batch.add(insert_stmt, data)
        count += 1

        if count % BATCH_SIZE == 0:
            session.execute(batch)
            batch = BatchStatement()

        if count % 5000 == 0:
            elapsed = time.time() - start_time
            print(f"➡️ Inserted {count} rows ({elapsed:.1f}s)")

# Flush remaining
if len(batch) > 0:
    session.execute(batch)

elapsed = time.time() - start_time
print(f"✅ Import completed: {count} rows in {elapsed:.1f}s")
