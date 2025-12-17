import csv
import time
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement

print("⏳ Connecting to Cassandra...")

cluster = Cluster(["cassandra"])
session = cluster.connect()

print("✅ Connected")

# Create keyspace
session.execute("""
CREATE KEYSPACE IF NOT EXISTS reviews_ks
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
""")

session.set_keyspace("reviews_ks")

# Xóa bảng cũ nếu có
session.execute("DROP TABLE IF EXISTS reviews")
print("🗑️ Old table dropped")

# Create table
session.execute("""
CREATE TABLE IF NOT EXISTS reviews (
  Id int,
  Score int,
  HelpfulnessNumerator int,
  HelpfulnessDenominator int,
  Text text,
  SentimentScore float,
  SentimentLabel text,
  PRIMARY KEY (Id)
)
""")

insert_stmt = session.prepare("""
INSERT INTO reviews (
  Id,
  Score,
  HelpfulnessNumerator,
  HelpfulnessDenominator,
  Text
)
VALUES (?, ?, ?, ?, ?)
""")

BATCH_SIZE = 20   # 500 là an toàn
batch = BatchStatement()
count = 0
start_time = time.time()

print("📦 Start importing CSV...")

with open("data/amazon-food-reviews-dataset.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    def safe_int(x):
        try:
            return int(x)
        except ValueError:
            return 0  # hoặc None nếu cột nullable

    for row in reader:
        batch.add(
            insert_stmt,
            (
                int(row["Id"]),
                safe_int(row["Score"]),
                safe_int(row["HelpfulnessNumerator"]),
                safe_int(row["HelpfulnessDenominator"]),
                row["Text"]
            )
        )

        count += 1

        if count % BATCH_SIZE == 0:
            session.execute(batch)
            batch.clear()

            if count % 5000 == 0:
                elapsed = time.time() - start_time
                print(f"➡️ Inserted {count} rows ({elapsed:.1f}s)")

# flush remaining
if batch:
    session.execute(batch)

elapsed = time.time() - start_time
print(f"✅ Import completed: {count} rows in {elapsed:.1f}s")




