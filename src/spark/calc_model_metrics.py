# src/spark/calc_model_metrics.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit

# =============================
# Spark session
# =============================
spark = SparkSession.builder \
    .appName("Calc Model Metrics") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print("✅ Spark connected")

# =============================
# Load model predictions
# =============================
preds = spark.read.format("org.apache.spark.sql.cassandra") \
    .options(table="model_predictions", keyspace="reviews_ks").load()

# =============================
# Load labels and add data_type
# =============================
labels_raw = spark.read.format("org.apache.spark.sql.cassandra") \
    .options(table="reviews_labels", keyspace="reviews_ks").load() \
    .withColumn("data_type", lit("raw"))

labels_clean = spark.read.format("org.apache.spark.sql.cassandra") \
    .options(table="reviews_labels", keyspace="reviews_ks").load() \
    .withColumn("data_type", lit("clean"))

labels_df = labels_raw.union(labels_clean)

# =============================
# Load length_bucket from cleaned data
# =============================
reviews_cleaned = spark.read.format("org.apache.spark.sql.cassandra") \
    .options(table="reviews_cleaned", keyspace="reviews_ks").load() \
    .select("id", "length_bucket")

# =============================
# Join predictions with labels and length_bucket
# =============================
df = preds.join(labels_df, on=["id","data_type"], how="inner")
df = df.join(reviews_cleaned, on="id", how="left")

# =============================
# Function to compute metrics
# =============================
def compute_metrics(sub_df):
    tp = sub_df.filter((col("prediction") == 1) & (col("rating_label") == 1)).count()
    tn = sub_df.filter((col("prediction") == 0) & (col("rating_label") == 0)).count()
    fp = sub_df.filter((col("prediction") == 1) & (col("rating_label") == 0)).count()
    fn = sub_df.filter((col("prediction") == 0) & (col("rating_label") == 1)).count()

    accuracy = (tp + tn) / max(tp + tn + fp + fn, 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-6)

    return accuracy, precision, recall, f1

# =============================
# Aggregate metrics by model_name, data_type, length_bucket
# =============================
metrics_list = []

groups = df.select("model_name", "data_type", "length_bucket").distinct().collect()
for g in groups:
    sub_df = df.filter(
        (col("model_name") == g["model_name"]) &
        (col("data_type") == g["data_type"]) &
        (col("length_bucket") == g["length_bucket"])
    )
    accuracy, precision, recall, f1 = compute_metrics(sub_df)
    metrics_list.append((
        g["model_name"], g["data_type"], g["length_bucket"],
        accuracy, precision, recall, f1
    ))

# =============================
# Convert to DataFrame
# =============================
metrics_df = spark.createDataFrame(metrics_list, schema=[
    "model_name", "data_type", "length_bucket", "accuracy", "precision", "recall", "f1_score"
])

# =============================
# Save to Cassandra
# =============================
metrics_df.write.format("org.apache.spark.sql.cassandra") \
    .mode("append") \
    .options(table="model_metrics", keyspace="reviews_ks") \
    .save()

print("✅ MODEL_METRICS updated")
spark.stop()
