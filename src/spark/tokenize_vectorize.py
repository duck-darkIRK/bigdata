from pyspark.sql import SparkSession
from pyspark.ml.feature import RegexTokenizer, StopWordsRemover, HashingTF, IDF
from pyspark.sql.functions import udf, col, lit
from pyspark.sql.types import BinaryType, ArrayType, StringType
import numpy as np

# =============================
# Spark Session
# =============================
spark = SparkSession.builder \
    .appName("Vectorize Raw & Clean Reviews") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")
print("✅ Spark connected")

# =============================
# UDFs
# =============================
# Lọc token ngắn
def filter_short(tokens):
    if tokens is None:
        return []
    return [t for t in tokens if len(t) > 2]

filter_udf = udf(filter_short, ArrayType(StringType()))

# Chuyển vector sang bytes float32
def vector_to_bytes(v):
    if v is None:
        return None
    arr = v.toArray().astype("float32")
    return bytearray(arr.tobytes())

to_bytes_udf = udf(vector_to_bytes, BinaryType())

# =============================
# Hàm tạo features
# =============================
def create_features(df, text_col, data_type):
    # Tokenizer & StopWords
    tokenizer = RegexTokenizer(inputCol=text_col, outputCol="tokens", pattern="\\W")
    remover = StopWordsRemover(inputCol="tokens", outputCol="filtered_tokens")

    df = tokenizer.transform(df)
    df = remover.transform(df)
    df = df.withColumn("filtered_tokens", filter_udf(col("filtered_tokens")))

    # HashingTF + IDF
    tf = HashingTF(inputCol="filtered_tokens", outputCol="raw_features", numFeatures=1024)
    idf = IDF(inputCol="raw_features", outputCol="features")
    df = tf.transform(df)
    df = idf.fit(df).transform(df)

    # Chuyển sang bytes + thêm data_type + text_field
    df_out = df.withColumn("features", to_bytes_udf(col("features"))) \
               .withColumn("data_type", lit(data_type)) \
               .withColumnRenamed(text_col, "text_field") \
               .select("id", "data_type", "features", "text_field")
    return df_out

# =============================
# Load dữ liệu
# =============================
df_clean = spark.read \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="reviews_cleaned", keyspace="reviews_ks") \
    .load()
print(f"📥 Loaded cleaned data: {df_clean.count()} rows")

df_raw = spark.read \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="reviews_raw", keyspace="reviews_ks") \
    .load()
print(f"📥 Loaded raw data: {df_raw.count()} rows")

# =============================
# Tạo features
# =============================
df_features_clean = create_features(df_clean, "clean_text", "clean")
df_features_raw = create_features(df_raw, "text", "raw")

# =============================
# Lưu chung bảng reviews_features
# =============================
df_features_clean.unionByName(df_features_raw).write \
    .format("org.apache.spark.sql.cassandra") \
    .mode("append") \
    .options(table="reviews_features", keyspace="reviews_ks") \
    .save()

print("✅ Features for both raw & clean saved successfully")
spark.stop()
