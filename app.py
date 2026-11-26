# KaynakCoPro V1.0 - TEST/DEMO sürümü
# Parça 3: giriş, Projeler, Personel ve belgeler, WPQR

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


# ------------------------------------------------------------------- WPQR
def harita(tablo, etiket):
    return {s["id"]: etiket(s) for s in oku(tablo)}


def secim(baslik, secenekler, anahtar):
    return st.selectbox(
        baslik,
        [None] + list(secenekler.keys()),
        format_func=lambda i: "— seçilmedi —" if i is None else secenekler[i],
        key=anahtar,
    )


def wpqr_ekrani():
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
        sayfa = st.radio("Sayfa", ["Projeler", "Personel ve belgeler", "WPQR"])
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
    elif sayfa == "WPQR":
        wpqr_ekrani()


ana()
