# --- PROJE KONFİGÜRASYONU ---

# ÖLÇEK FAKTÖRÜ (1 veya 10)
SCALE_FACTOR = 10

# EĞİTİM VERİSİ SAYISI (Kaç farklı sorgu üretilecek?)
# SF=10 için 50-100 arası idealdir (süre açısından).
# SF=1 için 200-500 yapılabilir.
QUERY_COUNT = 50

# Veritabanı Ayarları
DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASS = "1991"
DB_PORT = "5432"

# Scale Factor'e göre otomatik değişen ayarlar
if SCALE_FACTOR == 10:
    DB_NAME = "tpch_db_10"
    DATA_FILE = "training_data_sf10.csv"
    MODEL_FILE = "model_sf10_xgboost.pkl"
    META_FEATURES = "meta_features_sf10.pkl"
    META_LABELS = "meta_labels_sf10.pkl"
    # SF=10'da %5 iyileşme bile kabul edilir (disk I/O kazancı)
    IMPROVEMENT_THRESHOLD = 1.00
else:
    DB_NAME = "tpch_db"
    DATA_FILE = "training_data_sf1.csv"
    MODEL_FILE = "model_sf1_xgboost.pkl"
    META_FEATURES = "meta_features_sf1.pkl"
    META_LABELS = "meta_labels_sf1.pkl"
    # SF=1'de indeksin gerçekten değmesi için %10 iyileşme bekleyelim
    IMPROVEMENT_THRESHOLD = 1.00

# Aday İndeks Listesi (Tüm scriptler ortak kullansın)
CANDIDATE_INDEXES = [
    ("idx_lineitem_shipdate", "lineitem", "l_shipdate"),
    ("idx_lineitem_discount", "lineitem", "l_discount"),
    ("idx_lineitem_quantity", "lineitem", "l_quantity"),
    ("idx_orders_orderdate", "orders", "o_orderdate"),
    ("idx_customer_mktsegment", "customer", "c_mktsegment"),
    ("idx_orders_custkey", "orders", "o_custkey")
]

def get_db_config():
    return {
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASS,
        "host": DB_HOST,
        "port": DB_PORT
    }