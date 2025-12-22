from pyspark.sql import SparkSession
from pyspark.sql.functions import when, col, lit

spark = SparkSession.builder \
    .appName("Label Reviews") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print("✅ Spark connected")

df = spark.read \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="reviews_cleaned", keyspace="reviews_ks") \
    .load()

print(f"📥 Loaded cleaned data: {df.count()} rows")

# === Nhị phân ===
# 0 = negative (score <= 3), 1 = positive (score > 3)
df_labels = df.withColumn(
    "rating_label",
    when(col("score") > 3, 1).otherwise(0)
).withColumn(
    "sentiment_text",
    when(col("score") > 3, "positive").otherwise("negative")
)

df_labels.select("id", "rating_label", "sentiment_text") \
    .write \
    .format("org.apache.spark.sql.cassandra") \
    .mode("append") \
    .options(table="reviews_labels", keyspace="reviews_ks") \
    .save()

print("✅ Labels saved")
spark.stop()
