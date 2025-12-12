import random
from datetime import date, timedelta

class WorkloadGenerator:
    def __init__(self):
        self.start_date = date(1993, 1, 1)
        self.end_date = date(1997, 12, 31)

    def get_random_date(self):
        days_between = (self.end_date - self.start_date).days
        random_days = random.randrange(days_between)
        return self.start_date + timedelta(days=random_days)

    def generate_q6(self):
        # GÜNCELLEME: '1 month' yerine '5 days' yaptık.
        # Bu, "Needle in a haystack" (Samanlıkta iğne) etkisi yaratır.
        rand_date = self.get_random_date()
        rand_qty = random.randint(20, 30)
        rand_discount = round(random.uniform(0.02, 0.09), 2)
        
        # Filtreyi daralttık
        sql = f"""SELECT sum(l_extendedprice * l_discount) as revenue FROM lineitem WHERE l_shipdate >= DATE '{rand_date}' AND l_shipdate < DATE '{rand_date}' + INTERVAL '5 days' AND l_discount BETWEEN {rand_discount} - 0.01 AND {rand_discount} + 0.01 AND l_quantity < {rand_qty};"""
        
        meta = {"tables": ["lineitem"], "filter_range_days": 5, "join_count": 0, "query_type_label": "SCAN_HEAVY"}
        return sql.strip(), meta

    def generate_q1(self):
        delta = random.randint(60, 120)
        sql = f"""SELECT l_returnflag, l_linestatus, sum(l_quantity) as sum_qty, sum(l_extendedprice) as sum_base_price, sum(l_extendedprice * (1 - l_discount)) as sum_disc_price, sum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge, avg(l_quantity) as avg_qty, avg(l_extendedprice) as avg_price, avg(l_discount) as avg_disc, count(*) as count_order FROM lineitem WHERE l_shipdate <= date '1998-12-01' - integer '{delta}' GROUP BY l_returnflag, l_linestatus ORDER BY l_returnflag, l_linestatus;"""
        meta = {"tables": ["lineitem"], "filter_range_days": 2500 - delta, "join_count": 0, "query_type_label": "AGG_HEAVY"}
        return sql.strip(), meta

    def generate_q3(self):
        segments = ['BUILDING', 'AUTOMOBILE', 'MACHINERY', 'HOUSEHOLD', 'FURNITURE']
        rand_segment = random.choice(segments)
        rand_date = date(1995, 3, 15)
        sql = f"""SELECT l_orderkey, sum(l_extendedprice * (1 - l_discount)) as revenue, o_orderdate, o_shippriority FROM customer, orders, lineitem WHERE c_mktsegment = '{rand_segment}' AND c_custkey = o_custkey AND l_orderkey = o_orderkey AND o_orderdate < DATE '{rand_date}' AND l_shipdate > DATE '{rand_date}' GROUP BY l_orderkey, o_orderdate, o_shippriority ORDER BY revenue desc, o_orderdate LIMIT 10;"""
        meta = {"tables": ["customer", "orders", "lineitem"], "filter_range_days": 0, "join_count": 2, "query_type_label": "JOIN_HEAVY"}
        return sql.strip(), meta

    def generate_update_pk(self):
        rand_orderkey = random.randint(1, 1500000)
        rand_linenumber = random.randint(1, 4)
        sql = f"""UPDATE lineitem SET l_quantity = l_quantity WHERE l_orderkey = {rand_orderkey} AND l_linenumber = {rand_linenumber};"""
        meta = {"tables": ["lineitem"], "filter_range_days": 0, "join_count": 0, "query_type_label": "DML"}
        return sql.strip(), meta

    def generate_set_1(self):
        workload = []
        for _ in range(5): workload.append(("SELECT", *self._get_random_select()))
        for _ in range(3): workload.append(("UPDATE", *self._get_random_dml()))
        random.shuffle(workload)
        return workload

    def generate_set_2(self):
        workload = []
        for _ in range(5): workload.append(("SELECT", *self._get_random_select()))
        return workload

    def generate_set_3(self):
        return [("UPDATE", *self._get_random_dml()) for _ in range(3)]

    def _get_random_select(self):
        dice = random.random()
        if dice < 0.33: return self.generate_q6()
        elif dice < 0.66: return self.generate_q1()
        else: return self.generate_q3()

    def _get_random_dml(self):
        return self.generate_update_pk()