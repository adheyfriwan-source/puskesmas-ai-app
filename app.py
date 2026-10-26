import os
import pandas as pd
import streamlit as st
import google.generativeai as genai

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Asisten Laporan Puskesmas AI", 
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Asisten Pembuat Laporan Puskesmas berbasis AI")
st.caption("Unggah berkas data Puskesmas (Excel/CSV) untuk meracik laporan otomatis dengan bantuan Gemini AI.")

# --- KONFIGURASI API KEY (MENGGUNAKAN SECRETS ATAU FALLBACK KODE ANDA) ---
API_KEY_DEFAULT = "AQ.Ab8RN6KIHLyg7eMp8pX-Qfy2q3_Etgpz9FpNISQsJH-_BEGIMQ"
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", API_KEY_DEFAULT)

# Inisialisasi Pustaka AI
genai.configure(api_key=GEMINI_API_KEY)

# Fungsi Inisialisasi Model dengan Penanganan Otomatis
def init_gemini_model():
    candidate_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash']
    for model_name in candidate_models:
        try:
            return genai.GenerativeModel(model_name)
        except Exception:
            continue
    return genai.GenerativeModel('gemini-1.5-flash')

model = init_gemini_model()

# --- TAMPILAN UTAMA UNGGAH BERKAS ---
uploaded_file = st.file_uploader(
    "Unggah Berkas Data Puskesmas (Format .xlsx, .xls, atau .csv)", 
    type=['xlsx', 'xls', 'csv']
)

if uploaded_file:
    st.success("✅ Berkas berhasil dimuat! Data diproses aman secara sementara di memori.")

    # Membaca Data Excel/CSV dari Memori
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.subheader("📊 Pratinjau Data Unggahan:")
        st.dataframe(df.head(10), use_container_width=True)

        st.markdown("---")
        st.subheader("📝 Pengaturan Pembuatan Laporan")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            jenis_laporan = st.selectbox(
                "Pilih Jenis Laporan Puskesmas:",
                [
                    "Laporan Bulanan Stunting", 
                    "Laporan Kesehatan Ibu & Anak (KIA)", 
                    "Laporan Capaian Program Kesehatan", 
                    "Laporan Penyakit Menular / PTM",
                    "Laporan Kustom"
                ]
            )
        
        with col2:
            instruksi_tambahan = st.text_area(
                "Instruksi Khusus / Catatan Tambahan (Opsional):",
                placeholder="Contoh: Fokuskan analisis pada kenaikan kasus di Kelurahan A..."
            )

        if st.button("🚀 Hasilkan Laporan dengan AI", type="primary"):
            with st.spinner("Gemini AI sedang menganalisis data dan menyusun laporan..."):
                try:
                    data_summary = df.to_string()
                    
                    prompt = f"""
                    Anda adalah asisten AI profesional spesialis pembuatan laporan kesehatan di Puskesmas. 
                    Buatlah {jenis_laporan} secara komprehensif berdasarkan data berikut:
                    
                    DATA PUSKESMAS:
                    {data_summary}
                    
                    INSTRUKSI TAMBAHAN:
                    {instruksi_tambahan if instruksi_tambahan else 'Tidak ada instruksi khusus.'}
                    
                    PETUNJUK FORMATTING LAPORAN:
                    1. Judul Laporan yang resmi dan baku.
                    2. Pendahuluan & Ringkasan Eksekutif.
                    3. Analisis Data Utama (sampaikan angka kunci, tren, atau temuan signifikan).
                    4. Narasi Capaian / Kendala di Lapangan.
                    5. Rekomendasi Tindak Lanjut Teknis untuk Tim Puskesmas.
                    
                    Gunakan bahasa Indonesia yang formal, sistematis, dan mudah dipahami.
                    """
                    
                    response = model.generate_content(prompt)
                    
                    st.markdown("---")
                    st.subheader("📄 Hasil Laporan AI:")
                    st.markdown(response.text)

                    st.session_state['last_report'] = response.text
                    
                except Exception as err:
                    st.error(f"⚠️ Gagal memproses laporan dengan AI: {err}")
                    st.info("Catatan: Jika terjadi error API Key, pastikan membuat API Key baru dari Google AI Studio (aistudio.google.com) yang diawali huruf 'AIzaSy...'.")

    except Exception as e:
        st.error(f"❌ Gagal membaca isi berkas Excel/CSV: {e}")

# --- FITUR CHAT REVISI INTERAKTIF ---
if 'last_report' in st.session_state:
    st.markdown("---")
    st.subheader("💬 Chat dengan AI untuk Revisi / Pertanyaan Laporan")
    
    user_query = st.text_input("Ketik instruksi revisi atau pertanyaan Anda di sini:")
    
    if user_query:
        with st.spinner("Mengolah instruksi revisi..."):
            try:
                chat_prompt = f"""
                Berikut adalah laporan yang telah dibuat sebelumnya:
                ---
                {st.session_state['last_report']}
                ---
                
                Permintaan/Pertanyaan Pengguna tentang laporan di atas:
                {user_query}
                
                Berikan jawaban atau draf revisi laporan sesuai dengan permintaan pengguna di atas.
                """
                chat_response = model.generate_content(chat_prompt)
                st.markdown("### 🤖 Tanggapan AI:")
                st.write(chat_response.text)
            except Exception as e:
                st.error(f"Gagal memproses percakapan: {e}")
