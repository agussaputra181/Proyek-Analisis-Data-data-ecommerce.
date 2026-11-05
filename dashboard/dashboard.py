import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ------------------------------------------------------------------
# Konfigurasi halaman & gaya
# ------------------------------------------------------------------
st.set_page_config(page_title="\U0001F6CD\uFE0F E-Commerce Dashboard", page_icon="\U0001F6CD\uFE0F", layout="wide")
MAIN, ACCENT, GREY = "#1f6f8b", "#e07a5f", "#c9d1d3"
TEMPLATE = "plotly_white"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------
# Load data (di-cache agar dashboard cepat)
# ------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join(BASE_DIR, "main_data.csv"), parse_dates=["order_purchase_timestamp"])
    return df


@st.cache_data
def load_customer_geo():
    return pd.read_csv(os.path.join(BASE_DIR, "customer_geo.csv"))


@st.cache_data
def state_centers():
    """Titik pusat tiap negara bagian = median koordinat pelanggan (dari tabel geolocation)."""
    return load_customer_geo().groupby("customer_state")[["lat", "lng"]].median()


@st.cache_data
def silhouette_points():
    """Siluet Brasil dari koordinat pelanggan (dibulatkan agar ringan), tanpa file peta tambahan."""
    return load_customer_geo()[["lat", "lng"]].round(1).drop_duplicates()


