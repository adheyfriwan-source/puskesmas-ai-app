import os
import io
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
import google.generativeai as genai
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Asisten Laporan Puskesmas AI", layout="wide")
st.title("🏥 Asisten Pembuat Laporan Puskesmas berbasis AI")

# --- MENGAMBIL SECRETS ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
FOLDER_ID = st.secrets.get("GOOGLE_DRIVE_FOLDER_ID", os.getenv("GOOGLE_DRIVE_FOLDER_ID"))

# Inisialisasi Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Inisialisasi Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']
if "gcp_service_account" in st.secrets:
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
else:
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=creds)

# --- FUNGSI PEMBERSIH OTOMATIS (HAPUS BERKAS > 48 JAM) ---
def auto_delete_old_files():
    try:
        query = f"'{FOLDER_ID}' in parents and trashed = false"
        results = drive_service.files().list(q=query, fields="files(id, name, createdTime)").execute()
        files = results.get('files', [])
        
        now = datetime.now(timezone.utc)
        for f in files:
            created_time = datetime.fromisoformat(f['createdTime'].replace('Z', '+00:00'))
            age_in_hours = (now - created_time).total_seconds() / 3600
            
            if age_in_hours > 48:
                drive_service.files().delete(fileId=f['id']).execute()
    except Exception as e:
        st.warning(f"Info pembersihan otomatis: {e}")

# Jalankan pembersihan berkas lama
auto_delete_old_files()

# --- FUNGSI UPLOAD AMAN KE GOOGLE DRIVE ---
def upload_to_drive(uploaded_file):
    try:
        file_metadata = {
            'name': uploaded_file.name,
            'parents': [FOLDER_ID]
        }
        fh = io.BytesIO(uploaded_file.getvalue())
        media = MediaIoBaseUpload(fh, mimetype=uploaded_file.type or 'application/octet-stream', resumable=True)
        
        uploaded_drive_file = drive_service.files().create(
            body=file_metadata, media_body=media, fields='id'
        ).execute()
        return uploaded_drive_file.get('id')
    except Exception as e:
        st.error(f"Gagal mengunggah ke Drive. Pastikan folder Drive sudah dibagikan ke email Service Account sebagai Editor. Detail: {e}")
        return None

# --- TAMPILAN UTAMA APLIKASI ---
uploaded_file = st.file_uploader("Unggah Berkas Data Puskesmas (Excel/CSV)", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    with st.spinner("Mengunggah berkas ke Google Drive..."):
        file_id = upload_to_drive(uploaded_file)
    
    if file_id:
        st.success("Berkas berhasil diunggah! (Akan otomatis terhapus dalam 2 hari).")

        # Membaca data
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
                with st.spinner("Gemini AI sedang meracik laporan..."):
                    data_summary = df.to_string()
                    
                    prompt = f"""
                    Anda adalah asisten AI profesional di Puskesmas. Buatlah {jenis_laporan} berdasarkan data berikut:
                    
                    {data_summary}
                    
                    Instruksi Tambahan: {instruksi_tambahan}
                    
                    Format laporan harus rapi, baku, mencakup analisis angka/trend kunci, narasi capaian, serta rekomendasi tindak lanjut.
                    """
                    
                    response = model.generate_content(prompt)
                    st.markdown("### Hasil Laporan AI:")
                    st.write(response.text)

                    st.session_state['last_report'] = response.text
        except Exception as e:
            st.error(f"Gagal membaca isi berkas Excel/CSV: {e}")

# Fitur Chat AI
if 'last_report' in st.session_state:
    st.markdown("---")
    st.subheader("💬 Chat dengan AI untuk Revisi/Pertanyaan Laporan")
    user_query = st.text_input("Ingin mengubah bagian tertentu atau bertanya tentang data ini?")
    if user_query:
        chat_prompt = f"Berdasarkan laporan berikut:\n{st.session_state['last_report']}\n\nPertanyaan/Permintaan Pengguna: {user_query}"
        chat_response = model.generate_content(chat_prompt)
        st.write(chat_response.text)
