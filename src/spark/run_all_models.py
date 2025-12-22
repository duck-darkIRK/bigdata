from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, udf
from pyspark.sql.types import DoubleType
from pyspark.ml import Pipeline
from pyspark.ml.classification import (
    LogisticRegression, NaiveBayes,
    DecisionTreeClassifier, RandomForestClassifier, GBTClassifier
)
from pyspark.ml.linalg import Vectors, VectorUDT
import numpy as np

# =============================
# Spark Session
# =============================
spark = SparkSession.builder \
    .appName("Run ML Models Raw vs Clean") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")
print("✅ Spark connected")

# =============================
# UDF chuyển bytes (float32) -> Vector
# =============================
def bytes_to_vector_float32(b):
    if b is None:
        return None
    arr = np.frombuffer(b, dtype=np.float32)
    return Vectors.dense(arr)

to_vector_udf = udf(bytes_to_vector_float32, VectorUDT())

# =============================
# Load labels
# =============================
labels = spark.read.format("org.apache.spark.sql.cassandra") \
    .options(table="reviews_labels", keyspace="reviews_ks").load()

# =============================
# Load features từ cùng 1 bảng, lọc theo data_type
# =============================
def load_features(dtype):
    df = spark.read.format("org.apache.spark.sql.cassandra") \
        .options(table="reviews_features", keyspace="reviews_ks").load() \
        .filter(col("data_type") == dtype)
    df = df.withColumn("features", to_vector_udf(col("features")))
    return df

raw_data = load_features("raw").join(labels, "id").withColumn("data_type", lit("raw"))
clean_data = load_features("clean").join(labels, "id").withColumn("data_type", lit("clean"))

# =============================
# Chọn cột cần thiết
# =============================
raw_data = raw_data.select("id", "text_field", "features", "rating_label", "data_type") \
                   .withColumnRenamed("text_field", "text") \
                   .withColumnRenamed("rating_label", "label")

clean_data = clean_data.select("id", "text_field", "features", "rating_label", "data_type") \
                       .withColumnRenamed("text_field", "text") \
                       .withColumnRenamed("rating_label", "label")

# =============================
# Models
# =============================
models = {
    "LR": LogisticRegression(maxIter=10, featuresCol="features", labelCol="label"),
    "NB": NaiveBayes(featuresCol="features", labelCol="label"),
    "DT": DecisionTreeClassifier(maxDepth=5, featuresCol="features", labelCol="label"),
    "RF": RandomForestClassifier(numTrees=30, maxDepth=5, featuresCol="features", labelCol="label"),
    "GBT": GBTClassifier(maxIter=20, maxDepth=5, featuresCol="features", labelCol="label")
}

# =============================
# UDF lấy probability nhãn positive
# =============================
def get_positive_prob(v):
    if v is None:
        return None
    return float(v.values[1]) if len(v.values) > 1 else 0.0

prob_udf = udf(get_positive_prob, DoubleType())

# =============================
# Chạy models
# =============================
def run(df, dtype):
    for name, model in models.items():
        print(f"🚀 {name} - {dtype}")

        pipe = Pipeline(stages=[model])
        train, test = df.randomSplit([0.8, 0.2], seed=42)
        preds = pipe.fit(train).transform(test)

        preds = preds.withColumn("probability", prob_udf(col("probability")))

        preds.select(
            lit(name).alias("model_name"),
            lit(dtype).alias("data_type"),
            col("id"),
            col("prediction").cast("int"),
            col("probability")
        ).write.format("org.apache.spark.sql.cassandra") \
         .mode("append") \
         .options(table="model_predictions", keyspace="reviews_ks") \
         .save()

        print(f"✅ Saved {name} - {dtype}")

# =============================
# Execute
# =============================
run(raw_data, "raw")
run(clean_data, "clean")

spark.stop()
print("🎉 DONE ALL MODELS")
