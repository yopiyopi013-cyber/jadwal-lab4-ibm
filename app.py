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
DB_FILE = "booking_lab4_ibm_v3.db"

# Struktur jam pelajaran sesuai format gambar kedua
JADWAL_SLOT = [
    {"jam_ke": "1", "waktu": "07.00-07.40", "is_istirahat": False},
    {"jam_ke": "2", "waktu": "07.40-08.20", "is_istirahat": False},
    {"jam_ke": "3", "waktu": "08.20-09.00", "is_istirahat": False},
    {"jam_ke": "4", "waktu": "09.00-09.40", "is_istirahat": False},
    {"jam_ke": "ISTIRAHAT", "waktu": "", "is_istirahat": True},
    {"jam_ke": "5", "waktu": "10.10-10.50", "is_istirahat": False},
    {"jam_ke": "6", "waktu": "10.50-11.30", "is_istirahat": False},
    {"jam_ke": "7", "waktu": "11.30-12.10", "is_istirahat": False},
    {"jam_ke": "ISTIRAHAT", "waktu": "", "is_istirahat": True},
    {"jam_ke": "8", "waktu": "13.40-14.20", "is_istirahat": False},
    {"jam_ke": "9", "waktu": "14.20-15.00", "is_istirahat": False},
]

JAM_AKTIF_LIST = [f"Jam {s['jam_ke']} ({s['waktu']})" for s in JADWAL_SLOT if not s["is_istirahat"]]

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
        CREATE TABLE IF NOT EXISTS bookings_v3 (
            tanggal TEXT,
            jam_ke TEXT,
            kelas TEXT,
            pelajaran TEXT,
            guru TEXT,
            materi TEXT,
            PRIMARY KEY (tanggal, jam_ke)
        )
    ''')
    conn.commit()
    conn.close()

def get_all_bookings():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT tanggal, jam_ke, kelas, pelajaran, guru, materi FROM bookings_v3")
    rows = c.fetchall()
    conn.close()
    data = {}
    for r in rows:
        data[(r[0], r[1])] = {
            "kelas": r[2],
            "pelajaran": r[3],
            "guru": r[4],
            "materi": r[5]
        }
    return data

def save_booking(tanggal_iso, jam_ke, kelas, pelajaran, guru, materi):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO bookings_v3 (tanggal, jam_ke, kelas, pelajaran, guru, materi)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(tanggal, jam_ke) DO UPDATE SET
            kelas=excluded.kelas,
            pelajaran=excluded.pelajaran,
            guru=excluded.guru,
            materi=excluded.materi
    ''', (tanggal_iso, str(jam_ke), kelas.strip(), pelajaran.strip(), guru.strip(), materi.strip()))
    conn.commit()
    conn.close()

