# Birleşimler sayfası

import pandas as pd
import streamlit as st

from ortak import MEKANIZASYON_ADI, TUR_ADI, harita, oku, sb


def baglari_oku(tablo):
    return sb().table(tablo).select("*").execute().data


def baglari_guncelle(tablo, birlesim_id, alan, yeni, mevcut):
    """Bir birleşimin bağlarını, seçilen listeye göre ekler veya siler."""
    for i in set(mevcut) - set(yeni):
        sb().table(tablo).delete().eq("birlesim_id", birlesim_id).eq(alan, i).execute()
    for i in set(yeni) - set(mevcut):
        sb().table(tablo).insert({"birlesim_id": birlesim_id, alan: i}).execute()


def ekran():
    st.header("Birleşimler")
    st.caption(
        "TEST/DEMO sürümü. Bir birleşimde birden fazla WPS olabilir. "
        "Her WPS'in dayanak WPQR'ı listede görünür; uygunluğu mühendis değerlendirir."
    )

    try:
        projeler = harita("proje", lambda s: f"{s['kod']} — {s['ad']}")
        prosedurler = harita("prosedur", lambda s: f"{s['numara']} ({s['tur']})")
        personeller = harita(
            "personel", lambda s: f"{s['ad_soyad']} ({TUR_ADI.get(s['tur'], s['tur'])})"
        )
    except Exception:
        st.error("Seçim listeleri okunamadı. Tablo izinlerini kontrol edin.")
        return
    if not projeler:
        st.info("Önce Projeler sayfasından bir proje ekleyin.")
        return

    # ------------------------------------------------------ yeni birleşim
    st.subheader("Yeni birleşim")
    with st.form("yeni_birlesim", clear_on_submit=True):
        proje_id = st.selectbox(
            "Proje", list(projeler.keys()), format_func=lambda i: projeler[i]
        )
        parca = st.text_input("Parça")
        tip = st.text_input("Birleşim tipi")
        kalinlik = st.number_input("Kalınlık (mm)", value=None, min_value=0.0)
        pozisyon = st.text_input("Pozisyon")
        mek = st.selectbox(
            "Mekanizasyon seviyesi",
            list(MEKANIZASYON_ADI.keys()),
            format_func=lambda x: MEKANIZASYON_ADI[x],
        )
        kalite = st.text_input("Kalite seviyesi")
        wps_idler = st.multiselect(
            "Bağlı WPS'ler (birden fazla olabilir)",
            list(prosedurler.keys()),
            format_func=lambda i: prosedurler[i],
        )
        personel_idler = st.multiselect(
            "Çalışacak personel",
            list(personeller.keys()),
            format_func=lambda i: personeller[i],
        )
        kaydet = st.form_submit_button("Birleşimi kaydet")
    if kaydet:
        if not parca.strip():
            st.error("Parça adı zorunludur.")
        else:
            try:
                yanit = (
                    sb()
                    .table("birlesim")
                    .insert(
                        {
                            "proje_id": proje_id,
                            "parca": parca.strip(),
                            "birlesim_tipi": tip.strip() or None,
                            "kalinlik_mm": kalinlik,
                            "pozisyon": pozisyon.strip() or None,
                            "mekanizasyon": mek,
                            "kalite_seviyesi": kalite.strip() or None,
                        }
                    )
                    .execute()
                )
                yeni_id = yanit.data[0]["id"]
                st.success("Birleşim kaydedildi.")
                try:
                    baglari_guncelle("birlesim_prosedur", yeni_id, "prosedur_id", wps_idler, [])
                    baglari_guncelle("birlesim_personel", yeni_id, "personel_id", personel_idler, [])
                except Exception:
                    st.error(
                        "Birleşim kaydedildi ama WPS veya personel bağlantıları kurulamadı. "
                        "Aşağıdaki bölümden tekrar deneyin."
                    )
            except Exception:
                st.error("Kaydedilemedi.")

    # ------------------------------------------- bağlantıları düzenleme
    try:
        birlesimler = oku("birlesim")
        wps_baglari = baglari_oku("birlesim_prosedur")
        per_baglari = baglari_oku("birlesim_personel")
    except Exception:
        st.error("Birleşimler okunamadı. Tablo izinlerini kontrol edin.")
        return

    st.subheader("Bağlı WPS ve personeli düzenle")
    if not birlesimler:
        st.info("Henüz birleşim yok.")
        return
    etiketler = {
        b["id"]: f"{b['parca']} — {projeler.get(b['proje_id'], '?')}" for b in birlesimler
    }
    bid = st.selectbox(
        "Birleşim seçin",
        list(etiketler.keys()),
        format_func=lambda i: etiketler[i],
        key="b_sec",
    )
    mevcut_wps = [x["prosedur_id"] for x in wps_baglari if x["birlesim_id"] == bid]
    mevcut_per = [x["personel_id"] for x in per_baglari if x["birlesim_id"] == bid]
    yeni_wps = st.multiselect(
        "Bağlı WPS'ler",
        list(prosedurler.keys()),
        default=mevcut_wps,
        format_func=lambda i: prosedurler[i],
        key=f"d_wps_{bid}",
    )
    yeni_per = st.multiselect(
        "Çalışacak personel",
        list(personeller.keys()),
        default=mevcut_per,
        format_func=lambda i: personeller[i],
        key=f"d_per_{bid}",
    )
    if st.button("Değişiklikleri kaydet", key="b_kaydet"):
        try:
            baglari_guncelle("birlesim_prosedur", bid, "prosedur_id", yeni_wps, mevcut_wps)
            baglari_guncelle("birlesim_personel", bid, "personel_id", yeni_per, mevcut_per)
            st.success("Bağlantılar güncellendi.")
        except Exception:
            st.error("Güncellenemedi. Tablo izinlerini kontrol edin.")

    # ---------------------------------------------------------- liste
    st.subheader("Kayıtlı birleşimler")
    try:
        wps_baglari = baglari_oku("birlesim_prosedur")
        per_baglari = baglari_oku("birlesim_personel")
        prosedur_wpqr = {
            b["prosedur_id"]: b["wpqr_id"] for b in baglari_oku("prosedur_wpqr")
        }
        wpqr_adlari = {w["id"]: w["numara"] for w in oku("wpqr")}
    except Exception:
        st.error("Bağlantılar okunamadı. Tablo izinlerini kontrol edin.")
        return

    satirlar = []
    for b in birlesimler:
        wps_ids = [x["prosedur_id"] for x in wps_baglari if x["birlesim_id"] == b["id"]]
        per_ids = [x["personel_id"] for x in per_baglari if x["birlesim_id"] == b["id"]]
        wpqr_numaralari = sorted(
            {
                wpqr_adlari[prosedur_wpqr[i]]
                for i in wps_ids
                if i in prosedur_wpqr and prosedur_wpqr[i] in wpqr_adlari
            }
        )
        satirlar.append(
            {
                "Proje": projeler.get(b["proje_id"], ""),
                "Parça": b["parca"],
                "Birleşim tipi": b["birlesim_tipi"],
                "Kalınlık (mm)": b["kalinlik_mm"],
                "Pozisyon": b["pozisyon"],
                "Mekanizasyon": MEKANIZASYON_ADI.get(b["mekanizasyon"], b["mekanizasyon"]),
                "Kalite seviyesi": b["kalite_seviyesi"],
                "WPS'ler": ", ".join(prosedurler.get(i, "?") for i in wps_ids),
                "Dayanak WPQR'lar": ", ".join(wpqr_numaralari),
                "Personel": ", ".join(personeller.get(i, "?") for i in per_ids),
            }
        )
    st.dataframe(pd.DataFrame(satirlar), hide_index=True)
