# WPQR sayfası

import pandas as pd
import streamlit as st

from ortak import harita, oku, sb, secim


def ekran():
    st.header("WPQR")
    st.caption(
        "TEST/DEMO sürümü: gerçek standart değeri girmeyin. "
        "Test türü listesi standarttan gelecek; şimdilik serbest yazıdır."
    )

    try:
        malzemeler = harita("malzeme_grubu", lambda s: f"{s['grup_kodu']} [{s['durum']}]")
        dolgular = harita(
            "dolgu_malzemesi",
            lambda s: f"{s['sinif']}" + (f", ⌀{s['cap_mm']} mm" if s["cap_mm"] is not None else ""),
        )
        gazlar = harita("koruma_gazi", lambda s: s["sinif"])
    except Exception:
        st.error("Seçim listeleri okunamadı. Tablo izinlerini kontrol edin.")
        return

    st.subheader("Yeni WPQR")
    with st.form("yeni_wpqr", clear_on_submit=True):
        numara = st.text_input("WPQR numarası (benzersiz)")
        proses = st.text_input("Proses", value="135")
        malzeme_id = secim("Malzeme grubu", malzemeler, "w_malzeme")
        kalinlik = st.number_input("Kalınlık (mm)", value=None, min_value=0.0)
        dolgu_id = secim("Dolgu malzemesi", dolgular, "w_dolgu")
        gaz_id = secim("Koruyucu gaz", gazlar, "w_gaz")
        st.markdown("**Test sırasında kullanılan değerler (tek değer)**")
        akim = st.number_input("Akım (A)", value=None, min_value=0.0)
        gerilim = st.number_input("Gerilim (V)", value=None, min_value=0.0)
        hiz = st.number_input("Kaynak hızı (mm/dk)", value=None, min_value=0.0)
        tarih = st.date_input("Tarih", value=None, format="DD.MM.YYYY")
        ozet = st.text_area("Sonuç özeti")
        kaydet = st.form_submit_button("WPQR'ı kaydet")
    if kaydet:
        if not numara.strip():
            st.error("WPQR numarası zorunludur.")
        else:
            try:
                sb().table("wpqr").insert(
                    {
                        "numara": numara.strip(),
                        "proses": proses.strip() or "135",
                        "malzeme_grubu_id": malzeme_id,
                        "kalinlik_mm": kalinlik,
                        "dolgu_malzemesi_id": dolgu_id,
                        "koruma_gazi_id": gaz_id,
                        "akim_a": akim,
                        "gerilim_v": gerilim,
                        "hiz_mm_dk": hiz,
                        "tarih": tarih.isoformat() if tarih else None,
                        "sonuc_ozeti": ozet.strip() or None,
                    }
                ).execute()
                st.success("WPQR kaydedildi (durum: Taslak).")
            except Exception:
                st.error("Kaydedilemedi. Bu WPQR numarası zaten kullanılıyor olabilir.")

    st.subheader("Kayıtlı WPQR'lar")
    try:
        wpqrlar = oku("wpqr")
    except Exception:
        st.error("WPQR kayıtları okunamadı. Tablo izinlerini kontrol edin.")
        return
    if not wpqrlar:
        st.info("Henüz WPQR yok.")
        return

    satirlar = []
    for w in wpqrlar:
        satirlar.append(
            {
                "Numara": w["numara"],
                "Proses": w["proses"],
                "Malzeme grubu": malzemeler.get(w["malzeme_grubu_id"], ""),
                "Kalınlık (mm)": w["kalinlik_mm"],
                "Dolgu": dolgular.get(w["dolgu_malzemesi_id"], ""),
                "Gaz": gazlar.get(w["koruma_gazi_id"], ""),
                "Akım (A)": w["akim_a"],
                "Gerilim (V)": w["gerilim_v"],
                "Hız (mm/dk)": w["hiz_mm_dk"],
                "Tarih": w["tarih"],
                "Sonuç özeti": w["sonuc_ozeti"],
                "Durum": w["durum"],
            }
        )
    st.dataframe(pd.DataFrame(satirlar), hide_index=True)

    st.subheader("Testler")
    numaralar = {w["id"]: w["numara"] for w in wpqrlar}
    wid = st.selectbox(
        "WPQR seçin",
        list(numaralar.keys()),
        format_func=lambda i: numaralar[i],
        key="test_wpqr",
    )
    with st.form("yeni_test", clear_on_submit=True):
        test_turu = st.text_input("Test türü")
        sonuc = st.text_input("Sonuç")
        test_kaydet = st.form_submit_button("Testi kaydet")
    if test_kaydet:
        if not test_turu.strip():
            st.error("Test türü zorunludur.")
        else:
            try:
                sb().table("wpqr_test").insert(
                    {
                        "wpqr_id": wid,
                        "test_turu": test_turu.strip(),
                        "sonuc": sonuc.strip() or None,
                    }
                ).execute()
                st.success("Test kaydedildi.")
            except Exception:
                st.error("Test kaydedilemedi.")

    try:
        testler = (
            sb().table("wpqr_test").select("*").eq("wpqr_id", wid).order("id").execute().data
        )
    except Exception:
        st.error("Testler okunamadı. Tablo izinlerini kontrol edin.")
        return
    if not testler:
        st.info("Bu WPQR için test kaydı yok.")
        return
    tdf = pd.DataFrame(testler)[["test_turu", "sonuc"]]
    tdf.columns = ["Test türü", "Sonuç"]
    st.dataframe(tdf, hide_index=True)
