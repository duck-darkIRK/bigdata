#!/bin/bash
set -e

# =============================
# CONFIG
# =============================
SPARK_MASTER="spark://spark-master:7077"
CONNECTOR="com.datastax.spark:spark-cassandra-connector_2.12:3.5.1"
SPARK_SUBMIT="/opt/spark/bin/spark-submit"
IVY_DIR="/tmp/.ivy2"

# Cassandra config
SPARK_CASS_CONF="
--conf spark.cassandra.connection.host=cassandra
--conf spark.cassandra.connection.port=9042
--conf spark.jars.ivy=${IVY_DIR}
"

# Log config (GIẢM SPAM)
LOG_SUPPRESS_CONF="
--conf spark.ui.showConsoleProgress=false
--conf spark.eventLog.enabled=false
--conf spark.sql.ui.explainMode=none
--conf spark.executor.extraJavaOptions=-Dlog4j2.disable.jmx=true\ -Dlog4j2.level=ERROR
--conf spark.driver.extraJavaOptions=-Dlog4j2.disable.jmx=true\ -Dlog4j2.level=ERROR
--conf spark.executor.extraJavaOptions=-Dorg.slf4j.simpleLogger.defaultLogLevel=error
--conf spark.driver.extraJavaOptions=-Dorg.slf4j.simpleLogger.defaultLogLevel=error
--conf spark.executor.extraJavaOptions=-Dorg.slf4j.simpleLogger.showDateTime=false
--conf spark.driver.extraJavaOptions=-Dorg.slf4j.simpleLogger.showDateTime=false
"


# Step bắt đầu (default = 0)
START_STEP=${1:-0}

echo "🚀 START PIPELINE (from step ${START_STEP})"

# =============================
# Prepare Ivy cache (QUAN TRỌNG)
# =============================
docker exec spark-master mkdir -p ${IVY_DIR}/cache
docker exec spark-worker mkdir -p ${IVY_DIR}/cache

# =============================
# STEP 0: Init Cassandra
# =============================
if [ "$START_STEP" -le 0 ]; then
  echo "🧱 [0] Init Cassandra schema"
  docker exec python-dev python3 src/storage/init.py
fi

# =============================
# STEP 1: Load raw data
# =============================
if [ "$START_STEP" -le 1 ]; then
  echo "📥 [1] Load raw data"
  docker exec python-dev python3 src/storage/load.py
fi

# =============================
# STEP 2: Clean
# =============================
if [ "$START_STEP" -le 2 ]; then
  echo "🧹 [2] Clean text"
  docker exec spark-master $SPARK_SUBMIT \
    --master $SPARK_MASTER \
    $SPARK_CASS_CONF \
    $LOG_CONF \
    --packages $CONNECTOR \
    /app/src/spark/spark_clean.py
fi

# =============================
# STEP 3: Label
# =============================
if [ "$START_STEP" -le 3 ]; then
  echo "🏷️ [3] Label reviews"
  docker exec spark-master $SPARK_SUBMIT \
    --master $SPARK_MASTER \
    $SPARK_CASS_CONF \
    $LOG_CONF \
    --packages $CONNECTOR \
    /app/src/spark/label_reviews.py
fi

# =============================
# STEP 4: Tokenize + Vectorize
# =============================
if [ "$START_STEP" -le 4 ]; then
  echo "🔤 [4] Tokenize & Vectorize"
  docker exec spark-master $SPARK_SUBMIT \
    --master $SPARK_MASTER \
    $SPARK_CASS_CONF \
    $LOG_CONF \
    --packages $CONNECTOR \
    /app/src/spark/tokenize_vectorize.py
fi

# =============================
# STEP 5: Run models
# =============================
if [ "$START_STEP" -le 5 ]; then
  echo "🤖 [5] Run ML models"
  docker exec spark-master $SPARK_SUBMIT \
    --master $SPARK_MASTER \
    $SPARK_CASS_CONF \
    $LOG_CONF \
    --packages $CONNECTOR \
    --conf spark.executor.memory=4G \
    --conf spark.driver.memory=8G \
    --conf spark.executor.cores=2 \
    --conf spark.sql.shuffle.partitions=20 \
    /app/src/spark/run_all_models.py
fi

# =============================
# STEP 6: Compute model metrics
# =============================
if [ "$START_STEP" -le 6 ]; then
  echo "📊 [6] Compute model metrics"
  docker exec spark-master $SPARK_SUBMIT \
    --master $SPARK_MASTER \
    $SPARK_CASS_CONF \
    $LOG_CONF \
    --packages $CONNECTOR \
    --conf spark.executor.memory=2G \
    --conf spark.driver.memory=4G \
    --conf spark.executor.cores=1 \
    /app/src/spark/calc_model_metrics.py
fi


# =============================
# STEP 7: Visualize model metrics
# =============================
if [ "$START_STEP" -le 7 ]; then
  echo "📈 [7] Visualize model metrics"
  docker exec python-dev python3 /app/src/visualize/visualize_metrics.py

  echo "📂 Copy metrics HTML/PNG to host"
  mkdir -p ./output/metrics_img
  docker cp python-dev:/app/output/metrics_img/. ./output/metrics_img/

  echo "🌐 Open metrics in browser"
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open ./output/metrics_img/metrics.html || true
  elif command -v open >/dev/null 2>&1; then
    open ./output/metrics_img/metrics.html || true
  else
    echo "⚠️ Mở ./output/metrics_img/metrics.html thủ công"
  fi
fi




echo "✅ PIPELINE FINISHED"
