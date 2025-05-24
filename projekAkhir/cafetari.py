import streamlit as st
from pymongo import MongoClient, errors
from datetime import datetime
import certifi

# URI Atlas dengan opsi TLS dan sertifikat
client = MongoClient(
    "mongodb+srv://dintananggreini99:1N7AN999intan@clusterkunanta.9pyj4dh.mongodb.net/?retryWrites=true&w=majority&appName=ClusterKunAnta"
    ,tls=True,
    tlsCAFile=certifi.where()
)

db = client["salesrecord"]
collection = db["order_mongo"]

try:
    client.admin.command('ping')
    print("Koneksi ke MongoDB Atlas berhasil!")
except Exception as e:
    print("Terjadi kesalahan saat menghubungkan ke MongoDB Atlas:", e)


def insert_order(name, food, drink):
    all_items = list(food.keys()) + list(drink.keys())
    quantities = []
    prices = []

    for item in all_items:
        key = f"porsi_{item}"
        if key in st.session_state:
            quantities.append(st.session_state[key])
        else:
            quantities.append(1)
        prices.append(food.get(item, 0) + drink.get(item, 0))

    document = {
        "pemesan": name,
        "item": all_items,
        "manyitems": quantities,
        "price": prices,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        collection.insert_one(document)
        st.success("✅ Pesanan berhasil disimpan!")
    except errors.PyMongoError as e:
        st.error(f"❌ Gagal menyimpan ke database: {e}")

if "page" not in st.session_state:
    st.session_state.page = 1

def next_page():
    st.session_state.page += 1

def double_next_page():
    st.session_state.page += 2

def prev_page():
    st.session_state.page -= 1

# Inisialisasi data hanya sekali
if "data" not in st.session_state:
    st.session_state.data = {
        "name": "",
        "food": {},
        "drink": {},
        "price": 0
    }

st.markdown("<h1 style='text-align: center;'>🍪 Kun Anta Coffe</h1>", unsafe_allow_html=True)

# HALAMAN 1: Input Nama
if st.session_state.page == 1:
    st.markdown("<h3 style='text-align: center;'>Hey, Foodie!👋</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Pesan, duduk, dan nikmati vibes-nya! 🍕☕</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    try:
        with col2:
            inName = st.text_input("Masukin nama kamu:", key="name")
            if st.button("🍽️ Pesan Makanan"):
                if not inName.strip():
                    raise ValueError("Masukin namamu dulu!")
                else:
                    st.session_state.data["name"] = inName
                    next_page()
    except ValueError as e:
        st.warning(str(e))

# HALAMAN 2: Pilih Makanan
elif st.session_state.page == 2:
    st.markdown("<h3 style='text-align: center;'>I'm so Hungry 🍽️</h3>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align: center;'>Choose Your Favorite Foods</h5>", unsafe_allow_html=True)

    menu = {
        "Mie Jawa": 12000,
        "Mie Ayam": 12000,
        "Mie Hot Goreng": 15000,
        "Mie Hot Kuah": 15000,
        "Ayam Geprek": 18000,
        "Siomay Original": 9000,
        "Siomay Ikan": 11000,
        "Udang Buble": 9000,
        "Udang Cheese": 11000,
        "Risoles Original": 9000,
        "Risoles Cheese": 10000,
        "Risoles Vegen": 9000,
    }

    pesanan = {}
    totalHarga = 0

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        for makanan, harga in menu.items():
            pilih = st.checkbox(f"{makanan} - Rp{harga:,}", key=makanan)
            if pilih:
                porsi = st.number_input(f"Jumlah porsi {makanan}", min_value=1, step=1, key=f"porsi_{makanan}")
                subtotal = harga * porsi
                pesanan[makanan] = subtotal
                totalHarga += subtotal

    st.session_state.data["food"] = pesanan
    st.session_state.data["price"] = totalHarga

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        st.button("Selesai ✅", on_click=double_next_page)
    with col3:
        st.button("➡️ Choose Beverage", on_click=next_page)

# HALAMAN 3: Pilih Minuman
elif st.session_state.page == 3:
    st.markdown("<h3 style='text-align: center;'>I'm Feeling Thirsty🥤</h3>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align: center;'>Choose Your Favorite Beverage</h5>", unsafe_allow_html=True)

    menu = {
        "Es Gobak Sodor": 9000,
        "Es Tok Aba": 7000,
        "Air Mineral": 4000,
        "Lemon Tea": 5000,
        "Milo": 8000,
        "Es Jeruk": 5000,
        "Es Teh": 4000,
        "Teh Tarik": 6000,
        "Thai Tea": 7000,
        "Matcha Latte": 8000,
        "Kopi Hitam": 7000,
        "Kopi Susu": 8000,
    }

    pesanan = {}
    totalHarga = 0

    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        for minuman, harga in menu.items():
            pilih = st.checkbox(f"{minuman} - Rp{harga:,}", key=minuman)
            if pilih:
                porsi = st.number_input(f"Jumlah porsi {minuman}", min_value=1, step=1, key=f"porsi_{minuman}")
                subtotal = harga * porsi
                pesanan[minuman] = subtotal
                totalHarga += subtotal

    st.session_state.data["drink"] = pesanan
    st.session_state.data["price"] += totalHarga

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        st.button("⬅️ Sebelumnya", on_click=prev_page)
    with col3:
        st.button("Selesai ✅", on_click=next_page)

# HALAMAN 4: Total Belanja
elif st.session_state.page == 4:

    name = st.session_state.data.get("name", "")
    food = st.session_state.data.get("food", {})
    drink = st.session_state.data.get("drink", {})
    total = st.session_state.data.get("price", 0)

    st.markdown("<h3 style='text-align: center;'>🧾 Total Belanja Anda</h3>", unsafe_allow_html=True)
    st.markdown(f"**Nama Pelanggan:** {st.session_state.data['name']}")

    
    st.markdown("### 🍽️ Makanan:")
    for item, subtotal in st.session_state.data["food"].items():
        st.write(f"- {item}: Rp{subtotal:,}")

    st.markdown("### 🥤 Minuman:")
    for item, subtotal in st.session_state.data["drink"].items():
        st.write(f"- {item}: Rp{subtotal:,}")

    st.markdown("---")
    st.markdown(f"## 💰 Total Harga: Rp{st.session_state.data['price']:,}")

    insert_order(name, food, drink)

    if st.button("🔄 Mulai Ulang"):
        st.session_state.page = 1
        st.session_state.data = {
            "name": "",
            "food": {},
            "drink": {},
            "price": 0
        }
        st.rerun()
