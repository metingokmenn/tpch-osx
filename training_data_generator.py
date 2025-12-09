import psycopg2
import time
import os
import csv
import copy
from workload import WorkloadGenerator
import config  # Config dosyasını dahil ettik

def get_db_connection():
    try:
        conn = psycopg2.connect(**config.get_db_config())
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

def measure_time(conn, sql):
    try:
        cur = conn.cursor()
        start = time.time()
        cur.execute(sql)
        elapsed = (time.time() - start) * 1000
        cur.close()
        return elapsed
    except:
        return None

def manage_index(conn, action, index_def):
    name, table, col = index_def
    try:
        cur = conn.cursor()
        cur.execute("SET statement_timeout = 0;")
        if action == "CREATE":
            print(f"   🔨 Oluşturuluyor: {name}...", end="", flush=True)
            cur.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({col})")
            print(" Tamam.")
        elif action == "DROP":
            print(f"   🗑️  Siliniyor: {name}...", end="", flush=True)
            cur.execute(f"DROP INDEX IF EXISTS {name}")
            print(" Tamam.")
        cur.close()
    except Exception as e:
        print(f"\n   ⚠️ Index Error: {e}")

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

def extract_features(conn, q_id, q_type, meta):
    features = {
        "query_id": q_id,
        "query_type": 1 if q_type == "SELECT" else 0,
        "table_lineitem": 1 if "lineitem" in meta["tables"] else 0,
        "table_orders": 1 if "orders" in meta["tables"] else 0,
        "table_customer": 1 if "customer" in meta["tables"] else 0,
        "join_count": meta.get("join_count", 0),
        "filter_range_width": meta.get("filter_range_days", 0),
        "col_distinct_count": 0
    }
    if meta.get("tables"):
        tbl = meta["tables"][0]
        col = "l_shipdate" if tbl == "lineitem" else "c_mktsegment"
        features["col_distinct_count"] = get_column_stats(conn, tbl, col)
    return features

def main():
    # Sayıyı config'den alıyoruz
    target_count = config.QUERY_COUNT
    
    print(f"--- BATCH EĞİTİM VERİSİ TOPLAYICI ---")
    print(f"Hedef DB: {config.DB_NAME} (SF={config.SCALE_FACTOR})")
    print(f"Hedef Sorgu Sayısı: {target_count}")
    
    conn = get_db_connection()
    if not conn: return

    # 1. BÜYÜK İŞ YÜKÜ OLUŞTUR
    gen = WorkloadGenerator()
    workload = []
    
    print("1. İş yükü havuzu oluşturuluyor...")
    while len(workload) < target_count:
        batch = gen.generate_set_1() + gen.generate_set_2()
        workload.extend(batch)
    
    workload = workload[:target_count]
    
    data_rows = []

    # 2. BASELINE ÖLÇÜMLERİ
    print("\n2. İndekssiz (Base) süreler ölçülüyor...")
    for i, (q_type, sql, meta) in enumerate(workload):
        print(f"   [{i+1}/{target_count}] Base ölçüm...", end="\r")
        base_time = measure_time(conn, sql)
        
        if base_time is None: continue

        row = extract_features(conn, i, q_type, meta)
        row["base_time"] = base_time
        row["_sql"] = sql 
        
        for idx in config.CANDIDATE_INDEXES:
            row[f"label_{idx[0]}"] = 0
            
        data_rows.append(row)
    
    print(f"\n   ✅ {len(data_rows)} geçerli sorgu için base süreler alındı.")

    # 3. TOPLU İNDEKS TESTİ
    for idx_def in config.CANDIDATE_INDEXES:
        idx_name = idx_def[0]
        print(f"\n3. Test Ediliyor: {idx_name}")
        
        manage_index(conn, "CREATE", idx_def)
        
        improvement_count = 0
        for i, row in enumerate(data_rows):
            print(f"   -> Sorgu {i+1}/{len(data_rows)} deneniyor...", end="\r")
            
            target_table = idx_def[1]
            tables_in_query = []
            if row["table_lineitem"]: tables_in_query.append("lineitem")
            if row["table_orders"]: tables_in_query.append("orders")
            if row["table_customer"]: tables_in_query.append("customer")
            
            if target_table not in tables_in_query:
                continue

            indexed_time = measure_time(conn, row["_sql"])
            
            if indexed_time:
                # Eşik değerini de config'den alıyoruz
                if indexed_time < (row["base_time"] * config.IMPROVEMENT_THRESHOLD):
                    row[f"label_{idx_name}"] = 1
                    improvement_count += 1
        
        print(f"\n   ✅ {idx_name}: {improvement_count} sorguda iyileşme sağladı.")
        
        manage_index(conn, "DROP", idx_def)

    # 4. KAYDET
    print(f"\n4. CSV'ye Kaydediliyor: {config.DATA_FILE}")
    
    final_rows = []
    for r in data_rows:
        r_clean = copy.deepcopy(r)
        del r_clean["_sql"]
        final_rows.append(r_clean)

    fieldnames = ["query_id", "query_type", "table_lineitem", "table_orders", "table_customer", 
                  "join_count", "filter_range_width", "col_distinct_count", "base_time"]
    for idx in config.CANDIDATE_INDEXES: fieldnames.append(f"label_{idx[0]}")

    with open(config.DATA_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(final_rows)

    conn.close()
    print("\n--- BATCH EĞİTİM SETİ TAMAMLANDI ---")

if __name__ == "__main__":
    main()