import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta, datetime

# ==========================================
# KONFIGURASI HALAMAN & PASSWORD ADMIN
# ==========================================
st.set_page_config(
    page_title="Booking Lab Komputer 4 - SMA Putra IBM",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

ADMIN_PASSWORD = "adminibm2026"  # <-- Ganti password admin di sini
DB_FILE = "booking_lab4_ibm_v5.db"

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

st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
    }
    .slot-card {
        border: 1px solid #444;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 10px;
        background-color: #1e2229;
    }
    .slot-card-booked {
        border: 1px solid #2e7d32;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 10px;
        background-color: #16291a;
    }
    .slot-card-rest {
        border: 1px solid #b28704;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 10px;
        background-color: #332700;
        text-align: center;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# FUNGSI DATABASE (SQLITE)
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings_v5 (
            tanggal TEXT,
            bulan_tahun TEXT,
            jam_ke TEXT,
            kelas TEXT,
            pelajaran TEXT,
            guru TEXT,
            materi TEXT,
            diperbarui_pada TEXT,
            PRIMARY KEY (tanggal, jam_ke)
        )
    ''')
    conn.commit()
    conn.close()

def get_all_bookings():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT tanggal, bulan_tahun, jam_ke, kelas, pelajaran, guru, materi, diperbarui_pada
        FROM bookings_v5
        ORDER BY tanggal ASC, CAST(jam_ke AS INTEGER) ASC
    """)
    rows = c.fetchall()
    conn.close()
    data = {}
    for r in rows:
        data[(r[0], r[2])] = {
            "tanggal": r[0],
            "bulan_tahun": r[1],
            "jam_ke": r[2],
            "kelas": r[3],
            "pelajaran": r[4],
            "guru": r[5],
            "materi": r[6],
            "diperbarui_pada": r[7]
        }
    return data

def save_booking(tanggal_iso, bulan_tahun, jam_ke, kelas, pelajaran, guru, materi):
    waktu_simpan = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO bookings_v5 (tanggal, bulan_tahun, jam_ke, kelas, pelajaran, guru, materi, diperbarui_pada)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(tanggal, jam_ke) DO UPDATE SET
            bulan_tahun=excluded.bulan_tahun,
            kelas=excluded.kelas,
            pelajaran=excluded.pelajaran,
            guru=excluded.guru,
            materi=excluded.materi,
            diperbarui_pada=excluded.diperbarui_pada
    ''', (tanggal_iso, bulan_tahun, str(jam_ke), kelas.strip(), pelajaran.strip(), guru.strip(), materi.strip(), waktu_simpan))
    conn.commit()
    conn.close()

