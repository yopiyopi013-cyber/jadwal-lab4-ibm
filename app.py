import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta

# ==========================================
# KONFIGURASI HALAMAN & PASSWORD ADMIN
# ==========================================
st.set_page_config(
    page_title="Booking Lab Komputer 4 - SMA Putra IBM",
    page_icon="💻",
    layout="wide"
)

ADMIN_PASSWORD = "adminibm2026"  # <-- Ganti password admin di sini
DB_FILE = "booking_lab4_ibm_v2.db"

# Definisi Slot Jam Pelajaran beserta waktunya
SLOT_COLS = [
    "Jam 1 (07.00-07.40)",
    "Jam 2 (07.40-08.20)",
    "Jam 3 (08.20-09.00)",
    "Jam 4 (09.00-09.40)",
    "Istirahat 1 (09.40-10.10)",
    "Jam 5 (10.10-10.50)",
    "Jam 6 (10.50-11.30)",
    "Jam 7 (11.30-12.10)",
    "Istirahat 2 (12.10-13.40)",
    "Jam 8 (13.40-14.20)",
    "Jam 9 (14.20-15.00)"
]

JAM_AKTIF = [s for s in SLOT_COLS if "Istirahat" not in s]

NAMA_HARI = {
    0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis",
    4: "Jumat", 5: "Sabtu", 6: "Minggu"
}

NAMA_BULAN = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

# ==========================================
# FUNGSI DATABASE (SQLITE)
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            tanggal TEXT,
            slot TEXT,
            kelas TEXT,
            pelajaran TEXT,
            guru TEXT,
            materi TEXT,
            PRIMARY KEY (tanggal, slot)
        )
    ''')
    conn.commit()
    conn.close()

def get_all_bookings():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT tanggal, slot, kelas, pelajaran, guru, materi FROM bookings")
    rows = c.fetchall()
    conn.close()
    # Format dict: {(tanggal_iso, slot): {"kelas": ..., "pelajaran": ..., "guru": ..., "materi": ...}}
    data = {}
    for r in rows:
        data[(r[0], r[1])] = {
            "kelas": r[2],
            "pelajaran": r[3],
            "guru": r[4],
            "materi": r[5]
        }
    return data

def save_booking(tanggal_iso, slot, kelas, pelajaran, guru, materi):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO bookings (tanggal, slot, kelas, pelajaran, guru, materi)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(tanggal, slot) DO UPDATE SET
            kelas=excluded.kelas,
            pelajaran=excluded.pelajaran,
            guru=excluded.guru,
            materi=excluded.materi
    ''', (tanggal_iso, slot, kelas.strip(), pelajaran.strip(), guru.strip(), materi.strip()))
    conn.commit()
    conn.close()

def delete_booking(tanggal_iso, slot):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM bookings WHERE tanggal = ? AND slot = ?", (tanggal_iso, slot))
    conn.commit()
    conn.close()

init_db()

# ==========================================
# GENERATE KALENDER (DES 2026 - DES 2027)
# ==========================================
@st.cache_data
def generate_calendar_dates():
    start_date = date(2026, 12, 1)
    end_date = date(2027, 12, 31)
    delta = end_date - start_date
    
    dates_list = []
    for i in range(delta.days + 1):
        d = start_date + timedelta(days=i)
        hari_str = NAMA_HARI[d.weekday()]
        is_jumat = (d.weekday() == 4)  # Jumat libur, Minggu tetap masuk
        bulan_tahun = f"{NAMA_BULAN[d.month]} {d.year}"
        tanggal_label = f"{hari_str}, {d.day:02d} {NAMA_BULAN[d.month]} {d.year}"
        
        dates_list.append({
            "tanggal_iso": d.isoformat(),
            "tanggal_label": tanggal_label,
            "bulan_tahun": bulan_tahun,
            "is_jumat": is_jumat
        })
    return pd.DataFrame(dates_list)

