# Personel ve belgeler sayfası

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from ortak import TUR_ADI, oku, sb


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


def ekran():
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
