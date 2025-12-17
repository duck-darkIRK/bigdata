# 📊 Rating–Review Sentiment Consistency Analysis (Big Data)

# Hướng dẫn chạy dự án(dev)
## 1. Khởi tạo tài nguyên và môi trường

```commandline
docker compose up
```

## 2. Truy truy cập môi trường 
```commandline
docker compose exec cassandra cqlsh
docker compose exec python bash
```

## 3. Truy truy cập spark(lưu ý phải ở trong môi trường python(tức docker))
```commandline
pyspark --master spark://spark-master:7077
```

## 4. Lưu dữ liệu vào cassandra
```commandline
python3 src/storage/main.py 
```


---

## 1. Giới thiệu

### Tên đề tài

**Consistency Analysis between User Ratings and Review Sentiment using Apache Spark**

### Mục tiêu

Phân tích mức độ **tương đồng (consistency)** giữa:

* **Điểm đánh giá (Score 1–5 sao)** do người dùng chấm
* **Cảm xúc (Sentiment)** được trích xuất từ nội dung comment (review text)

Bài toán nhằm trả lời câu hỏi:

> *Liệu số sao người dùng chấm có thực sự phản ánh đúng nội dung đánh giá hay không?*

Đây là một bài toán phân tích dữ liệu lớn kết hợp **Spark SQL + Spark MLlib**, không yêu cầu kiến thức domain về sản phẩm.

---

## 2. Công nghệ sử dụng

| Thành phần        | Công nghệ              |
| ----------------- |------------------------|
| Ngôn ngữ          | Python                 |
| Xử lý dữ liệu lớn | Apache Spark           |
| Machine Learning  | Spark MLlib            |
| Lưu trữ phân tán  | Cassandra (Docker)     |
| Trực quan hóa     | matplotlib / seaborn   |
| Quản lý mã nguồn  | GitHub                 |

---

## 3. Cấu trúc thư mục dự án

```text
bigdata-rating-sentiment/
│
├── data/
│   ├── amazon-food-reviews-dataset.csv(tải file xuống vứt nó vô đây)
│
├── spark/
│   ├── 01_load_data.py
│   ├── 02_preprocessing.py
│   ├── 03_sentiment_model.py
│   ├── 04_consistency_analysis.py
│
├── visualization/
│   ├── plots.py
│
├── output/
│   ├── statistics/
│   ├── figures/
│
├── src/
│   ├── storage/
│   ├── service/
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 4. Luồng xử lý tổng thể (Workflow)

```text
Raw Data (CSV)
   ↓
Data Cleaning & Store in Cassandra
   ↓
Sentiment Analysis (Spark MLlib) → Generate SentimentScore & SentimentLabel
   ↓
Rating–Sentiment Consistency Analysis (compare Score vs SentimentScore/Label)
   ↓
Visualization & Reporting
```

### Dữ liệu sử dụng

* **Amazon Fine Food Reviews Dataset** (nguồn mở)
* Định dạng CSV
* Hàng trăm nghìn bản ghi

---

## 6. Bước 2 – Tiền xử lý dữ liệu

### 6.1 Làm sạch dữ liệu

Các bước tiền xử lý:

* Loại bỏ review bị thiếu `Score` hoặc `Text`
* Chuẩn hóa timestamp
* Loại bỏ ký tự đặc biệt
* Chuyển text về lowercase

**Lý do:**

* Giảm nhiễu dữ liệu
* Tăng độ chính xác cho mô hình NLP

### 6.2 Tạo nhãn rating

Quy ước:

* Score ≥ 4 → `Positive`
* Score ≤ 2 → `Negative`
* Score = 3 → `Neutral` (có thể loại bỏ)

---

## 9. Bước 5 – Phân tích cảm xúc (Sentiment Analysis)

### Pipeline Spark MLlib

1. Tokenizer
2. StopWordsRemover
3. TF-IDF
4. Classification Model

   * Logistic Regression
   * Naive Bayes

### Output

* `predicted_sentiment ∈ {Positive, Negative}`

---

## 10. Bước 6 – Phân tích Rating–Sentiment Consistency

### Định nghĩa

* **Matched**: Score label == Predicted sentiment
* **Mismatched**: Score label ≠ Predicted sentiment

### Các phân tích chính

* Tỷ lệ match / mismatch tổng thể
* Mismatch theo từng mức sao
* Consistency theo thời gian
* Review length vs consistency

---

## 11. Bước 7 – Trực quan hóa kết quả

### Các biểu đồ sử dụng

| Biểu đồ          | Mục đích                       |
| ---------------- | ------------------------------ |
| Bar chart        | Phân bố score                  |
| Bar chart        | Positive vs Negative sentiment |
| Confusion Matrix | So sánh score vs sentiment     |
| Bar chart        | Mismatch theo score            |
| Line chart       | Consistency theo năm           |
| Box plot         | Độ dài review vs consistency   |

---

## 12. Data collection & Cassandrah giá 1⭐ và 5⭐ có mức độ tương đồng cao với nội dung review

* Đánh giá 3⭐ có tỷ lệ không nhất quán cao nhất
* Cho thấy người dùng thường pip install -r requirements.txt

# Khởi động Cassandra

docker-compose up -dảm xúc

---

## 13. Phân công nhóm (ví dụ)

| Thành viên | Nhiệm vụ                  |
| ---------- | ------------------------- |
| SV1        | Data collection & HDFS    |
| SV2        | Preprocessing & Spark SQL |
| SV3        | Spark MLlib               |
| SV4        | Visualization & Report    |

---

## 14. Hướng dẫn chinstall -r requirements.txt

spark-submit spark/01_load_data.py
spark-submit spark/02_preprocessing.py
spark-submit spark/03_sentiment_model.py
spark-submit spark/04--

## 15. Ghi chú

* Dự án tập trung vào **Big Data processing**, không yêu cầu kiến thức domain sản phẩm
* Mục tiêu chính là **phân tích dữ liệu ở quy mô lớn bằng Spark**

---

✅ *Tài liệu này phục vụ cho báo cáo, triển khai code và thuyết trình bảo vệ môn Dữ liệu lớn.*
