import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
import plotly.express as px
from pymongo import MongoClient  
import certifi

# Koneksi ke MongoDB
client = MongoClient(
    "mongodb+srv://dintananggreini99:1N7AN999intan@clusterkunanta.9pyj4dh.mongodb.net\
        /?retryWrites=true&w=majority&appName=ClusterKunAnta"
    ,tls=True,
    tlsCAFile=certifi.where()
)

db = client["salesrecord"]
collection = db["order_mongo"]

# --- Sidebar Navigasi ---
st.sidebar.title("Menu")
halaman = st.sidebar.radio("Choose Page :", ["📋 Order Record", "📊 Economic Order Quantity"])

# Tambahan: Input teks untuk regex pencarian nama pemesan
regex_filter = st.sidebar.text_input("🔍 Filter Pemesan (Regex)", "")

# --- Halaman Tabel ---
if halaman == "📋 Order Record":
    # Ambil data dari MongoDB dengan regex filter pada 'pemesan'
    query = {"pemesan": {"$regex": regex_filter, "$options": "i"}} if regex_filter else {}
    data = collection.find(query)

    # Proses data nested jadi tabel datar
    flattened_data = []
    for doc in data:
        customer = doc.get("pemesan", "")
        items = doc.get("item", [])
        quantities = [
            int(q["$numberInt"]) if isinstance(q, dict) and "$numberInt" in q else int(q)
            for q in doc.get("manyitems", [])
        ]
        prices = [
            int(p["$numberInt"]) if isinstance(p, dict) and "$numberInt" in p else int(p)
            for p in doc.get("price", [])
        ]
        date_start_str = doc.get("date", "2000-01-01 00:00:00")
        try:
            date_start = datetime.strptime(date_start_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            date_start = datetime.now()

        for i in range(len(items)):
            row = {
                "customer": customer,
                "item": items[i] if i < len(items) else "",
                "quantity": quantities[i] if i < len(quantities) else 0,
                "price": prices[i] if i < len(prices) else 0,
                "date": (date_start + timedelta(days=i)).strftime("%m/%d/%Y %H:%M")
            }
            flattened_data.append(row)

    # Konversi ke DataFrame
    df = pd.DataFrame(flattened_data)

    st.title("📋 Order Record")
    if not df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='DataPesanan')
        output.seek(0)
        tanggal = datetime.now().strftime("%Y%m%d")
        nama_file = f"order_record_{tanggal}.xlsx"
        st.download_button(
            label="📥 Download Data",
            data=output,
            file_name=nama_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.dataframe(df)
    else:
        st.warning("Tidak ada data ditemukan.")

# --- Halaman Grafik ---
elif halaman == "📊 Economic Order Quantity":
    st.title("📊 EOQ")
    query = {"pemesan": {"$regex": regex_filter, "$options": "i"}} if regex_filter else {}
    data = collection.find(query)

    item_counter = {}

    for doc in data:
        items = doc.get("item", [])
        quantities = doc.get("manyitems", [])

        for item, qty in zip(items, quantities):
            jumlah = int(qty["$numberInt"]) if isinstance(qty, dict) and "$numberInt" in qty else int(qty)
            item_counter[item] = item_counter.get(item, 0) + jumlah

    if item_counter:
        df_summary = pd.DataFrame(list(item_counter.items()), columns=["makanan", "jumlah"])
        st.markdown("<h3 style='text-align: center;'>Economic Order Quantity</h3>", unsafe_allow_html=True)
        fig = px.bar(df_summary, x="makanan", y="jumlah", color="makanan")
        st.plotly_chart(fig)
    else:
        st.warning("Tidak ada data ditemukan.")