def map_figure(height=560):
    """Kanvas peta: siluet abu-abu + sumbu disembunyikan + proporsi lintang-bujur dijaga."""
    sil = silhouette_points()
    fig = go.Figure(go.Scatter(x=sil["lng"], y=sil["lat"], mode="markers", hoverinfo="skip",
                               marker=dict(size=3, color="#b8c2c6", opacity=0.5)))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x")
    fig.update_layout(template=TEMPLATE, height=height, showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def to_order_level(df):
    """1 baris = 1 pesanan, agar metrik per pesanan tidak terhitung ganda."""
    return df.groupby("order_id").agg(
        order_date=("order_purchase_timestamp", "first"),
        customer_unique_id=("customer_unique_id", "first"),
        customer_state=("customer_state", "first"),
        order_value=("total_value", "sum"),
        delivery_days=("delivery_days", "first"),
        delay_days=("delay_days", "first"),
        is_late=("is_late", "first"),
        review_score=("review_score", "first"),
    ).reset_index()


def build_rfm(order_df):
    snapshot = order_df["order_date"].max().normalize() + pd.Timedelta(days=1)
    rfm = order_df.groupby("customer_unique_id").agg(
        last_order=("order_date", "max"),
        frequency=("order_id", "nunique"),
        monetary=("order_value", "sum")).reset_index()
    rfm["recency"] = (snapshot - rfm["last_order"].dt.normalize()).dt.days
    rfm["R_score"] = pd.qcut(rfm["recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["M_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    conditions = [
        (rfm["frequency"] >= 2) & (rfm["R_score"] >= 4),
        (rfm["frequency"] >= 2),
        (rfm["R_score"] >= 4) & (rfm["M_score"] >= 4),
        (rfm["R_score"] >= 4),
        (rfm["R_score"] == 3),
        (rfm["M_score"] >= 4),
    ]
    choices = ["Champions", "Loyal Customers", "Big Spender Baru", "Pelanggan Baru",
               "Need Attention", "At Risk (Big Spender)"]
    rfm["segment"] = np.select(conditions, choices, default="Hibernating")
    return rfm


main_df = load_data()

# ------------------------------------------------------------------
# Sidebar: filter interaktif
# ------------------------------------------------------------------
with st.sidebar:
    st.title("\U0001F6CD\uFE0FE-Commerce")
    st.caption("Proyek Analisis Data – Dicoding")
    min_date = main_df["order_purchase_timestamp"].min().date()
    max_date = main_df["order_purchase_timestamp"].max().date()
    date_range = st.date_input("Rentang waktu pembelian", value=[min_date, max_date],
                               min_value=min_date, max_value=max_date)
    states = sorted(main_df["customer_state"].unique())
    selected_states = st.multiselect("Negara bagian (kosongkan = semua)", states)
    categories = sorted(main_df["category"].dropna().unique())
    selected_categories = st.multiselect("Kategori produk (kosongkan = semua)", categories)
    st.markdown("---")
    st.caption("Data: E-Commerce Public Dataset, Jan 2017 – Agu 2018, pesanan berstatus *delivered*.")

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    st.warning("Pilih tanggal awal dan tanggal akhir pada sidebar.")
    st.stop()

mask = (main_df["order_purchase_timestamp"].dt.date >= start_date) & \
       (main_df["order_purchase_timestamp"].dt.date <= end_date)
if selected_states:
    mask &= main_df["customer_state"].isin(selected_states)
if selected_categories:
    mask &= main_df["category"].isin(selected_categories)
df = main_df[mask]


if df.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Silakan ubah filter pada sidebar.")
    st.stop()

order_df = to_order_level(df)
with st.sidebar:
    st.download_button("Unduh data filter (CSV)", df.to_csv(index=False).encode("utf-8"), 
                       file_name="data_terfilter.csv", mime="text/csv")
# ------------------------------------------------------------------
# Header & KPI
# ------------------------------------------------------------------
st.title("\U0001F6CD\uFE0F Dashboard Analisis E-Commerce")
st.caption(f"Periode: {start_date:%d %b %Y} – {end_date:%d %b %Y}"
           + (f" | Negara bagian: {', '.join(selected_states)}" if selected_states else " | Semua negara bagian"))

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total pesanan", f"{order_df['order_id'].nunique():,}", help="Jumlah pesanan yang sudah diterima pelanggan pada periode dan filter terpilih")
k2.metric("Total pendapatan", f"BRL {order_df['order_value'].sum() / 1e6:,.2f} juta", help="Harga barang + ongkos kirim dari semua pesanan terpilih")
k3.metric("Rata-rata skor ulasan", f"{order_df['review_score'].mean():.2f} / 5", help="Rata-rata bintang ulasan pelanggan (1 = sangat buruk, 5 = sangat baik)")
k4.metric("Pesanan terlambat", f"{order_df['is_late'].mean() * 100:.1f}%", help="Persentase pesanan yang tiba setelah tanggal estimasi pengiriman")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 Tren Bulanan", "🏷️ Kategori Produk", "🚚 Pengiriman & Ulasan", "🗺️ Geografis", "👥 Segmentasi RFM"])

# ------------------------------------------------------------------
# Tab 1 – Pertanyaan 1
# ------------------------------------------------------------------
with tab1:
    st.subheader("Bagaimana tren pendapatan dan jumlah pesanan bulanan?")
    monthly = (order_df.set_index("order_date").resample("MS")
               .agg(order_count=("order_id", "nunique"), revenue=("order_value", "sum")))
    monthly.index = monthly.index.strftime("%Y-%m")
    peak = monthly["revenue"].idxmax()

    months = monthly.index.tolist()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.6, 0.4], vertical_spacing=0.1,
                        subplot_titles=("Pendapatan bulanan (BRL)", "Jumlah pesanan bulanan"))
    fig.add_trace(go.Bar(x=months, y=monthly["revenue"], marker_color=[ACCENT if m == peak else MAIN for m in months],
                         customdata=monthly["order_count"],
                         hovertemplate="%{x}<br>Pendapatan: BRL %{y:,.0f}<br>Pesanan: %{customdata:,}<extra></extra>"),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=months, y=monthly["order_count"], mode="lines+markers", line=dict(color=MAIN),
                             hovertemplate="%{x}<br>Pesanan: %{y:,}<extra></extra>"), row=2, col=1)
    fig.update_xaxes(type="category", tickangle=-45)
    fig.update_yaxes(rangemode="tozero")
    fig.update_layout(template=TEMPLATE, height=560, showlegend=False, title=f"Puncak pendapatan: {peak}")
    st.plotly_chart(fig)

    with st.expander("💡 Insight"):
        st.write("Pendapatan tumbuh pesat sepanjang 2017 dan memuncak pada November 2017 (Black Friday). "
                 "Pada 2018 pendapatan stabil di kisaran 1 juta BRL per bulan dan sedikit menurun pada Juni–Agustus.")

