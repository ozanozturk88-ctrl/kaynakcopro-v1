# Projeler sayfası

import pandas as pd
import streamlit as st

from ortak import oku, sb


def ekran():
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
