import psycopg2
import pandas as pd
import joblib
import time
import os
from workload import WorkloadGenerator
import config # YENİ

def measure_time(conn, sql):
    cur = conn.cursor()
    start = time.time()
    cur.execute(sql)
    elapsed = (time.time() - start) * 1000
    cur.close()
    return elapsed

def get_column_stats(conn, table, column):
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT n_distinct FROM pg_stats WHERE tablename = '{table}' AND attname = '{column}'")
        res = cur.fetchone()
        cur.close()
        if res and res[0]:
            return res[0] if res[0] > 0 else 100000 
        return 1000
    except: return 0

def main():
    print(f"--- AKILLI ÖNERİ SİSTEMİ (SF={config.SCALE_FACTOR}) ---")
    
    if not os.path.exists(config.MODEL_FILE):
        print(f"Hata: {config.MODEL_FILE} bulunamadı.")
        return

    # Model ve Ayarları Yükle
    model = joblib.load(config.MODEL_FILE)
    features_col = joblib.load(config.META_FEATURES)
    labels_col = joblib.load(config.META_LABELS)
    
    # DB Bağlantısı
    try:
        conn = psycopg2.connect(**config.get_db_config())
        conn.autocommit = True
    except:
        print("DB Bağlantı Hatası!")
        return

    # Yeni Sorgu Üret
    gen = WorkloadGenerator()
    sql, meta = gen.generate_q6()
    print(f"\nSorgu Tipi: {meta['query_type_label']}")
    print(f"SQL: {sql[:80]}...")

    # Canlı Feature Çıkarımı
    col_distinct = 0
    if meta.get("tables"):
        tbl = meta["tables"][0]
        col = "l_shipdate" if tbl == "lineitem" else "c_mktsegment"
        col_distinct = get_column_stats(conn, tbl, col)

    row = {
        "query_type": 1,
        "table_lineitem": 1 if "lineitem" in meta["tables"] else 0,
        "table_orders": 1 if "orders" in meta["tables"] else 0,
        "table_customer": 1 if "customer" in meta["tables"] else 0,
        "join_count": meta.get("join_count", 0),
        "filter_range_width": meta.get("filter_range_days", 0),
        "col_distinct_count": col_distinct
    }
    
    df = pd.DataFrame([row])[features_col]
    
    # Tahmin
    print("Analiz ediliyor...")
    probs = model.predict_proba(df)
    recs = []
    
    # Label isminden indeks tanımını bulmak için tersine mühendislik
    # config.CANDIDATE_INDEXES listesini sözlüğe çevirelim
    idx_map = {f"label_{x[0]}": x for x in config.CANDIDATE_INDEXES}

    for i, prob_array in enumerate(probs):
        if prob_array[0][1] > 0.25: # %25 eşik
            label_name = labels_col[i]
            if label_name in idx_map:
                recs.append(idx_map[label_name])

    if not recs:
        print("❌ Öneri Yok (Mevcut yapı yeterli).")
    else:
        print(f"✅ Tavsiye: {[r[0] for r in recs]}")
        
        # Test
        print("   -> Base ölçülüyor...", end="")
        base = measure_time(conn, sql)
        print(f" {base:.0f} ms")

        print("   -> İndeksler kuruluyor...")
        for r in recs:
            cur = conn.cursor()
            cur.execute("SET statement_timeout = 0;")
            cur.execute(f"CREATE INDEX IF NOT EXISTS {r[0]} ON {r[1]} ({r[2]})")
            cur.close()
        
        print("   -> Optimize süre ölçülüyor...", end="")
        opt = measure_time(conn, sql)
        print(f" {opt:.0f} ms")

        # Temizlik
        for r in recs:
            cur = conn.cursor()
            cur.execute(f"DROP INDEX IF EXISTS {r[0]}")
            cur.close()

        if base > opt:
            print(f"🚀 HIZLANMA: %{((base-opt)/base)*100:.1f}")
        else:
            print("⚠️ Hızlanma yok.")

    conn.close()

if __name__ == "__main__":
    main()