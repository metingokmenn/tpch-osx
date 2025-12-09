import psycopg2
import json
import time
import os
from workload import WorkloadGenerator

DB_CONFIG = {
    "dbname": "tpch_db",
    "user": "postgres",
    "password": "1991",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

def get_table_stats(conn, table_name):
    try:
        cur = conn.cursor()
        sql = "SELECT reltuples::bigint, pg_size_pretty(pg_total_relation_size(oid)) FROM pg_class WHERE relname = %s"
        cur.execute(sql, (table_name,))
        res = cur.fetchone()
        cur.close()
        return res if res else (0, "0 MB")
    except:
        return 0, "Error"

def analyze_query(conn, query_sql, query_type):
    try:
        cur = conn.cursor()
        if query_type == "SELECT":
            cur.execute(f"EXPLAIN (ANALYZE, COSTS, FORMAT JSON) {query_sql}")
            res = cur.fetchone()
            plan = res[0][0]
            exec_time = plan.get('Execution Time')
            cost = plan['Plan'].get('Total Cost')
            node_type = plan['Plan'].get('Node Type')
            # Join tiplerini yakalamak için detay (Nested Loop, Hash Join vs)
            if 'Plans' in plan['Plan']:
                 child_node = plan['Plan']['Plans'][0].get('Node Type')
                 node_type = f"{node_type} -> {child_node}"
            return exec_time, cost, node_type
        elif query_type == "UPDATE":
            start = time.time()
            cur.execute(query_sql)
            exec_time = (time.time() - start) * 1000
            return exec_time, 0, "UPDATE (Heap Access)"
    except Exception as e:
        print(f"Err: {e}")
        return None, None, "Error"
    finally:
        cur.close()

def log_to_file(filename, set_name, q_idx, q_type, sql, meta, stats, time_ms, cost, node):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"--- {set_name} | Query #{q_idx+1} [{q_type}] ---\n")
        f.write(f"SQL: {sql[:150]}... \n")
        f.write(f"📊 Stats: Time={time_ms:.2f}ms | Cost={cost} | Method={node}\n")
        f.write(f"ℹ️  Meta: Tables={meta['tables']} | JoinCount={meta['join_count']}\n")
        for tbl in meta['tables']:
            rows, size = stats.get(tbl, (0,'0'))
            f.write(f"   -> {tbl}: {rows:,} rows, {size}\n")
        f.write("-" * 50 + "\n")

def main():
    print("--- TPC-H WORKLOAD RUNNER (SET 1, 2, 3) ---")
    conn = get_db_connection()
    if not conn: return

    gen = WorkloadGenerator()
    
    # Proje isterlerine göre 3 farklı set [cite: 39, 40, 41]
    scenarios = [
        ("Set 1 (5 SELECT + 5 DML)", gen.generate_set_1()),
        ("Set 2 (10 SELECT)", gen.generate_set_2()),
        ("Set 3 (10 DML)", gen.generate_set_3())
    ]

    result_file = "project_execution_log.txt"
    with open(result_file, "w") as f:
        f.write(f"PROJE EXECUTION LOG - {time.strftime('%Y-%m-%d %H:%M')}\n\n")

    for set_name, workload in scenarios:
        print(f"\n🚀 Başlatılıyor: {set_name}")
        
        for i, (q_type, sql, meta) in enumerate(workload):
            print(f"   Running Q{i+1} [{q_type}]...", end="", flush=True)
            
            # Tablo istatistiklerini al
            current_stats = {tbl: get_table_stats(conn, tbl) for tbl in meta.get('tables', [])}
            
            # Çalıştır
            t_ms, cost, node = analyze_query(conn, sql, q_type)
            
            if t_ms is not None:
                print(f" Done! {t_ms:.2f}ms ({node})")
                log_to_file(result_file, set_name, i, q_type, sql, meta, current_stats, t_ms, cost, node)
            else:
                print(" Fail.")
                
    conn.close()
    print(f"\n✅ Tüm senaryolar tamamlandı. Detaylar: {os.path.abspath(result_file)}")

if __name__ == "__main__":
    main()