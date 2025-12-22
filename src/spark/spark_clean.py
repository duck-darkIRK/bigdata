from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lower, regexp_replace, length, trim, when

spark = SparkSession.builder \
    .appName("Clean Amazon Reviews") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print("✅ Spark connected")

df_raw = spark.read \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="reviews_raw", keyspace="reviews_ks") \
    .load()

print(f"📥 Loaded raw data: {df_raw.count()} rows")

df_clean = (
    df_raw
    .withColumn("clean_text", lower(col("text")))
    .withColumn("clean_text", regexp_replace(col("clean_text"), "<[^>]+>", " "))
    .withColumn("clean_text", regexp_replace(col("clean_text"), "[^a-z0-9\\s]", " "))
    .withColumn("clean_text", regexp_replace(col("clean_text"), "\\s+", " "))
    .withColumn("clean_text", trim(col("clean_text")))
    .withColumn("clean_text_length", length(col("clean_text")))
    .withColumn(
        "length_bucket",
        when(col("clean_text_length") < 50, "short")
        .when(col("clean_text_length") < 200, "medium")
        .otherwise("long")
    )
)

final_df = df_clean.select(
    "id", "score", "clean_text", "clean_text_length", "length_bucket"
)

final_df.write \
    .format("org.apache.spark.sql.cassandra") \
    .mode("append") \
    .options(table="reviews_cleaned", keyspace="reviews_ks") \
    .save()

print("✅ Cleaned data saved")
spark.stop()
