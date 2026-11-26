# Prosedürler (pWPS / WPS) sayfası

import pandas as pd
import streamlit as st

from ortak import MEKANIZASYON_ADI, harita, oku, sb, secim

TUR_SECENEKLERI = ["pWPS", "WPS"]


def aralik(alt, ust):
    if alt is None and ust is None:
        return ""
    sol = "?" if alt is None else f"{alt:g}"
    sag = "?" if ust is None else f"{ust:g}"
    return f"{sol} – {sag}"


def aralik_hatasi(ad, alt, ust):
    if alt is not None and ust is not None and alt > ust:
        return f"{ad}: en az değer, en çok değerden büyük olamaz."
    return None


def ekran():
    st.header("Prosedürler (pWPS / WPS)")
    st.caption(
        "TEST/DEMO sürümü: gerçek standart değeri girmeyin. Aralıkları mühendis girer; "
        "program WPQR değerinden WPS aralığı hesaplamaz. Bir WPS tek WPQR'a dayanır."
    )

    try:
        malzemeler = harita("malzeme_grubu", lambda s: f"{s['grup_kodu']} [{s['durum']}]")
        dolgular = harita(
            "dolgu_malzemesi",
            lambda s: f"{s['sinif']}" + (f", ⌀{s['cap_mm']} mm" if s["cap_mm"] is not None else ""),
        )
        gazlar = harita("koruma_gazi", lambda s: s["sinif"])
        wpqr_kayitlari = {w["id"]: w for w in oku("wpqr")}
    except Exception:
        st.error("Seçim listeleri okunamadı. Tablo izinlerini kontrol edin.")
        return
    wpqr_adlari = {i: w["numara"] for i, w in wpqr_kayitlari.items()}

    # ------------------------------------------------------ yeni prosedür
    st.subheader("Yeni prosedür")
    with st.form("yeni_prosedur", clear_on_submit=True):
        numara = st.text_input("Prosedür numarası (benzersiz)")
        tur = st.selectbox("Tür", TUR_SECENEKLERI)
        mek = st.selectbox(
            "Mekanizasyon",
            list(MEKANIZASYON_ADI.keys()),
            format_func=lambda x: MEKANIZASYON_ADI[x],
        )
        malzeme_id = secim("Malzeme grubu", malzemeler, "p_malzeme")
        dolgu_id = secim("Dolgu malzemesi", dolgular, "p_dolgu")
        gaz_id = secim("Koruyucu gaz", gazlar, "p_gaz")
        wpqr_id = secim("Dayanak WPQR (en fazla bir)", wpqr_adlari, "p_wpqr")

        st.markdown("**Aralıklar (en az – en çok)**")
        s1, s2 = st.columns(2)
        kal_min = s1.number_input("Kalınlık en az (mm)", value=None, min_value=0.0)
        kal_max = s2.number_input("Kalınlık en çok (mm)", value=None, min_value=0.0)
        a1, a2 = st.columns(2)
        akim_min = a1.number_input("Akım en az (A)", value=None, min_value=0.0)
        akim_max = a2.number_input("Akım en çok (A)", value=None, min_value=0.0)
        g1, g2 = st.columns(2)
        ger_min = g1.number_input("Gerilim en az (V)", value=None, min_value=0.0)
        ger_max = g2.number_input("Gerilim en çok (V)", value=None, min_value=0.0)
        h1, h2 = st.columns(2)
        hiz_min = h1.number_input("Hız en az (mm/dk)", value=None, min_value=0.0)
        hiz_max = h2.number_input("Hız en çok (mm/dk)", value=None, min_value=0.0)
        kaydet = st.form_submit_button("Prosedürü kaydet")

    if kaydet:
        hatalar = [
            h
            for h in (
                aralik_hatasi("Kalınlık", kal_min, kal_max),
                aralik_hatasi("Akım", akim_min, akim_max),
                aralik_hatasi("Gerilim", ger_min, ger_max),
                aralik_hatasi("Hız", hiz_min, hiz_max),
            )
            if h
        ]
        if not numara.strip():
            st.error("Prosedür numarası zorunludur.")
        elif hatalar:
            for h in hatalar:
                st.error(h)
        else:
            try:
                yanit = (
                    sb()
                    .table("prosedur")
                    .insert(
                        {
                            "numara": numara.strip(),
                            "tur": tur,
                            "mekanizasyon": mek,
                            "malzeme_grubu_id": malzeme_id,
                            "dolgu_malzemesi_id": dolgu_id,
                            "koruma_gazi_id": gaz_id,
                            "kalinlik_min_mm": kal_min,
                            "kalinlik_max_mm": kal_max,
                            "akim_min_a": akim_min,
                            "akim_max_a": akim_max,
                            "gerilim_min_v": ger_min,
                            "gerilim_max_v": ger_max,
                            "hiz_min_mm_dk": hiz_min,
                            "hiz_max_mm_dk": hiz_max,
                        }
                    )
                    .execute()
                )
                yeni_id = yanit.data[0]["id"]
                st.success("Prosedür kaydedildi (durum: Taslak).")
                if wpqr_id is not None:
                    try:
                        sb().table("prosedur_wpqr").insert(
                            {"prosedur_id": yeni_id, "wpqr_id": wpqr_id}
                        ).execute()
                        st.success("Dayanak WPQR bağlandı.")
                    except Exception:
                        st.error(
                            "Prosedür kaydedildi ama dayanak WPQR bağlanamadı. "
                            "Aşağıdaki bölümden tekrar deneyin."
                        )
            except Exception:
                st.error("Kaydedilemedi. Bu prosedür numarası zaten kullanılıyor olabilir.")

    # ------------------------------------------------------ dayanak WPQR
    try:
        prosedurler = oku("prosedur")
    except Exception:
        st.error("Prosedürler okunamadı. Tablo izinlerini kontrol edin.")
        return

    st.subheader("Dayanak WPQR'ı bağla veya değiştir")
    if not prosedurler or not wpqr_adlari:
        st.info("Bağlamak için en az bir prosedür ve bir WPQR gerekir.")
    else:
        prosedur_adlari = {p["id"]: f"{p['numara']} ({p['tur']})" for p in prosedurler}
        with st.form("bagla", clear_on_submit=True):
            bp = st.selectbox(
                "Prosedür",
                list(prosedur_adlari.keys()),
                format_func=lambda i: prosedur_adlari[i],
            )
            bw = st.selectbox(
                "Dayanak WPQR",
                list(wpqr_adlari.keys()),
                format_func=lambda i: wpqr_adlari[i],
            )
            bagla = st.form_submit_button("Bağla (varsa eskisini değiştirir)")
        if bagla:
            try:
                sb().table("prosedur_wpqr").delete().eq("prosedur_id", bp).execute()
                sb().table("prosedur_wpqr").insert(
                    {"prosedur_id": bp, "wpqr_id": bw}
                ).execute()
                st.success("Dayanak WPQR bağlandı.")
            except Exception:
                st.error("Bağlanamadı. Tablo izinlerini kontrol edin.")

    # ---------------------------------------------------------- liste
    st.subheader("Kayıtlı prosedürler")
    if not prosedurler:
        st.info("Henüz prosedür yok.")
        return
    try:
        baglar = {
            b["prosedur_id"]: b["wpqr_id"]
            for b in sb().table("prosedur_wpqr").select("*").execute().data
        }
    except Exception:
        st.error("Dayanak WPQR bağlantıları okunamadı.")
        baglar = {}

    satirlar = []
    for p in prosedurler:
        w = wpqr_kayitlari.get(baglar.get(p["id"]))
        satirlar.append(
            {
                "Numara": p["numara"],
                "Tür": p["tur"],
                "Mekanizasyon": MEKANIZASYON_ADI.get(p["mekanizasyon"], p["mekanizasyon"]),
                "Malzeme grubu": malzemeler.get(p["malzeme_grubu_id"], ""),
                "Kalınlık (mm)": aralik(p["kalinlik_min_mm"], p["kalinlik_max_mm"]),
                "Dolgu": dolgular.get(p["dolgu_malzemesi_id"], ""),
                "Gaz": gazlar.get(p["koruma_gazi_id"], ""),
                "Akım (A)": aralik(p["akim_min_a"], p["akim_max_a"]),
                "Gerilim (V)": aralik(p["gerilim_min_v"], p["gerilim_max_v"]),
                "Hız (mm/dk)": aralik(p["hiz_min_mm_dk"], p["hiz_max_mm_dk"]),
                "Dayanak WPQR": w["numara"] if w else "",
                "WPQR akım (A)": w["akim_a"] if w else None,
                "WPQR gerilim (V)": w["gerilim_v"] if w else None,
                "WPQR hız (mm/dk)": w["hiz_mm_dk"] if w else None,
                "Durum": p["durum"],
            }
        )
    st.dataframe(pd.DataFrame(satirlar), hide_index=True)
