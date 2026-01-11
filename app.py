import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
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
riwayat = ctrl.Antecedent(np.arange(0, 11, 1), 'riwayat')
cicilan = ctrl.Antecedent(np.arange(0, 16, 1), 'cicilan')
dbr = ctrl.Antecedent(np.arange(0, 101, 1), 'dbr')

kelayakan = ctrl.Consequent(np.arange(0, 101, 1), 'kelayakan')

# =========================
# 2. MEMBERSHIP FUNCTION
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

riwayat['buruk'] = fuzz.trimf(riwayat.universe, [0, 0, 4])
riwayat['sedang'] = fuzz.trimf(riwayat.universe, [3, 5, 7])
riwayat['baik'] = fuzz.trimf(riwayat.universe, [6, 10, 10])

cicilan['baik'] = fuzz.trimf(cicilan.universe, [0, 1, 2])
cicilan['sedang'] = fuzz.trimf(cicilan.universe, [2, 3, 4])
cicilan['buruk'] = fuzz.trimf(cicilan.universe, [4, 5, 6])

# DBR (semakin kecil semakin baik)
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

    # Faktor dominan
    ctrl.Rule(dbr['tinggi'], kelayakan['tidak_layak']),
    ctrl.Rule(riwayat['buruk'], kelayakan['tidak_layak']),

    # Kondisi ideal
    ctrl.Rule(
        status['tinggi'] & lama['tinggi'] & gaji['tinggi'] & riwayat['baik'] & dbr['rendah'],
        kelayakan['layak']
    ),

    # Kondisi menengah
    ctrl.Rule(
        dbr['sedang'] & gaji['sedang'],
        kelayakan['dipertimbangkan']
    ),

    # Penyeimbang
    ctrl.Rule(
        dbr['rendah'] & riwayat['sedang'],
        kelayakan['dipertimbangkan']
    )
]
# Sistem kontrol fuzzy

kelayakan_ctrl = ctrl.ControlSystem(rules)
kelayakan_sim = ctrl.ControlSystemSimulation(kelayakan_ctrl)

# =========================
# 4. INPUT USER
# =========================
status_val = st.selectbox("Status Kepegawaian", ["Part-time", "Kontrak", "Tetap"])
lama_val = st.slider("Lama Bekerja (Tahun)", 1, 10, 3)
gaji_val = st.slider("Gaji per Bulan (juta rupiah)", 3, 20, 5)
cicilan_val = st.slider("Total Cicilan Saat Ini (juta rupiah)", 0, 15, 1)
riwayat_val = st.selectbox("Riwayat Kredit", ["2 Cicilan", "1 Cicilan", "Tidak Ada"])

status_map = {"Part-time": 2, "Kontrak": 5, "Tetap": 8}
riwayat_map = {"2 Cicilan": 2, "1 Cicilan": 5, "Tidak Ada": 8}

# =========================
# 5. HITUNG DBR OTOMATIS
# =========================
dbr_value = (cicilan_val / gaji_val) * 100
st.info(f"📌 DBR Saat Ini: {dbr_value:.2f}%")

# =========================
# 6. PROSES ANALISIS
# =========================
if st.button("Proses Kredit"):
    kelayakan_sim.input['status'] = status_map[status_val]
    kelayakan_sim.input['lama'] = lama_val
    kelayakan_sim.input['gaji'] = gaji_val
    kelayakan_sim.input['riwayat'] = riwayat_map[riwayat_val]
    kelayakan_sim.input['dbr'] = dbr_value

    kelayakan_sim.compute()
    hasil = kelayakan_sim.output['kelayakan']

    # =========================
    # 7. LOGIKA CICILAN MAKSIMAL
    # =========================
    if dbr_value < 30:
        max_cicilan = 0.50 * gaji_val
        kategori = "DBR Rendah (<30%)"
    elif dbr_value <= 50:
        max_cicilan = 0.40 * gaji_val
        kategori = "DBR Sedang (30–50%)"
    else:
        max_cicilan = 0.30 * gaji_val
        kategori = "DBR Tinggi (>50%)"

    # =========================
    # 8. OUTPUT
    # =========================
    st.subheader("📊 Hasil Keputusan Kredit")
    st.write(f"**Kategori DBR:** {kategori}")
    st.write(f"**Nilai Kelayakan:** {hasil:.2f}")
    st.write(
        f"**Maksimal Cicilan yang Diberikan:** "
        f"Rp {max_cicilan * 1_000_000:,.0f} / bulan"
    )

    if hasil >= 60:
        st.success("✅ Kredit Layak Disetujui")
    elif hasil >= 40:
        st.warning("⚠️ Kredit Dipertimbangkan")
    else:
        st.error("❌ Kredit Tidak Layak")

