"""
Streamlit: Web arayüzü.
yfinance: Veri çekme.
plotly: Grafik çizme.
pandas: Tablo ve matematik işlemleri.
components: JavaScript (Scroll ve Işınlanma) için.
"""
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import streamlit.components.v1 as components 
import time

# --- 1. AYARLAR ---
st.set_page_config(
    page_title="BorsaAI Pro",        
    page_icon="📈",              
    layout="wide",               
    initial_sidebar_state="expanded",
)

# --- SİHİRLİ JAVASCRIPT SCROLL (ÇAPA YÖNTEMİ) ---
def force_scroll_to_top():
    js = """
    <script>
        var element = window.parent.document.getElementById("tepe_noktasi");
        if (element) {
            element.scrollIntoView({behavior: "smooth", block: "start", inline: "nearest"});
        }
    </script>
    """
    components.html(js, height=0)

# --- GÖRÜNMEZ ÇAPA NOKTASI ---
st.markdown('<div id="tepe_noktasi"></div>', unsafe_allow_html=True)

# --- BIST 100 GENİŞLETİLMİŞ LİSTE ---
# Ziraat'teki yükselenleri yakalamak için listeyi BIST 100 seviyesine çektik.
BIST_HAVUZU = [
    # BIST 30 (Devler)
    "THYAO.IS", "GARAN.IS", "ASELS.IS", "SISE.IS", "AKBNK.IS", "KCHOL.IS", "EREGL.IS", 
    "SAHOL.IS", "TUPRS.IS", "BIMAS.IS", "YKBNK.IS", "ISCTR.IS", "FROTO.IS", "EKGYO.IS", 
    "PETKM.IS", "TCELL.IS", "HALKB.IS", "TOASO.IS", "TTKOM.IS", "KOZAL.IS", "PGSUS.IS", 
    "ARCLK.IS", "HEKTS.IS", "SASA.IS", "KONTR.IS", "ODAS.IS", "OYAKC.IS", "ENKAI.IS", 
    "VESTL.IS", "ALARK.IS", 
    
    # BIST 100 (Diğerleri)
    "AEFES.IS", "AGHOL.IS", "AHGAZ.IS", "AKCNS.IS", "AKFGY.IS", "AKSA.IS", "AKSEN.IS", 
    "ALBRK.IS", "ALFAS.IS", "ASUZU.IS", "AYDEM.IS", "BAGFS.IS", "BERA.IS", "BIOEN.IS", 
    "BOBET.IS", "BRSAN.IS", "BRYAT.IS", "BUCIM.IS", "CANTE.IS", "CCOLA.IS", "CEMTS.IS", 
    "CIMSA.IS", "CWENE.IS", "DOAS.IS", "DOHOL.IS", "ECILC.IS", "ECZYT.IS", "EGEEN.IS", 
    "ENJSA.IS", "EUPWR.IS", "EUREN.IS", "GENIL.IS", "GESAN.IS", "GLYHO.IS", "GSDHO.IS", 
    "GUBRF.IS", "GWIND.IS", "IMASM.IS", "IPEKE.IS", "ISDMR.IS", "ISGYO.IS", "ISMEN.IS", 
    "IZMDC.IS", "KARSN.IS", "KCAER.IS", "KONYA.IS", "KORDS.IS", "KOZAA.IS", "KRDMD.IS", 
    "KZBGY.IS", "MAVI.IS", "MIATK.IS", "OTKAR.IS", "PENTA.IS", "PSGYO.IS", "QUAGR.IS", 
    "SMRTG.IS", "SNGYO.IS", "SOKM.IS", "TAVHL.IS", "TKFEN.IS", "TSKB.IS", "TTRAK.IS", 
    "TUKAS.IS", "TURSG.IS", "ULKER.IS", "VESBE.IS", "YEOTK.IS", "YYLGD.IS", "ZOREN.IS"
]

# --- 2. FONKSİYONLAR ---

# --- YENİ: TOPLU ANALİZ MOTORU ---
# Liste büyüdüğü için işlem süresi artabilir, o yüzden cache süresini koruyoruz.
@st.cache_data(ttl=300) 
def piyasayi_tarama():
    try:
        # Tüm listeyi indir (Burada biraz bekletebilir ama tek seferliktir)
        data = yf.download(BIST_HAVUZU, period="2d", group_by='ticker', progress=False, threads=True)
    except:
        return pd.DataFrame() 
    
    analiz_listesi = []
    
    for sembol in BIST_HAVUZU:
        try:
            df = data[sembol]
            if len(df) >= 2:
                bugun = df['Close'].iloc[-1]
                dun = df['Close'].iloc[-2]
                hacim = df['Volume'].iloc[-1]
                
                if pd.isna(bugun) or pd.isna(dun): continue
                    
                degisim = ((bugun - dun) / dun) * 100
                
                analiz_listesi.append({
                    "Sembol": sembol,
                    "Degisim": degisim,
                    "Hacim": hacim
                })
        except:
            continue 
            
    return pd.DataFrame(analiz_listesi)

@st.cache_data 
def get_data(sembol): 
    try:
        hisse = yf.Ticker(sembol)
        veri = hisse.history(period="1y") 
        if veri.empty: return None
        
        veri['SMA20'] = veri['Close'].rolling(window=20).mean()
        veri['SMA50'] = veri['Close'].rolling(window=50).mean()
        return veri 
    except: return None 

