import os
import pandas as pd
import streamlit as st
import google.generativeai as genai

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Asisten Laporan Puskesmas AI", layout="wide")
st.title("🏥 Asisten Pembuat Laporan Puskesmas berbasis AI")

# --- MENGAMBIL GEMINI API KEY ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if not GEMINI_API_KEY:
    st.error("Gemini API Key belum dikonfigurasi di Secrets!")
    st.stop()

# Inisialisasi Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- TAMPILAN UTAMA APLIKASI ---
uploaded_file = st.file_uploader("Unggah Berkas Data Puskesmas (Excel/CSV)", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    st.success("Berkas berhasil dimuat! Data disimpan aman secara sementara di memori.")

    # Membaca data langsung dari memori
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.subheader("Pratinjau Data Unggahan:")
        st.dataframe(df.head())

        # Form Pembuatan Laporan
        st.subheader("📝 Buat Laporan Otomatis")
        jenis_laporan = st.selectbox(
            "Pilih Jenis Laporan Puskesmas:",
            ["Laporan Bulanan Stunting", "Laporan Kesehatan Ibu & Anak (KIA)", "Laporan Capaian Program", "Laporan Kustom"]
        )
        
        instruksi_tambahan = st.text_area("Instruksi atau Catatan Khusus (Opsional):", "")

        if st.button("Hasilkan Laporan dengan AI"):
            with st.spinner("Gemini AI sedang menganalisis data dan meracik laporan..."):
                data_summary = df.to_string()
                
                prompt = f"""
                Anda adalah asisten AI profesional di Puskesmas. Buatlah {jenis_laporan} berdasarkan data berikut ini:
                
                {data_summary}
                
                Instruksi Tambahan: {instruksi_tambahan}
                
                Format laporan harus rapi, baku, mencakup analisis angka/trend kunci, narasi capaian, serta rekomendasi tindak lanjut untuk tim Puskesmas.
                """
                
                response = model.generate_content(prompt)
                st.markdown("### Hasil Laporan AI:")
                st.write(response.text)

                st.session_state['last_report'] = response.text
    except Exception as e:
        st.error(f"Gagal membaca isi berkas Excel/CSV: {e}")

# Fitur Chat AI Interaktif
if 'last_report' in st.session_state:
    st.markdown("---")
    st.subheader("💬 Chat dengan AI untuk Revisi/Pertanyaan Laporan")
    user_query = st.text_input("Ingin mengubah bagian tertentu atau bertanya tentang data ini?")
    if user_query:
        chat_prompt = f"Berdasarkan laporan berikut:\n{st.session_state['last_report']}\n\nPertanyaan/Permintaan Pengguna: {user_query}"
        chat_response = model.generate_content(chat_prompt)
        st.write(chat_response.text)
