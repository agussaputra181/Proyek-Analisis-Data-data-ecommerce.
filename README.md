# Proyek Analisis Data: E-Commerce Public Dataset

Analisis data E-Commerce Public Dataset (Brasil) periode Januari 2017 – Agustus 2018,
dilengkapi dashboard interaktif dengan Streamlit.

- **Nama:** Putu Agus Saputra
- **Email:** agusputrasa@hotmail.com
- **ID Dicoding:** ds174b6y1448

## Pertanyaan Bisnis
1. Bagaimana tren pendapatan dan jumlah pesanan bulanan, dan kapan puncak penjualan?
2. Kategori produk apa yang menyumbang pendapatan tertinggi dan terendah?
3. Seberapa besar pengaruh keterlambatan pengiriman terhadap skor ulasan?
4. Negara bagian mana yang pendapatannya terbesar dan pengirimannya paling lama?

Analisis lanjutan: RFM Analysis, Geospatial Analysis, dan Clustering (binning & manual grouping).

## Struktur Proyek
```
├── .streamlit
│   └── config.toml          # tema warna dashboard
├── dashboard
│   ├── dashboard.py         # aplikasi Streamlit
│   ├── main_data.csv        # data bersih hasil notebook
│   └── customer_geo.csv     # koordinat pelanggan hasil notebook
├── data                     # 9 file CSV dataset mentah
├── notebook.ipynb           # seluruh proses analisis data
├── README.md
├── requirements.txt
└── url.txt                  # link dashboard di Streamlit Cloud
```

## Setup Environment - Anaconda
```
conda create --name main-ds python=3.11
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal
```
python -m venv venv
venv\Scripts\activate       
pip install -r requirements.txt
```

## Run Streamlit App
Jalankan dari folder utama proyek:
```
streamlit run dashboard/dashboard.py
```
Dashboard akan terbuka di `http://localhost:8501`.

## Catatan
- Semua grafik dibuat dengan **plotly** sehingga interaktif (hover, zoom).
  Buka `Proyek_Analisis_Data.ipynb` di Google Colab, Jupyter, atau VS Code agar grafik tampil.
<<<<<<< HEAD
- Dashboard online: lihat link di `url.txt`.
=======
- Dashboard online: lihat link di `url.txt`.
>>>>>>> b198fa2 (memperbaharui README)
