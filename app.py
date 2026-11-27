# KaynakCoPro V1.0 - TEST/DEMO sürümü
# Ana dosya: giriş kontrolü ve sayfa menüsü. Her sayfa kendi dosyasındadır.

import streamlit as st

st.set_page_config(page_title="KaynakCoPro V1.0 (DEMO)", page_icon="🔧", layout="wide")

import sayfa_birlesim
import sayfa_kullanici
import sayfa_personel
import sayfa_proje
import sayfa_prosedur
import sayfa_wpqr
from ortak import ROL_ADI, giris_ekrani, sb

# Menüye yeni sayfa eklemek için buraya bir satır eklenir.
SAYFALAR = {
    "Projeler": sayfa_proje.ekran,
    "Birleşimler": sayfa_birlesim.ekran,
    "Prosedürler (pWPS/WPS)": sayfa_prosedur.ekran,
    "WPQR": sayfa_wpqr.ekran,
    "Personel ve belgeler": sayfa_personel.ekran,
    "Kullanıcılar": sayfa_kullanici.ekran,
}


def ana():
    if "kullanici" not in st.session_state:
        giris_ekrani()
        return

    k = st.session_state["kullanici"]
    with st.sidebar:
        st.markdown(f"**{k['ad_soyad']}**")
        st.caption(ROL_ADI.get(k["rol"], k["rol"]))
        st.caption("TEST/DEMO sürümü")
        sayfa = st.radio("Sayfa", list(SAYFALAR.keys()))
        if st.button("Çıkış"):
            try:
                sb().auth.sign_out()
            except Exception:
                pass
            st.session_state.clear()
            st.rerun()

    SAYFALAR[sayfa]()


ana()
