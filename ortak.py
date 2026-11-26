# KaynakCoPro V1.0 - ortak yardımcılar (bağlantı, giriş ekranı, seçim listeleri)

import streamlit as st
from supabase import create_client

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

MEKANIZASYON_ADI = {
    "elde_torclu": "Elde torçlu",
    "robot": "Robot",
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


def harita(tablo, etiket):
    """Bir tablodaki satırları {id: görünen ad} biçiminde verir."""
    return {s["id"]: etiket(s) for s in oku(tablo)}


def secim(baslik, secenekler, anahtar):
    """İsteğe bağlı seçim kutusu (seçilmezse None döner)."""
    return st.selectbox(
        baslik,
        [None] + list(secenekler.keys()),
        format_func=lambda i: "— seçilmedi —" if i is None else secenekler[i],
        key=anahtar,
    )


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