df_calendar = generate_calendar_dates()

# ==========================================
# SIDEBAR: PILIH BULAN & LOGIN ADMIN
# ==========================================
with st.sidebar:
    st.title("🏫 SMA Putra IBM")
    st.caption("Sistem Booking Lab Komputer 4")
    st.divider()
    
    daftar_bulan = df_calendar["bulan_tahun"].unique().tolist()
    selected_bulan = st.selectbox("📅 Pilih Bulan & Tahun:", daftar_bulan, index=0)
    
    st.divider()
    st.subheader("🔐 Login Admin")
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

    if not st.session_state.is_admin:
        pwd_input = st.text_input("Password Admin:", type="password", placeholder="Masukkan password...")
        if st.button("Masuk sebagai Admin", use_container_width=True):
            if pwd_input == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Password Admin salah!")
    else:
        st.success("✅ Mode Admin Aktif")
        st.caption("Admin dapat mengedit dan menghapus jadwal booking yang sudah ada.")
        if st.button("Keluar (Logout Admin)", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()

    st.divider()
    st.info(
        "**Aturan Penggunaan:**\n"
        "- **Jumat:** Libur (Terkunci otomatis).\n"
        "- **Minggu:** Masuk normal.\n"
        "- **Guru:** Dapat mengisi slot kosong & mengedit isian, namun **tidak bisa menghapus** jadwal yang sudah tersimpan.\n"
        "- **Admin:** Dapat mengedit & menghapus jadwal."
    )

# ==========================================
# HEADER UTAMA
# ==========================================
st.title("💻 Jadwal Booking Laboratorium Komputer 4")
st.markdown("#### SMA Putra IBM — Periode Desember 2026 s.d. Desember 2027")

if st.session_state.is_admin:
    st.warning("🛡️ **MODE ADMIN AKTIF:** Anda memiliki akses untuk mengubah maupun menghapus data booking.")

# ==========================================
# TABEL 1: MATRIKS JADWAL BULANAN
# ==========================================
bookings_data = get_all_bookings()
df_bulan = df_calendar[df_calendar["bulan_tahun"] == selected_bulan].copy()

matrix_rows = []
detail_rows = []

for _, row in df_bulan.iterrows():
    t_iso = row["tanggal_iso"]
    t_label = row["tanggal_label"]
    row_dict = {"Tanggal / Hari": t_label}
    
    for slot in SLOT_COLS:
        if row["is_jumat"]:
            row_dict[slot] = "LIBUR"
        elif "Istirahat" in slot:
            row_dict[slot] = "ISTIRAHAT"
        else:
            item = bookings_data.get((t_iso, slot))
            if item:
                # Format tampilan ringkas di matriks utama
                row_dict[slot] = f"{item['kelas']} | {item['pelajaran']} | {item['guru']} ({item['materi']})"
                # Simpan juga untuk tabel rincian di bawah
                detail_rows.append({
                    "Tanggal / Hari": t_label,
                    "Jam Ke-": slot,
                    "Kelas": item["kelas"],
                    "Pelajaran": item["pelajaran"],
                    "Guru": item["guru"],
                    "Materi": item["materi"]
                })
            else:
                # Kolom harus kosong jika belum dibooking
                row_dict[slot] = ""
                
    matrix_rows.append(row_dict)

df_matrix = pd.DataFrame(matrix_rows)

def style_matrix(val):
    if val == "LIBUR":
        return "background-color: #ffe5e5; color: #b30000; font-weight: bold; text-align: center;"
    elif val == "ISTIRAHAT":
        return "background-color: #f1f3f6; color: #555555; font-style: italic; text-align: center;"
    elif val != "":
        return "background-color: #d1e7dd; color: #0f5132; font-weight: 500;"
    return ""

st.markdown(f"### 📅 Tabel Jadwal Bulan {selected_bulan}")
st.dataframe(
    df_matrix.style.map(style_matrix, subset=SLOT_COLS),
    use_container_width=True,
    height=460,
    hide_index=True
)

st.divider()

# ==========================================
# FORM INPUT / EDIT / HAPUS BOOKING
# ==========================================
st.markdown("### ✍️ Form Booking / Edit Jadwal")

df_hari_masuk = df_bulan[~df_bulan["is_jumat"]]
pilihan_tanggal_map = dict(zip(df_hari_masuk["tanggal_label"], df_hari_masuk["tanggal_iso"]))

col_sel1, col_sel2 = st.columns(2)
with col_sel1:
    pilih_tgl_label = st.selectbox("1. Pilih Tanggal / Hari:", list(pilihan_tanggal_map.keys()))
    pilih_tgl_iso = pilihan_tanggal_map[pilih_tgl_label]

with col_sel2:
    pilih_jam = st.selectbox("2. Pilih Jam Ke-:", JAM_AKTIF)

existing_item = bookings_data.get((pilih_tgl_iso, pilih_jam))

# Ambil nilai awal (kosong jika belum dibooking, atau data lama jika sedang diedit)
val_kelas = existing_item["kelas"] if existing_item else ""
val_pelajaran = existing_item["pelajaran"] if existing_item else ""
val_guru = existing_item["guru"] if existing_item else ""
val_materi = existing_item["materi"] if existing_item else ""

if existing_item:
    st.info(f"ℹ️ Slot **{pilih_tgl_label}** pada **{pilih_jam}** sudah terisi. Silakan ubah kolom di bawah jika ingin mengedit data.")

with st.form("form_booking_lab", clear_on_submit=False):
    c1, c2 = st.columns(2)
    with c1:
        in_kelas = st.text_input("Kelas:", value=val_kelas, placeholder="Contoh: XI IPA 2")
        in_guru = st.text_input("Nama Guru:", value=val_guru, placeholder="Contoh: Ahmad Fauzi, S.Kom")
    with c2:
        in_pelajaran = st.text_input("Mata Pelajaran:", value=val_pelajaran, placeholder="Contoh: Informatika / TIK")
        in_materi = st.text_input("Materi Praktikum:", value=val_materi, placeholder="Contoh: Pemrograman Dasar Python")

    submitted = st.form_submit_button("💾 Simpan / Update Booking", type="primary", use_container_width=True)
    if submitted:
        if not in_kelas.strip() or not in_pelajaran.strip() or not in_guru.strip() or not in_materi.strip():
            st.error("⚠️ Semua kolom (Kelas, Pelajaran, Guru, dan Materi) wajib diisi!")
        else:
            save_booking(pilih_tgl_iso, pilih_jam, in_kelas, in_pelajaran, in_guru, in_materi)
            st.success(f"✅ Jadwal berhasil disimpan untuk {pilih_tgl_label} — {pilih_jam}!")
            st.rerun()

# Tombol Hapus Khusus Admin
if st.session_state.is_admin and existing_item:
    st.markdown("#### 🗑️ Kontrol Penghapusan (Khusus Admin)")
    if st.button(f"Hapus Booking ({pilih_tgl_label} | {pilih_jam})", type="secondary"):
        delete_booking(pilih_tgl_iso, pilih_jam)
        st.warning("Booking telah berhasil dihapus oleh Admin.")
        st.rerun()

st.divider()

# ==========================================
# TABEL 2: RINCIAN DATA BOOKING BULAN TERPILIH
# ==========================================
st.markdown(f"### 📋 Rincian Terstruktur Booking Bulan {selected_bulan}")
if len(detail_rows) > 0:
    df_detail = pd.DataFrame(detail_rows)
    st.dataframe(df_detail, use_container_width=True, hide_index=True)
else:
    st.caption(f"Belum ada jadwal yang dibooking pada bulan {selected_bulan}. Semua slot jam aktif masih kosong.")