def delete_booking(tanggal_iso, jam_ke):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM bookings_v5 WHERE tanggal = ? AND jam_ke = ?", (tanggal_iso, str(jam_ke)))
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

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ==========================================
# SIDEBAR (OPSIONAL UNTUK LOGIN ADMIN)
# ==========================================
with st.sidebar:
    st.title("🏫 SMA Putra IBM")
    st.caption("Lab Komputer 4")
    st.divider()
    st.subheader("🔐 Login Admin")
    if not st.session_state.is_admin:
        pwd_side = st.text_input("Password Admin:", type="password", key="pwd_side", placeholder="Password...")
        if st.button("Masuk Admin", key="btn_side_login", use_container_width=True):
            if pwd_side == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Password salah!")
    else:
        st.success("✅ Mode Admin Aktif")
        if st.button("Logout Admin", key="btn_side_logout", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()

# ==========================================
# HEADER UTAMA
# ==========================================
st.title("💻 Booking Lab Komputer 4")
st.caption("SMA Putra IBM • Desember 2026 – Desember 2027 • Jumat Libur • Minggu Masuk")

with st.expander("🔐 Akses Admin (Edit & Hapus Jadwal)", expanded=False):
    if not st.session_state.is_admin:
        pwd_main = st.text_input("Masukkan Password Admin:", type="password", key="pwd_main", placeholder="Khusus Admin Lab...")
        if st.button("Masuk sebagai Admin", key="btn_main_login"):
            if pwd_main == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Password Admin salah!")
    else:
        st.success("✅ Mode Admin Aktif — Anda bisa mengedit dan menghapus jadwal.")
        if st.button("Keluar dari Mode Admin", key="btn_main_logout"):
            st.session_state.is_admin = False
            st.rerun()

# ==========================================
# PILIH BULAN & TANGGAL
# ==========================================
col_bln, col_tgl, col_mode = st.columns([1.2, 1.5, 1.3])

daftar_bulan = df_calendar["bulan_tahun"].unique().tolist()
with col_bln:
    selected_bulan = st.selectbox("📅 Bulan & Tahun:", daftar_bulan, index=0)

df_bulan = df_calendar[df_calendar["bulan_tahun"] == selected_bulan].copy()
pilihan_tanggal_all = dict(zip(df_bulan["tanggal_label"], df_bulan["tanggal_iso"]))
map_iso_to_label = dict(zip(df_bulan["tanggal_iso"], df_bulan["tanggal_label"]))

with col_tgl:
    selected_tgl_label = st.selectbox("🗓️ Tanggal / Hari:", list(pilihan_tanggal_all.keys()), index=0)
    selected_tgl_iso = pilihan_tanggal_all[selected_tgl_label]
    is_selected_jumat = bool(df_bulan[df_bulan["tanggal_iso"] == selected_tgl_iso]["is_jumat"].iloc[0])

with col_mode:
    tampilan_mode = st.radio(
        "📱 Tampilan Jadwal:",
        ["Otomatis / Kartu (Cocok di HP)", "Tabel Penuh (Cocok di Laptop)"],
        horizontal=False
    )

bookings_data = get_all_bookings()

st.divider()

# ==========================================
# TAMPILAN JADWAL HARIAN
# ==========================================
st.subheader(f"📋 Jadwal: {selected_tgl_label}")

if is_selected_jumat:
    st.error("📅 Hari **Jumat** libur. Silakan pilih tanggal lain.")
elif tampilan_mode.startswith("Otomatis"):
    for slot in JADWAL_SLOT:
        if slot["is_istirahat"]:
            st.markdown('<div class="slot-card-rest">☕ ISTIRAHAT</div>', unsafe_allow_html=True)
        else:
            jam_str = slot["jam_ke"]
            waktu_str = slot["waktu"]
            item = bookings_data.get((selected_tgl_iso, jam_str))
            if item:
                st.markdown(f"""
                <div class="slot-card-booked">
                    <strong>Jam ke-{jam_str}</strong> ({waktu_str}) — <span style="color:#81c784;">Terisi</span><br>
                    <b>Kelas:</b> {item['kelas']} | <b>Pelajaran:</b> {item['pelajaran']}<br>
                    <b>Guru:</b> {item['guru']} | <b>Materi:</b> {item['materi']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="slot-card">
                    <strong>Jam ke-{jam_str}</strong> ({waktu_str}) — <span style="color:#aaa;">Kosong</span>
                </div>
                """, unsafe_allow_html=True)
else:
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
            rows_for_table.append({
                "TANGGAL/HARI": selected_tgl_label,
                "JAM - KE": jam_str,
                "WAKTU": slot["waktu"],
                "KELAS": item["kelas"] if item else "",
                "PELAJARAN": item["pelajaran"] if item else "",
                "GURU": item["guru"] if item else "",
                "MATERI": item["materi"] if item else ""
            })
    df_table = pd.DataFrame(rows_for_table)
    st.dataframe(df_table, use_container_width=True, height=450, hide_index=True)

st.divider()

# ==========================================
# FORM INPUT / EDIT / HAPUS BOOKING
# ==========================================
st.subheader("✍️ Isi / Edit Booking Jadwal")

if not is_selected_jumat:
    pilih_jam_label = st.selectbox("Pilih Jam - Ke & Waktu:", JAM_AKTIF_LIST)
    jam_ke_terpilih = pilih_jam_label.split(" ")[1]
    existing_item = bookings_data.get((selected_tgl_iso, jam_ke_terpilih))

    val_kelas = existing_item["kelas"] if existing_item else ""
    val_pelajaran = existing_item["pelajaran"] if existing_item else ""
    val_guru = existing_item["guru"] if existing_item else ""
    val_materi = existing_item["materi"] if existing_item else ""

    if existing_item:
        st.info(f"ℹ️ Jam ke-**{jam_ke_terpilih}** pada **{selected_tgl_label}** sudah terisi. Silakan ubah jika ingin mengedit.")

    with st.form("form_booking_v5", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            in_kelas = st.text_input("KELAS", value=val_kelas, placeholder="Contoh: X IPA 1")
            in_guru = st.text_input("GURU", value=val_guru, placeholder="Contoh: Budi Santoso, S.Pd")
        with c2:
            in_pelajaran = st.text_input("PELAJARAN", value=val_pelajaran, placeholder="Contoh: Informatika")
            in_materi = st.text_input("MATERI", value=val_materi, placeholder="Contoh: Pengenalan Perangkat Keras")

        simpan_btn = st.form_submit_button("💾 Simpan Booking", type="primary", use_container_width=True)
        if simpan_btn:
            if not in_kelas.strip() or not in_pelajaran.strip() or not in_guru.strip() or not in_materi.strip():
                st.error("⚠️ Harap isi semua kolom: KELAS, PELAJARAN, GURU, dan MATERI.")
            else:
                save_booking(selected_tgl_iso, selected_bulan, jam_ke_terpilih, in_kelas, in_pelajaran, in_guru, in_materi)
                st.success(f"✅ Booking tersimpan untuk {selected_tgl_label} — Jam ke-{jam_ke_terpilih}!")
                st.rerun()

    if st.session_state.is_admin and existing_item:
        if st.button(f"🗑️ Hapus Booking Jam ke-{jam_ke_terpilih}", type="secondary", use_container_width=True):
            delete_booking(selected_tgl_iso, jam_ke_terpilih)
            st.warning("Booking telah dihapus oleh Admin.")
            st.rerun()

st.divider()

# ==========================================
# REKAP SEMUA BOOKINGAN TERSIMPAN DALAM 1 BULAN
# ==========================================
st.subheader(f"🗂️ Semua Bookingan Tersimpan — {selected_bulan}")
st.caption("Menampilkan seluruh jadwal yang tersimpan di database untuk bulan terpilih agar mudah dilihat siapa saja.")

bulan_bookings = [
    {
        "TANGGAL / HARI": map_iso_to_label.get(v["tanggal"], v["tanggal"]),
        "JAM - KE": v["jam_ke"],
        "KELAS": v["kelas"],
        "PELAJARAN": v["pelajaran"],
        "GURU": v["guru"],
        "MATERI": v["materi"],
        "TERSIMPAN SEJAK": v["diperbarui_pada"]
    }
    for (_, _), v in bookings_data.items()
    if v["bulan_tahun"] == selected_bulan
]

if bulan_bookings:
    df_rekap_bulan = pd.DataFrame(bulan_bookings)
    st.dataframe(df_rekap_bulan, use_container_width=True, hide_index=True)
else:
    st.info(f"Belum ada bookingan yang tersimpan pada bulan **{selected_bulan}**.")
