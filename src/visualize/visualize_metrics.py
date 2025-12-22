import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from cassandra.cluster import Cluster

# =============================
# Output folder tuyệt đối trong container
# =============================
OUT_DIR = "/app/output/metrics_img"
os.makedirs(OUT_DIR, exist_ok=True)

# =============================
# Connect Cassandra
# =============================
cluster = Cluster(["cassandra"])
session = cluster.connect("reviews_ks")
print("✅ Connected to Cassandra")

# =============================
# Load metrics
# =============================
rows = session.execute("""
SELECT model_name, data_type, length_bucket, accuracy, precision, recall, f1_score
FROM model_metrics
""")
data = pd.DataFrame(list(rows))
if data.empty:
    print("⚠️ No data in model_metrics table")
    exit(1)

# =============================
# Plot metrics by model/data_type/length_bucket
# =============================
sns.set(style="whitegrid")
metrics = ["accuracy", "precision", "recall", "f1_score"]

for metric in metrics:
    for dtype in data['data_type'].unique():
        df_sub = data[data['data_type'] == dtype]
        plt.figure(figsize=(10,6))
        sns.barplot(
            data=df_sub,
            x="model_name",
            y=metric,
            hue="length_bucket",
            palette="Set2"
        )
        plt.title(f"{metric.capitalize()} by Model and Length Bucket ({dtype})")
        plt.ylim(0,1)
        plt.ylabel(metric.capitalize())
        plt.xlabel("Model")
        plt.legend(title="Length Bucket")
        plt.tight_layout()

        out_file = os.path.join(OUT_DIR, f"{metric}_{dtype}.png")
        plt.savefig(out_file)
        plt.close()
        print(f"📦 Saved {out_file}")

# =============================
# Simple HTML linking PNGs
# =============================
html_path = os.path.join(OUT_DIR, "metrics.html")
with open(html_path, "w") as f:
    f.write("<html><body>\n")
    for metric in metrics:
        for dtype in data['data_type'].unique():
            f.write(f"<h2>{metric.capitalize()} - {dtype}</h2>\n")
            f.write(f'<img src="{metric}_{dtype}.png" style="max-width:100%;"><br>\n')
    f.write("</body></html>")

print(f"🎉 Visualization done. HTML saved at {html_path}")