# ------------------------------------------------------------------
# Tab 2 – Pertanyaan 2
# ------------------------------------------------------------------
with tab2:
    st.subheader("Kategori produk apa yang menyumbang pendapatan tertinggi dan terendah?")
    n = st.slider("Jumlah kategori yang ditampilkan", 5, 15, 10)
    cat = df.groupby("category").agg(revenue=("price", "sum"), items=("order_item_id", "count")) \
            .sort_values("revenue", ascending=False)
    share = cat["revenue"].cumsum() / cat["revenue"].sum()
    st.info(f"**{int((share <= 0.8).sum()) + 1} dari {len(cat)} kategori** menyumbang 80% pendapatan.")

    c1, c2 = st.columns(2)
    for col, data, title, color in [(c1, cat.head(n).iloc[::-1], "Pendapatan tertinggi", MAIN),
                                    (c2, cat.tail(n), "Pendapatan terendah", ACCENT)]:
        with col:
            fig = go.Figure(go.Bar(x=data["revenue"], y=data.index, orientation="h", marker_color=color,
                                   customdata=data["items"],
                                   hovertemplate="%{y}<br>BRL %{x:,.0f}<br>Item terjual: %{customdata:,}<extra></extra>"))
            fig.update_xaxes(title_text="Pendapatan (BRL)", tickformat=",.0f", rangemode="tozero")
            fig.update_layout(template=TEMPLATE, title=title, height=30 * n + 120, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig)

# ------------------------------------------------------------------
# Tab 3 – Pertanyaan 3 (binning)
# ------------------------------------------------------------------
with tab3:
    st.subheader("Seberapa besar pengaruh keterlambatan terhadap skor ulasan?")
    labels = ["Tepat waktu", "Telat 1-3 hari", "Telat 4-7 hari", "Telat 8-14 hari", "Telat > 14 hari"]
    order_df["delay_group"] = pd.cut(order_df["delay_days"], [-np.inf, 0, 3, 7, 14, np.inf], labels=labels)
    grp = order_df.dropna(subset=["review_score"]).groupby("delay_group", observed=False).agg(
        orders=("order_id", "count"), avg_review=("review_score", "mean"),
        bad_pct=("review_score", lambda s: (s <= 2).mean() * 100 if len(s) else np.nan))

    m1, m2 = st.columns(2)
    m1.metric("Skor rata-rata – tepat waktu", f"{order_df.loc[~order_df['is_late'], 'review_score'].mean():.2f}")
    late_score = order_df.loc[order_df["is_late"], "review_score"].mean()
    m2.metric("Skor rata-rata – terlambat", "-" if np.isnan(late_score) else f"{late_score:.2f}")

    colors = [MAIN] + [ACCENT] * 4
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Rata-rata skor ulasan", "% ulasan buruk (skor 1-2)"))
    fig.add_trace(go.Bar(x=labels, y=grp["avg_review"], marker_color=colors, customdata=grp["orders"],
                         hovertemplate="%{x}<br>Skor: %{y:.2f}<br>Pesanan: %{customdata:,}<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Bar(x=labels, y=grp["bad_pct"], marker_color=colors, customdata=grp["orders"],
                         hovertemplate="%{x}<br>Ulasan buruk: %{y:.1f}%<br>Pesanan: %{customdata:,}<extra></extra>"),
                  row=1, col=2)
    fig.update_yaxes(range=[0, 5], row=1, col=1)
    fig.update_yaxes(range=[0, 100], ticksuffix="%", row=1, col=2)
    fig.update_xaxes(tickangle=-20)
    fig.update_layout(template=TEMPLATE, height=430, showlegend=False)
    st.plotly_chart(fig)
    st.dataframe(grp.rename(columns={"orders": "Jumlah pesanan", "avg_review": "Rata-rata skor",
                                     "bad_pct": "% ulasan buruk"})
                 .rename_axis("Kelompok keterlambatan") .style.format({"Jumlah pesanan": "{:,.0f}", "Rata-rata skor": "{:.2f}", "% ulasan buruk": "{:.1f}%"}, na_rep="–"))