def delete_booking(tanggal_iso, jam_ke):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM bookings_v3 WHERE tanggal = ? AND jam_ke = ?", (tanggal_iso, str(jam_ke)))
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
# SIDEBAR: PILIH BULAN, TANGGAL & LOGIN ADMIN
# ==========================================
with st.sidebar:
    st.title("🏫 SMA Putra IBM")
    st.caption("Lab Komputer 4")
    st.divider()

    daftar_bulan = df_calendar["bulan_tahun"].unique().tolist()
    selected_bulan = st.selectbox("📅 Pilih Bulan & Tahun:", daftar_bulan, index=0)

    df_bulan = df_calendar[df_calendar["bulan_tahun"] == selected_bulan].copy()
    pilihan_tanggal_all = dict(zip(df_bulan["tanggal_label"], df_bulan["tanggal_iso"]))

    selected_tgl_label = st.selectbox(
        "🗓️ Pilih Tanggal / Hari:",
        list(pilihan_tanggal_all.keys()),
        index=0
    )
    selected_tgl_iso = pilihan_tanggal_all[selected_tgl_label]
    is_selected_jumat = bool(df_bulan[df_bulan["tanggal_iso"] == selected_tgl_iso]["is_jumat"].iloc[0])

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
                st.error("Password salah!")
    else:
        st.success("✅ Mode Admin Aktif")
        st.caption("Admin dapat mengedit dan menghapus booking.")
        if st.button("Keluar (Logout Admin)", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()

    st.divider()
    st.info(
        "**Aturan:**\n"
        "- **Jumat:** Libur.\n"
        "- **Minggu:** Masuk normal.\n"
        "- **Guru:** Bisa mengisi & mengedit data, tidak bisa menghapus.\n"
        "- **Admin:** Bisa mengedit & menghapus data."
    )

# ==========================================
# HEADER UTAMA
# ==========================================
st.title("💻 Jadwal Booking Laboratorium Komputer 4")
st.markdown("#### SMA Putra IBM — Periode Desember 2026 s.d. Desember 2027")

if st.session_state.is_admin:
    st.warning("🛡️ **MODE ADMIN AKTIF:** Anda bisa mengedit maupun menghapus booking pada jadwal.")

# ==========================================
# TABEL UTAMA (FORMAT SESUAI GAMBAR KE-2)
# ==========================================
bookings_data = get_all_bookings()

rows_for_table = []
for slot in JADWAL_SLOT:
    if slot["is_istirahat"]:
        rows_for_table.append({
            "TANGGAL/HARI": selected_tgl_label,
            "JAM - KE": "ISTIRAHAT",
            "WAKTU": "",
            "KELAS": "",
            "PELAJARAN": "",
            "GURU": "",
            "MATERI": ""
        })
    else:
        jam_str = slot["jam_ke"]
        item = bookings_data.get((selected_tgl_iso, jam_str))

        if is_selected_jumat:
            rows_for_table.append({
                "TANGGAL/HARI": selected_tgl_label,
                "JAM - KE": jam_str,
                "WAKTU": slot["waktu"],
                "KELAS": "LIBUR",
                "PELAJARAN": "LIBUR",
                "GURU": "LIBUR",
                "MATERI": "LIBUR"
            })
        elif item:
            rows_for_table.append({
                "TANGGAL/HARI": selected_tgl_label,
                "JAM - KE": jam_str,
                "WAKTU": slot["waktu"],
                "KELAS": item["kelas"],
                "PELAJARAN": item["pelajaran"],
                "GURU": item["guru"],
                "MATERI": item["materi"]
            })
        else:
            # Kolom dibiarkan kosong jika belum dibooking
            rows_for_table.append({
                "TANGGAL/HARI": selected_tgl_label,
                "JAM - KE": jam_str,
                "WAKTU": slot["waktu"],
                "KELAS": "",
                "PELAJARAN": "",
                "GURU": "",
                "MATERI": ""
            })

df_table = pd.DataFrame(rows_for_table)

def style_jadwal_row(row):
    if row["JAM - KE"] == "ISTIRAHAT":
        return ["background-color: #f4b400; color: #1f1f1f; font-weight: bold; text-align: center;"] * len(row)
    if is_selected_jumat:
        return ["background-color: #ffe5e5; color: #990000; font-weight: bold;"] * len(row)

    styles = []
    for col in row.index:
        if col in ["TANGGAL/HARI", "JAM - KE", "WAKTU"]:
            styles.append("background-color: #fff3cd; color: #222222; font-weight: 500; text-align: center;" if col != "TANGGAL/HARI" else "background-color: #fff3cd; color: #222222; font-weight: 600;")
        else:
            if str(row[col]).strip() != "":
                styles.append("background-color: #d1e7dd; color: #0f5132; font-weight: 500;")
            else:
                styles.append("background-color: #ffffff; color: #111111;")
    return styles

st.markdown(f"### 📋 Jadwal: **{selected_tgl_label}**")
st.dataframe(
    df_table.style.apply(style_jadwal_row, axis=1),
    use_container_width=True,
    height=460,
    hide_index=True
)

st.divider()

# ==========================================
# FORM INPUT / EDIT / HAPUS BOOKING
# ==========================================
st.markdown("### ✍️ Isi / Edit Booking Jadwal")

if is_selected_jumat:
    st.error("📅 Hari **Jumat** libur. Silakan pilih tanggal lain di panel sebelah kiri.")
else:
    pilih_jam_label = st.selectbox("Pilih Jam - Ke & Waktu:", JAM_AKTIF_LIST)
    # Ekstrak angka jam ke- (misal "Jam 1 (07.00-07.40)" -> "1")
    jam_ke_terpilih = pilih_jam_label.split(" ")[1]

    existing_item = bookings_data.get((selected_tgl_iso, jam_ke_terpilih))

    val_kelas = existing_item["kelas"] if existing_item else ""
    val_pelajaran = existing_item["pelajaran"] if existing_item else ""
    val_guru = existing_item["guru"] if existing_item else ""
    val_materi = existing_item["materi"] if existing_item else ""

    if existing_item:
        st.info(f"ℹ️ Jam ke-**{jam_ke_terpilih}** pada **{selected_tgl_label}** sudah terisi. Anda dapat mengedit datanya di bawah.")

    with st.form("form_booking_v3", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            in_kelas = st.text_input("KELAS", value=val_kelas, placeholder="Contoh: X IPA 1")
            in_guru = st.text_input("GURU", value=val_guru, placeholder="Contoh: Budi Santoso, S.Pd")
        with col2:
            in_pelajaran = st.text_input("PELAJARAN", value=val_pelajaran, placeholder="Contoh: Informatika")
            in_materi = st.text_input("MATERI", value=val_materi, placeholder="Contoh: Pengenalan Perangkat Keras")

        simpan_btn = st.form_submit_button("💾 Simpan Booking", type="primary", use_container_width=True)
        if simpan_btn:
            if not in_kelas.strip() or not in_pelajaran.strip() or not in_guru.strip() or not in_materi.strip():
                st.error("⚠️ Harap isi semua kolom: KELAS, PELAJARAN, GURU, dan MATERI.")
            else:
                save_booking(selected_tgl_iso, jam_ke_terpilih, in_kelas, in_pelajaran, in_guru, in_materi)
                st.success(f"✅ Booking tersimpan untuk {selected_tgl_label} — Jam ke-{jam_ke_terpilih}!")
                st.rerun()

    if st.session_state.is_admin and existing_item:
        st.markdown("#### 🗑️ Hapus Booking (Khusus Admin)")
        if st.button(f"Hapus Jadwal Jam ke-{jam_ke_terpilih} ({selected_tgl_label})", type="secondary"):
            delete_booking(selected_tgl_iso, jam_ke_terpilih)
            st.warning("🗑️ Booking telah dihapus oleh Admin.")
            st.rerun()
