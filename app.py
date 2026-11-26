# KaynakCoPro V1.0 - TEST/DEMO sürümü
# Parça 2: giriş, Projeler, Personel ve belgeler

from datetime import date, timedelta

import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="KaynakCoPro V1.0 (DEMO)", page_icon="🔧", layout="wide")

ROL_ADI = {
    "muhendis": "Kaynak mühendisi",
    "vekil": "Kaynak mühendisi vekili",
    "inspektor": "Kaynak inspektörü",
}

TUR_ADI = {
    "kaynakci": "Kaynakçı",
    "robot_operator_ayarci": "Robot operatörü/ayarcı",
    "inspektor": "İnspektör",
}


def sb():
    """Her tarayıcı oturumu için ayrı bir Supabase bağlantısı tutar."""
    if "sb" not in st.session_state:
        st.session_state["sb"] = create_client(
            st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
        )
    return st.session_state["sb"]


def oku(tablo):
    return sb().table(tablo).select("*").order("id").execute().data


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


# ---------------------------------------------------------------- Projeler
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
        veri = oku("proje")
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


# ------------------------------------------------------ Personel ve belgeler
def gecerlilik_durumu(tarih_metni):
    if not tarih_metni:
        return "Tarih yok"
    bitis = date.fromisoformat(tarih_metni)
    bugun = date.today()
    if bitis < bugun:
        return "Süresi dolmuş"
    if bitis <= bugun + timedelta(days=30):
        return "30 gün içinde bitiyor"
    return "Geçerli"


def personel_ekrani():
    st.header("Personel ve belgeler")
    st.caption("Gerçek personel adı girmeyin; TEST/DEMO sürümünde uydurma adlar kullanılır.")

    st.subheader("Yeni personel")
    with st.form("yeni_personel", clear_on_submit=True):
        ad = st.text_input("Ad soyad")
        tur = st.selectbox(
            "Tür", list(TUR_ADI.keys()), format_func=lambda x: TUR_ADI[x]
        )
        kaydet = st.form_submit_button("Kaydet")
    if kaydet:
        if not ad.strip():
            st.error("Ad soyad zorunludur.")
        else:
            try:
                sb().table("personel").insert(
                    {"ad_soyad": ad.strip(), "tur": tur}
                ).execute()
                st.success("Personel kaydedildi.")
            except Exception:
                st.error("Kaydedilemedi.")

    st.subheader("Kayıtlı personel")
    try:
        personel = oku("personel")
    except Exception:
        st.error("Personel okunamadı. Tablo izinlerini kontrol edin.")
        return
    if not personel:
        st.info("Henüz personel yok.")
        return
    df = pd.DataFrame(personel)[["ad_soyad", "tur", "aktif"]]
    df["tur"] = df["tur"].map(lambda x: TUR_ADI.get(x, x))
    df["aktif"] = df["aktif"].map(lambda x: "Evet" if x else "Hayır")
    df.columns = ["Ad soyad", "Tür", "Aktif"]
    st.dataframe(df, hide_index=True)

    st.subheader("Belgeler")
    bilgi = {p["id"]: p for p in personel}
    pid = st.selectbox(
        "Personel seçin",
        list(bilgi.keys()),
        format_func=lambda i: f"{bilgi[i]['ad_soyad']} ({TUR_ADI.get(bilgi[i]['tur'], bilgi[i]['tur'])})",
    )

    with st.form("yeni_belge", clear_on_submit=True):
        belge_turu = st.text_input("Belge türü")
        kapsam = st.text_input("Kapsam")
        verilis = st.date_input("Veriliş tarihi", value=None, format="DD.MM.YYYY")
        gecerlilik = st.date_input("Geçerlilik tarihi", value=None, format="DD.MM.YYYY")
        belge_kaydet = st.form_submit_button("Belgeyi kaydet")
    if belge_kaydet:
        if not belge_turu.strip():
            st.error("Belge türü zorunludur.")
        elif verilis and gecerlilik and gecerlilik < verilis:
            st.error("Geçerlilik tarihi, veriliş tarihinden önce olamaz.")
        else:
            try:
                sb().table("personel_belgesi").insert(
                    {
                        "personel_id": pid,
                        "belge_turu": belge_turu.strip(),
                        "kapsam": kapsam.strip() or None,
                        "verilis_tarihi": verilis.isoformat() if verilis else None,
                        "gecerlilik_tarihi": gecerlilik.isoformat() if gecerlilik else None,
                    }
                ).execute()
                st.success("Belge kaydedildi (durum: DEMO).")
            except Exception:
                st.error("Belge kaydedilemedi.")

    try:
        belgeler = (
            sb()
            .table("personel_belgesi")
            .select("*")
            .eq("personel_id", pid)
            .order("id")
            .execute()
            .data
        )
    except Exception:
        st.error("Belgeler okunamadı. Tablo izinlerini kontrol edin.")
        return
    if not belgeler:
        st.info("Bu personel için belge yok.")
        return
    bdf = pd.DataFrame(belgeler)
    bdf["gecerlilik_durumu"] = bdf["gecerlilik_tarihi"].map(gecerlilik_durumu)
    bdf = bdf[
        [
            "belge_turu",
            "kapsam",
            "verilis_tarihi",
            "gecerlilik_tarihi",
            "gecerlilik_durumu",
            "durum",
        ]
    ]
    bdf.columns = [
        "Belge türü",
        "Kapsam",
        "Veriliş",
        "Geçerlilik",
        "Geçerlilik durumu",
        "Kayıt durumu",
    ]
    st.dataframe(bdf, hide_index=True)


# -------------------------------------------------------------------- Ana
def ana():
    if "kullanici" not in st.session_state:
        giris_ekrani()
        return

    k = st.session_state["kullanici"]
    with st.sidebar:
        st.markdown(f"**{k['ad_soyad']}**")
        st.caption(ROL_ADI.get(k["rol"], k["rol"]))
        st.caption("TEST/DEMO sürümü")
        sayfa = st.radio("Sayfa", ["Projeler", "Personel ve belgeler"])
        if st.button("Çıkış"):
            try:
                sb().auth.sign_out()
            except Exception:
                pass
            st.session_state.clear()
            st.rerun()

    if sayfa == "Projeler":
        proje_ekrani()
    elif sayfa == "Personel ve belgeler":
        personel_ekrani()


ana()