# ------------------------------------------------------------------
# Tab 4 – Pertanyaan 4 (geospatial)
# ------------------------------------------------------------------
with tab4:
    st.subheader("State mana yang pendapatannya terbesar dan pengirimannya paling lama?")
    metric_label = st.radio("Metrik pada peta",
                            ["Pendapatan (BRL)", "Rata-rata lama pengiriman (hari)", "% pesanan terlambat"],
                            horizontal=True)
    state = order_df.groupby("customer_state").agg(
        revenue=("order_value", "sum"), avg_delivery_days=("delivery_days", "mean"),
        late_pct=("is_late", lambda s: s.mean() * 100), orders=("order_id", "nunique")).reset_index()
    col_map = {"Pendapatan (BRL)": ("revenue", "Blues"),
               "Rata-rata lama pengiriman (hari)": ("avg_delivery_days", "Oranges"),
               "% pesanan terlambat": ("late_pct", "Reds")}
    column, cmap = col_map[metric_label]

    geo = state.set_index("customer_state").join(state_centers())
    c1, c2 = st.columns([3, 2])
    with c1:
        fig = map_figure()
        size = 10 + np.sqrt(geo["revenue"] / geo["revenue"].max()) * 45
        fig.add_trace(go.Scatter(x=geo["lng"], y=geo["lat"], mode="markers", text=geo.index,
                                 marker=dict(size=size, color=geo[column], colorscale=cmap, opacity=0.9,
                                             line=dict(color="#555555", width=0.6),
                                             colorbar=dict(title=metric_label, tickformat=",.0f")),
                                 customdata=geo[["revenue", "avg_delivery_days", "late_pct"]],
                                 hovertemplate="<b>%{text}</b><br>Pendapatan: BRL %{customdata[0]:,.0f}"
                                               "<br>Rata-rata kirim: %{customdata[1]:.1f} hari"
                                               "<br>Pesanan telat: %{customdata[2]:.1f}%<extra></extra>"))
        fig.update_layout(title="Ukuran gelembung = pendapatan; warna = metrik terpilih")
        st.plotly_chart(fig)
    with c2:
        st.markdown(f"**Top 10 state – {metric_label}**")
    top = state.sort_values(column, ascending=False).head(10)[["customer_state", column, "orders"]]
    tabel = top.rename(columns={"customer_state": "Negara bagian", column: metric_label, "orders": "Jumlah pesanan"}).set_index("Negara bagian")
    st.dataframe(tabel.style.format({metric_label: "{:,.1f}", "Jumlah pesanan": "{:,.0f}"})) 
    terbesar = state.sort_values("revenue", ascending=False).iloc[0]
    terlama = state.sort_values("avg_delivery_days", ascending=False).iloc[0]
    st.info(
        f"**{terbesar['customer_state']}** menyumbang pendapatan terbesar (BRL {terbesar['revenue']:,.0f}), "
        f"sedangkan pengiriman telama ada di **{terlama['customer_state']}** "
        f"(rata-rata {terlama['avg_delivery_days']:.1f} hari)."
    )
    st.markdown("#### Sebaran lokasi pelanggan")
    st.caption("Setiap titik adalah satu pelanggan, berdasarkan koordinat kode pos dari tabel geolocation.")
    cust_geo = load_customer_geo()
    cust_geo = cust_geo[cust_geo["customer_unique_id"].isin(order_df["customer_unique_id"])]
    fig = map_figure()
    fig.add_trace(go.Scattergl(x=cust_geo["lng"], y=cust_geo["lat"], mode="markers",
                               marker=dict(size=2, color=MAIN, opacity=0.3), customdata=cust_geo["customer_state"],
                               hovertemplate="Negara bagian : %{customdata}<extra></extra>"))
    c3, c4 = st.columns([3, 2])
    with c3:
        st.plotly_chart(fig)
    with c4:
        st.metric("Pelanggan terpetakan", f"{len(cust_geo):,}")
        st.write("Titik pelanggan terkonsentrasi di pesisir Tenggara dan Selatan, "
                 "sejalan dengan konsentrasi pendapatan pada peta di atas.")

