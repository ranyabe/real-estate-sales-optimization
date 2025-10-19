# optimize_sales_schedule.py
import os
import pandas as pd
from itertools import product

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

lots = pd.read_csv('/Users/mac/Downloads/Response Request Lots.csv')
costs = pd.read_csv('/Users/mac/Downloads/Construction Costs.csv')

months = list(costs["month"].astype(int))
lot_ids = list(lots["lot_id"])
price = dict(zip(lots["lot_id"], lots["price"]))
cost_per_lot = dict(zip(lots["lot_id"], lots["cost"]))
earliest = dict(zip(lots["lot_id"], lots["earliest_month"]))
construction_cost = dict(zip(costs["month"], costs["construction_cost"]))

monthly_sales_cap = 8
initial_cash = 0

def run_pulp():
    import pulp as pl
    mdl = pl.LpProblem("RealEstate_Sales_Phasing_OR", pl.LpMinimize)
    x = pl.LpVariable.dicts("x", (lot_ids, months), lowBound=0, upBound=1, cat=pl.LpBinary)
    draw = pl.LpVariable.dicts("draw", months, lowBound=0, cat=pl.LpContinuous)
    balance = pl.LpVariable.dicts("balance", months, lowBound=0, cat=pl.LpContinuous)
    # constraints
    for l in lot_ids:
        mdl += pl.lpSum(x[l][m] for m in months) <= 1
        for m in months:
            if m < int(earliest[l]):
                mdl += x[l][m] == 0
    for m in months:
        mdl += pl.lpSum(x[l][m] for l in lot_ids) <= monthly_sales_cap
    cash_in = {m: pl.lpSum(price[l]*x[l][m] for l in lot_ids) for m in months}
    lot_out = {m: pl.lpSum(cost_per_lot[l]*x[l][m] for l in lot_ids) for m in months}
    for i, m in enumerate(months):
        if i == 0:
            mdl += balance[m] == initial_cash + cash_in[m] - (construction_cost[m] + lot_out[m]) + draw[m]
        else:
            mp = months[i-1]
            mdl += balance[m] == balance[mp] + cash_in[m] - (construction_cost[m] + lot_out[m]) + draw[m]
    total_draw = pl.lpSum(draw[m] for m in months)
    total_margin = pl.lpSum((price[l]-cost_per_lot[l])*x[l][m] for l,m in product(lot_ids, months))
    mdl += total_draw - 1e-6*total_margin
    mdl.solve(pl.PULP_CBC_CMD(msg=False))
    status = pl.LpStatus[mdl.status]
    if status not in ("Optimal", "Feasible"):
        raise RuntimeError("PuLP failed with status: %s" % status)
    sales = []
    for l in lot_ids:
        sold_month = 0
        for m in months:
            if pl.value(x[l][m]) > 0.5:
                sold_month = m
                break
        sales.append({"lot_id": l, "sold_month": sold_month})
    sales_df = pd.DataFrame(sales).merge(lots, on="lot_id", how="left").sort_values(["sold_month","lot_id"])
    monthly = []
    bal_prev = initial_cash
    for m in months:
        cin = sum(price[l]*pl.value(x[l][m]) for l in lot_ids)
        lout = sum(cost_per_lot[l]*pl.value(x[l][m]) for l in lot_ids)
        site = construction_cost[m]
        d = pl.value(draw[m])
        bal = pl.value(balance[m])
        monthly.append({"month": m,"cash_in_from_sales": round(cin,2),"lot_costs_out": round(lout,2),
                        "construction_cost": site,"bank_draw": round(d,2),"balance_end": round(bal,2)})
        bal_prev = bal
    monthly_df = pd.DataFrame(monthly)
    return sales_df, monthly_df

def run_greedy():
    # Fallback: simple heuristic — each month sell up to cap among eligible lots by (price - cost) descending.
    remaining = set(lot_ids)
    records = []
    balance = initial_cash
    monthly_rows = []
    for m in months:
        eligible = [l for l in remaining if earliest[l] <= m]
        # sort by margin then price
        eligible.sort(key=lambda l: (price[l]-cost_per_lot[l], price[l]), reverse=True)
        to_sell = eligible[:monthly_sales_cap]
        cash_in = sum(price[l] for l in to_sell)
        lot_out = sum(cost_per_lot[l] for l in to_sell)
        site = construction_cost[m]
        # compute minimum draw to keep non-negative
        tentative = balance + cash_in - lot_out - site
        draw = 0 if tentative >= 0 else -tentative
        balance = tentative + draw
        for l in to_sell:
            records.append({"lot_id": l, "sold_month": m})
            remaining.remove(l)
        monthly_rows.append({"month": m,"cash_in_from_sales": cash_in,"lot_costs_out": lot_out,
                             "construction_cost": site,"bank_draw": draw,"balance_end": balance})
    # unsold get 0
    for l in remaining:
        records.append({"lot_id": l, "sold_month": 0})
    sales_df = pd.DataFrame(records).merge(lots, on="lot_id", how="left").sort_values(["sold_month","lot_id"])
    monthly_df = pd.DataFrame(monthly_rows)
    return sales_df, monthly_df

try:
    sales_df, monthly_df = run_pulp()
    mode = "PuLP (MILP)"
except Exception as e:
    sales_df, monthly_df = run_greedy()
    mode = "Greedy fallback (no PuLP)"

sales_df.to_csv(os.path.join(RESULTS_DIR, "sales_schedule.csv"), index=False)
monthly_df.to_csv(os.path.join(RESULTS_DIR, "monthly_cashflow.csv"), index=False)
print("Solved with mode:", mode)
print("Saved results to results/*.csv")