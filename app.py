import streamlit as st
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# =========================
# KONFIGURASI HALAMAN
# =========================
st.set_page_config(page_title="Sistem Pakar Kredit", layout="centered")
st.title("💳 Sistem Pakar Pemberian Kredit")
st.caption("Metode Fuzzy Mamdani + DBR Otomatis")

# =========================
# 1. DEFINISI VARIABEL FUZZY
# =========================
status = ctrl.Antecedent(np.arange(0, 11, 1), 'status')
lama = ctrl.Antecedent(np.arange(0, 11, 1), 'lama')
gaji = ctrl.Antecedent(np.arange(0, 21, 1), 'gaji')
jaminan = ctrl.Antecedent(np.arange(0, 11, 1), 'jaminan')
pinjaman = ctrl.Antecedent(np.arange(0, 81, 1), 'pinjaman')
dbr = ctrl.Antecedent(np.arange(0, 101, 1), 'dbr')

kelayakan = ctrl.Consequent(np.arange(0, 101, 1), 'kelayakan')

# =========================
# 2. FUNGSI KEANGGOTAAN
# =========================
status['rendah'] = fuzz.trimf(status.universe, [0, 0, 5])
status['sedang'] = fuzz.trimf(status.universe, [3, 5, 7])
status['tinggi'] = fuzz.trimf(status.universe, [5, 10, 10])

lama['rendah'] = fuzz.trimf(lama.universe, [0, 0, 4])
lama['sedang'] = fuzz.trimf(lama.universe, [3, 5, 7])
lama['tinggi'] = fuzz.trimf(lama.universe, [6, 10, 10])

gaji['rendah'] = fuzz.trimf(gaji.universe, [0, 3, 5])
gaji['sedang'] = fuzz.trimf(gaji.universe, [4, 7, 10])
gaji['tinggi'] = fuzz.trimf(gaji.universe, [9, 20, 20])

jaminan['buruk'] = fuzz.trimf(jaminan.universe, [0, 0, 4])
jaminan['sedang'] = fuzz.trimf(jaminan.universe, [3, 5, 7])
jaminan['baik'] = fuzz.trimf(jaminan.universe, [6, 10, 10])

# 🔹 PINJAMAN (juta)
pinjaman['rendah'] = fuzz.trimf(pinjaman.universe, [0, 20, 30])
pinjaman['sedang'] = fuzz.trimf(pinjaman.universe, [25, 40, 55])
pinjaman['tinggi'] = fuzz.trimf(pinjaman.universe, [50, 70, 80])

# 🔹 DBR
dbr['rendah'] = fuzz.trimf(dbr.universe, [0, 20, 30])
dbr['sedang'] = fuzz.trimf(dbr.universe, [30, 40, 50])
dbr['tinggi'] = fuzz.trimf(dbr.universe, [50, 70, 100])

kelayakan['tidak_layak'] = fuzz.trimf(kelayakan.universe, [0, 0, 50])
kelayakan['dipertimbangkan'] = fuzz.trimf(kelayakan.universe, [30, 50, 70])
kelayakan['layak'] = fuzz.trimf(kelayakan.universe, [60, 100, 100])

# =========================
# 3. RULE FUZZY
# =========================
rules = [
    ctrl.Rule(status['rendah'], kelayakan['tidak_layak']),
    ctrl.Rule(jaminan['buruk'], kelayakan['tidak_layak']),
    ctrl.Rule(lama['rendah'], kelayakan['tidak_layak']),
    ctrl.Rule(gaji['rendah'], kelayakan['tidak_layak']),
    ctrl.Rule(dbr['tinggi'], kelayakan['tidak_layak']),

    ctrl.Rule(
        gaji['tinggi'] & jaminan['baik'] & pinjaman['rendah'],
        kelayakan['layak']
    ),

    ctrl.Rule(
        status['sedang'] & gaji['sedang'] & jaminan['sedang'],
        kelayakan['dipertimbangkan']
    ),

    # ✅ RULE PENJAGA (WAJIB ADA)
    ctrl.Rule(
        status['rendah'] | status['sedang'],
        kelayakan['dipertimbangkan']
    )
]


kelayakan_ctrl = ctrl.ControlSystem(rules)
kelayakan_sim = ctrl.ControlSystemSimulation(kelayakan_ctrl)

# =========================
# 4. INPUT USER
# =========================
# Variabel Input
status_val = st.selectbox("Status Kepegawaian", ["Part-time", "Kontrak", "Tetap"])
lama_val = st.slider("Lama Bekerja (Tahun)", 1, 10, 3)
gaji_val = st.slider("Gaji per Bulan (juta)", 3, 20, 5)
jaminan_val = st.selectbox("Jenis Jaminan", ["Tidak Ada", "BPKB", "SHM"])

# Variabel Pinjaman (tambahan untuk perhitungan DBR)
pinjaman_val = st.slider("Pinjaman Diajukan (juta)", 10, 80, 20)
status_map = {"Part-time": 2, "Kontrak": 5, "Tetap": 8}
jaminan_map = {"Tidak Ada": 2, "BPKB": 5, "SHM": 10}

# =========================
# 5. HITUNG DBR OTOMATIS
# =========================
tenor = st.selectbox(
    "Tenor Pinjaman (bulan)",
    [12, 24, 36]
)
estimasi_cicilan = pinjaman_val / tenor
dbr_value = (estimasi_cicilan / gaji_val) * 100

st.info(f"📌 Estimasi Cicilan: {estimasi_cicilan:.2f} jt / bulan")
st.info(f"📌 DBR: {dbr_value:.2f}%")

# =========================
# 6. PROSES
# =========================
if st.button("Proses Kredit"):
    kelayakan_sim.input['status'] = status_map[status_val]
    kelayakan_sim.input['lama'] = lama_val
    kelayakan_sim.input['gaji'] = gaji_val
    kelayakan_sim.input['jaminan'] = jaminan_map[jaminan_val]
    kelayakan_sim.input['pinjaman'] = pinjaman_val
    kelayakan_sim.input['dbr'] = dbr_value

    kelayakan_sim.compute()
    hasil = kelayakan_sim.output['kelayakan']

    st.subheader("📊 Hasil Keputusan Kredit")
    st.write(f"**Nilai Kelayakan:** {hasil:.2f}")

    if hasil >= 60:
        st.success("✅ Kredit Layak Disetujui")
    elif hasil >= 40:
        st.warning("⚠️ Kredit Dipertimbangkan")
    else:
        st.error("❌ Kredit Tidak Layak")
