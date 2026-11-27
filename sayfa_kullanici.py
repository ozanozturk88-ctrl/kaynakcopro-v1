# Kullanıcılar sayfası (yalnızca görüntüleme)

import pandas as pd
import streamlit as st

from ortak import ROL_ADI, harita, oku


def ekran():
    st.header("Kullanıcılar")
    st.caption(
        "Bu sayfa yalnızca görüntüleme içindir. Kullanıcı ekleme, vekil yetkilendirme "
        "ve rol bazlı izinler Adım 2'de yapılacak."
    )

    try:
        kullanicilar = oku("kullanici")
        personeller = harita("personel", lambda s: s["ad_soyad"])
    except Exception:
        st.error("Kullanıcılar okunamadı. Tablo izinlerini kontrol edin.")
        return
    if not kullanicilar:
        st.info("Henüz kullanıcı kaydı yok.")
        return

    satirlar = [
        {
            "Ad soyad": k["ad_soyad"],
            "Rol": ROL_ADI.get(k["rol"], k["rol"]),
            "Aktif": "Evet" if k["aktif"] else "Hayır",
            "Bağlı personel kaydı": personeller.get(k["personel_id"], ""),
        }
        for k in kullanicilar
    ]
    st.dataframe(pd.DataFrame(satirlar), hide_index=True)
