# KaynakCoPro V1.0 - TEST/DEMO sürümü
# Parça 1: giriş ekranı ve Projeler sayfası

import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="KaynakCoPro V1.0 (DEMO)", page_icon="🔧", layout="wide")

ROL_ADI = {
    "muhendis": "Kaynak mühendisi",
    "vekil": "Kaynak mühendisi vekili",
    "inspektor": "Kaynak inspektörü",
}


def sb():
    """Her tarayıcı oturumu için ayrı bir Supabase bağlantısı tutar."""
    if "sb" not in st.session_state:
        st.session_state["sb"] = create_client(
            st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
        )
    return st.session_state["sb"]


def giris_ekrani():
    st.title("KaynakCoPro V1.0")
    st.warning("TEST/DEMO sürümü: yalnızca uydurma (DEMO) verilerle kullanılır.")
    with st.form("giris"):
        eposta = st.text_input("E-posta")
        sifre = st.text_input("Şifre", type="password")
        gonder = st.form_submit_button("Giriş yap")
    if not gonder:
        return

    try:
        yanit = sb().auth.sign_in_with_password(
            {"email": eposta.strip(), "password": sifre}
        )
    except Exception:
        st.error("Giriş yapılamadı. E-posta veya şifreyi kontrol edin.")
        return

    try:
        kayit = (
            sb().table("kullanici").select("*").eq("id", yanit.user.id).execute().data
        )
    except Exception:
        st.error("Kullanıcı kaydı okunamadı. Tablo izinlerini kontrol edin.")
        return

    if not kayit or not kayit[0]["aktif"]:
        sb().auth.sign_out()
        st.error("Bu hesap için kullanıcı kaydı yok veya hesap pasif.")
        return

    st.session_state["kullanici"] = kayit[0]
    st.rerun()


def proje_ekrani():
    st.header("Projeler")

    st.subheader("Yeni proje")
    with st.form("yeni_proje", clear_on_submit=True):
        kod = st.text_input("Proje kodu (benzersiz)")
        ad = st.text_input("Proje adı")
        musteri = st.text_input("Müşteri")
        kaydet = st.form_submit_button("Kaydet")
    if kaydet:
        if not kod.strip() or not ad.strip():
            st.error("Proje kodu ve proje adı zorunludur.")
        else:
            try:
                sb().table("proje").insert(
                    {
                        "kod": kod.strip(),
                        "ad": ad.strip(),
                        "musteri": musteri.strip() or None,
                    }
                ).execute()
                st.success("Proje kaydedildi (durum: Taslak, faz: Faz 0).")
            except Exception:
                st.error("Kaydedilemedi. Bu proje kodu zaten kullanılıyor olabilir.")

    st.subheader("Kayıtlı projeler")
    try:
        veri = sb().table("proje").select("*").order("id").execute().data
    except Exception:
        st.error("Projeler okunamadı. Tablo izinlerini kontrol edin.")
        return
    if not veri:
        st.info("Henüz proje yok.")
        return
    df = pd.DataFrame(veri)[
        ["kod", "ad", "musteri", "faz", "durum", "olusturma_zamani"]
    ]
    df.columns = [
        "Proje kodu",
        "Proje adı",
        "Müşteri",
        "Faz",
        "Durum",
        "Oluşturma zamanı",
    ]
    st.dataframe(df, hide_index=True)


def ana():
    if "kullanici" not in st.session_state:
        giris_ekrani()
        return

    k = st.session_state["kullanici"]
    with st.sidebar:
        st.markdown(f"**{k['ad_soyad']}**")
        st.caption(ROL_ADI.get(k["rol"], k["rol"]))
        st.caption("TEST/DEMO sürümü")
        sayfa = st.radio("Sayfa", ["Projeler"])
        if st.button("Çıkış"):
            try:
                sb().auth.sign_out()
            except Exception:
                pass
            st.session_state.clear()
            st.rerun()

    if sayfa == "Projeler":
        proje_ekrani()


ana()