def buyuk_grafik_ciz(veri, sembol):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=veri.index, open=veri['Open'], high=veri['High'], low=veri['Low'], close=veri['Close'], name=sembol))
    fig.add_trace(go.Scatter(x=veri.index, y=veri['SMA20'], mode='lines', line=dict(color='cyan', width=2), name='SMA 20'))
    fig.add_trace(go.Scatter(x=veri.index, y=veri['SMA50'], mode='lines', line=dict(color='yellow', width=2), name='SMA 50'))
    fig.update_layout(title=f"{sembol} Detaylı Teknik Analiz", height=550, template='plotly_dark', xaxis_rangeslider_visible=False)
    return fig

def kucuk_grafik_ciz(veri, sembol):
    fig = go.Figure()
    son_fiyat = veri['Close'].iloc[-1]
    bas_fiyat = veri['Close'].iloc[0]
    renk = '#00ff00' if son_fiyat > bas_fiyat else '#ff0000'
    
    fig.add_trace(go.Scatter(x=veri.index, y=veri['Close'], mode='lines', line=dict(color=renk, width=2), fill='tozeroy'))
    fig.update_layout(
        title=dict(text=f"{sembol}<br>{son_fiyat:.2f} TL", font=dict(size=14, color="white"), x=0.5),
        height=180, margin=dict(l=0, r=0, t=40, b=0), template='plotly_dark', xaxis=dict(visible=False), yaxis=dict(visible=False)
    )
    return fig 

# --- 3. AKILLI BAŞLANGIÇ ---

# Piyasayı Tara
df_analiz = piyasayi_tarama()

# Seçili hisse yoksa (ilk açılış), o günün şampiyonunu (En çok artan) seç
if 'secili_hisse' not in st.session_state:
    if not df_analiz.empty:
        # En çok artan 1. hisseyi al
        sampiyon = df_analiz.sort_values(by="Degisim", ascending=False).iloc[0]['Sembol']
        st.session_state.secili_hisse = sampiyon
    else:
        st.session_state.secili_hisse = "THYAO.IS"

# Scroll Bayrağı Kontrolü
if 'yukari_git' not in st.session_state:
    st.session_state.yukari_git = False

if st.session_state.yukari_git:
    force_scroll_to_top()
    st.session_state.yukari_git = False 

# --- 4. ANA EKRAN DÜZENİ ---

st.title(f"📈 BorsaAI Pro: {st.session_state.secili_hisse}")

ana_veri = get_data(st.session_state.secili_hisse)

if ana_veri is not None:
    fig_ana = buyuk_grafik_ciz(ana_veri, st.session_state.secili_hisse)
    st.plotly_chart(fig_ana, use_container_width=True, key="ana_grafik_alani")
else:
    st.warning("Veri yükleniyor veya geçici hata... Lütfen bekleyiniz.")    

st.markdown("---") 

# --- 5. SEKMELER VE LİSTELER ---
st.subheader("🔍 Canlı Piyasa Taraması (BIST 100)") 

if not df_analiz.empty:
    # ARTIK DAHA FAZLA HİSSE GÖSTERİYORUZ (15'er tane)
    artanlar = df_analiz.sort_values(by="Degisim", ascending=False).head(15) 
    azalanlar = df_analiz.sort_values(by="Degisim", ascending=True).head(15) 
    hacimler = df_analiz.sort_values(by="Hacim", ascending=False).head(15)   

    tab1, tab2, tab3 = st.tabs(["🔥 Yükselenler", "🔻 Düşenler", "💰 Hacim Liderleri"])

    # --- SEKME 1: YÜKSELENLER ---
    with tab1:
        col1, col2, col3 = st.columns(3)
        sutunlar = [col1, col2, col3]
        for i, row in enumerate(artanlar.itertuples()):
            sembol = row.Sembol
            with sutunlar[i % 3]: 
                kucuk_veri = get_data(sembol)
                if kucuk_veri is not None:
                    fig = kucuk_grafik_ciz(kucuk_veri, sembol)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"chart_art_{sembol}")
                    
                    if st.button(f"İncele: {sembol} (%{row.Degisim:.1f})", key=f"btn_art_{sembol}", use_container_width=True):
                        st.session_state.secili_hisse = sembol
                        st.session_state.yukari_git = True 
                        st.rerun()

    # --- SEKME 2: DÜŞENLER ---
    with tab2:
        col1, col2, col3 = st.columns(3)
        sutunlar = [col1, col2, col3]
        for i, row in enumerate(azalanlar.itertuples()):
            sembol = row.Sembol
            with sutunlar[i % 3]:
                kucuk_veri = get_data(sembol)
                if kucuk_veri is not None:
                    fig = kucuk_grafik_ciz(kucuk_veri, sembol)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"chart_azl_{sembol}")
                    
                    if st.button(f"İncele: {sembol} (%{row.Degisim:.1f})", key=f"btn_azl_{sembol}", use_container_width=True):
                        st.session_state.secili_hisse = sembol
                        st.session_state.yukari_git = True
                        st.rerun()

    # --- SEKME 3: HACİM ---
    with tab3:
        col1, col2, col3 = st.columns(3)
        sutunlar = [col1, col2, col3]
        for i, row in enumerate(hacimler.itertuples()):
            sembol = row.Sembol
            with sutunlar[i % 3]:
                kucuk_veri = get_data(sembol)
                if kucuk_veri is not None:
                    fig = kucuk_grafik_ciz(kucuk_veri, sembol)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"chart_hcm_{sembol}")
                    
                    if st.button(f"İncele: {sembol}", key=f"btn_hcm_{sembol}", use_container_width=True):
                        st.session_state.secili_hisse = sembol
                        st.session_state.yukari_git = True
                        st.rerun()

else:
    st.info("BIST 100 Taranıyor... Bu işlem ilk açılışta 10-15 saniye sürebilir.")