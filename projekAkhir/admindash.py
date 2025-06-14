import logging as log
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import certifi
import io
import re

# --- Koneksi ke MongoDB Atlas ---
client = MongoClient(
    "mongodb+srv://dintananggreini99:1N7AN999intan@clusterkunanta.9pyj4dh.mongodb.net/?retryWrites=true&w=majority&appName=ClusterKunAnta"
    ,tls=True,
    tlsCAFile=certifi.where()
)

database = client["salesrecord"]
collection = database["order_mongo"]

try:
    client.admin.command('ping')
    log.info("Koneksi ke MongoDB Atlas berhasil!")
except Exception as e:
    log.error("Terjadi kesalahan saat menghubungkan ke MongoDB Atlas:", e)

# --- Ambil data dari MongoDB dan ubah ke DataFrame ---
data = list(collection.find({}, {"_id": 0}))
dataframeDB = pd.DataFrame(data)

# --- Sidebar Navigasi ---
st.sidebar.title("Menu")
halaman = st.sidebar.radio("Choose Page :", ["📋 Order Record",\
             "📊 Economic Order Quantity", "🔍 Tracer Customer"])

# --- Halaman Tabel ---
if halaman == "📋 Order Record":
    # Ambil data dari MongoDB
    data = collection.find({})

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


    dataFrameOrder = pd.DataFrame(flattened_data)

    st.title("📋 Order Record")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            dataFrameOrder.to_excel(writer, index=False, sheet_name='DataPesanan')
    output.seek(0)
    tanggal = datetime.now().strftime("%Y%m%d")
    nama_file = f"order_record_{tanggal}.xlsx"
    st.download_button(
            label= "📥 Download Data",
                data= output,
                file_name= nama_file,
                mime= "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    st.dataframe(dataFrameOrder)

# --- Halaman Grafik ---
elif halaman == "📊 Economic Order Quantity":
    st.title("📊 EOQ")
    data = collection.find({})

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
        barChart = px.bar(df_summary, x="makanan", y="jumlah", color="makanan")
        st.plotly_chart(barChart)
    else:
        st.warning("Data tidak ditemukan.")

elif halaman == "🔍 Tracer Customer":
    st.subheader("🔍 Tracer Customer")
    input_nama = st.text_input("Masukkan nama pemesan (bisa sebagian):")

    regex = re.compile(input_nama, re.IGNORECASE)
    hasil_cari = list(collection.find({"pemesan": regex}))

    if not hasil_cari:
            st.info(f"Tidak ditemukan data untuk pemesan yang cocok dengan '{input_nama}'.")
    else:
            # Kelompokkan berdasarkan nama
            pemesan_dict = {}
            for doc in hasil_cari:
                nama = doc['pemesan']
                tanggal = doc.get('date', '2000-01-01 00:00:00')
                items = doc.get('item', [])
                
                #menghindari duplikat
                if nama not in pemesan_dict:
                    pemesan_dict[nama] = {
                        "dates": [],
                        "items": []
                    }
                pemesan_dict[nama]["dates"].append(tanggal)
                pemesan_dict[nama]["items"].extend(items)

            for nama, data in pemesan_dict.items():
                try:
                    tanggal_terbaru = max(
                        data["dates"], key=lambda d: datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
                    )
                except ValueError:
                    tanggal_terbaru = max(data["dates"])  # fallback jika format tidak valid

                item_unik = list(dict.fromkeys(data["items"]))

                st.markdown(f"**Pelanggan {nama}** telah berkunjung ke Kun Anta Restaurant pada terakhir kali **{tanggal_terbaru}**.")
                st.markdown("Berikut menu yang dipesannya selama berkunjung:")
                for i, item in enumerate(item_unik, 1):
                    st.markdown(f"{i}. {item}")