# ------------------------------------------------------------------
# Tab 5 – RFM
# ------------------------------------------------------------------
with tab5:
    st.subheader("Segmentasi pelanggan dengan RFM Analysis")
    rfm = build_rfm(order_df)
    r1, r2, r3 = st.columns(3)
    r1.metric("Rata-rata Recency", f"{rfm['recency'].mean():.0f} hari",
              help="Berapa hari sejak pelanggan terakhir belanja (makin kecil makin baik)")
    r2.metric("Rata-rata Frequency", f"{rfm['frequency'].mean():.2f} pesanan",
              help="Rata-rata Jumlah pesanan per pelanggan")
    r3.metric("Rata-rata Monetary", f"BRL {rfm['monetary'].mean():,.2f}",
              help="Rata-rata total belanja per pelanggan")

    seg = rfm.groupby("segment").agg(customers=("customer_unique_id", "count"), revenue=("monetary", "sum"))
    seg["% pelanggan"] = seg["customers"] / seg["customers"].sum() * 100
    seg["% pendapatan"] = seg["revenue"] / seg["revenue"].sum() * 100
    seg = seg.sort_values("% pendapatan")

    fig = go.Figure()
    fig.add_trace(go.Bar(y=seg.index, x=seg["% pelanggan"], orientation="h", name="% pelanggan", marker_color=GREY,
                         customdata=seg["customers"],
                         hovertemplate="%{y}<br>%{x:.1f}% pelanggan (%{customdata:,} orang)<extra></extra>"))
    fig.add_trace(go.Bar(y=seg.index, x=seg["% pendapatan"], orientation="h", name="% pendapatan", marker_color=MAIN,
                         customdata=seg["revenue"],
                         hovertemplate="%{y}<br>%{x:.1f}% pendapatan (BRL %{customdata:,.0f})<extra></extra>"))
    fig.update_xaxes(ticksuffix="%", rangemode="tozero")
    fig.update_layout(template=TEMPLATE, barmode="group", height=450, title="Porsi pelanggan vs porsi pendapatan per segmen",
                      legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig)

    with st.expander("Aturan segmentasi"):
        st.markdown("""
- **Champions**: belanja ≥ 2 kali dan baru saja belanja (R-score ≥ 4)
- **Loyal Customers**: belanja ≥ 2 kali, tetapi sudah agak lama
- **Big Spender Baru**: sekali belanja, baru-baru ini, nilai besar (M-score ≥ 4)
- **Pelanggan Baru**: sekali belanja, baru-baru ini, nilai kecil
- **Need Attention**: sekali belanja, recency sedang (R-score = 3)
- **At Risk (Big Spender)**: sekali belanja bernilai besar, tetapi sudah lama
- **Hibernating**: sekali belanja bernilai kecil dan sudah lama
""")

st.markdown("----")
st.caption("Dibuat oleh Putu Agus Saputra– Proyek Analisis Data: E-Commerce Public Dataset (Jan 2017- Agu 2018)")