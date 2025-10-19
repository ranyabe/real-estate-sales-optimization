
# Real Estate Sales Phasing Optimization (OR demo)

This demo uses **Operations Research** to optimize the order and monthly phasing of unit sales
in a real-estate development to **delay bank draws** and improve **cashflow stability**.

## Contents
- `data/lots.csv` — inventory: price, cost, earliest sale month (synthetic sample)
- `data/construction_costs.csv` — monthly construction cost phasing
- `optimize_sales_schedule.py` — solver (MILP with PuLP, with a greedy fallback if PuLP isn't installed)
- `results/*.csv` — outputs: optimized sales schedule & monthly cashflow
- `streamlit_app.py` — a simple UI to browse results and show charts

## Run
```bash
pip install pulp pandas streamlit matplotlib
python optimize_sales_schedule.py
streamlit run streamlit_app.py
```

If PuLP isn't available, the script will run a **greedy heuristic** so you can still demo the concept.

## Idea
Not all "premium" units should be sold first. With the right model, you can sequence sales to
keep cash positive, minimize financing needs, and preserve average selling price.

## License
MIT
