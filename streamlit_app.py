
# streamlit_app.py
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(BASE_DIR, "results")

st.set_page_config(page_title="Real Estate OR Optimizer", layout="wide")
st.title("🏗️ Real Estate Sales Phasing — OR Demo")

sales_path = os.path.join(RESULTS_DIR, "sales_schedule.csv")
monthly_path = os.path.join(RESULTS_DIR, "monthly_cashflow.csv")

if not (os.path.exists(sales_path) and os.path.exists(monthly_path)):
    st.error("Run optimize_sales_schedule.py first to generate results.")
    st.stop()

sales = pd.read_csv(sales_path)
monthly = pd.read_csv(monthly_path)

st.subheader("Sales Schedule")
st.dataframe(sales[["lot_id","type","floor","surface_m2","view_premium","price","cost","earliest_month","sold_month"]])

st.subheader("Monthly Cashflow")
st.dataframe(monthly)

# Chart: balance over time
st.subheader("Balance Over Time")
fig1, ax1 = plt.subplots()
ax1.plot(monthly["month"], monthly["balance_end"])
ax1.set_xlabel("Month")
ax1.set_ylabel("End Balance (MAD)")
st.pyplot(fig1)

st.subheader("Bank Draw Per Month")
fig2, ax2 = plt.subplots()
ax2.bar(monthly["month"], monthly["bank_draw"])
ax2.set_xlabel("Month")
ax2.set_ylabel("Bank Draw (MAD)")
st.pyplot(fig2)
