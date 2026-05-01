import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import smtplib
from email.mime.text import MIMEText

# --- 1. KONFIGURACIJA STRANICE ---
st.set_page_config(page_title="Catering Narudžbe", layout="centered")

# CSS za ljepši izgled
st.markdown("""
    <style>
    .stNumberInput { width: 120px !important; }
    </style>
    """, unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. KORISNICI ---
users = {
    "admin": "tvoja_admin_sifra_123",
    "Lattonedil": "lattonedil321",
    "PVA Group": "pvagroup321",
    "Esintec": "esintec321",
    "ActivBH": "activbh321"
}

# --- 3. DINAMIČKI MENI, DATUM I ROK ---
try:
    df_meni_raw = conn.read(spreadsheet=spreadsheet_url, worksheet="Meni", ttl=0)
    
    # Izvlačenje info redova (Sedmica i Rok)
    sedmica_info = df_meni_raw[df_meni_raw['Dan'] == 'Sedmica']['Jelo'].values
    rok_info = df_meni_raw[df_meni_raw['Dan'] == 'Rok']['Jelo'].values
    
    sed_tekst = sedmica_info[0] if len(sedmica_info) > 0 else "Nije uneseno"
    rok_tekst = rok_info[0] if len(rok_info) > 0 else "Nije uneseno"

    # Filtriranje samo jela za prave dane
    pravi_dani = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak"]
    df_jela = df_meni_raw[df_meni_raw['Dan'].isin(pravi_dani)]
    meni = df_jela.groupby('Dan', sort=False)['Jelo'].apply(list).to_dict()
    
except Exception as e:
    st.error(f"Greška pri učitavanju tabele Meni: {e}")
    st.stop()

# --- 4. FUNKCIJA ZA EMAIL ---
def posalji_email(firma, podaci):
    try:
        sender = st.secrets["connections"]["gsheets"].get("email_user")
        pwd = st.secrets["connections"]["gsheets"].get("email_password")
        if sender and pwd:
            detalji = "\n".join([f"{n['Dan']} - {n['Jelo']}: {n['Kolicina']} kom" for n in podaci])
            msg = MIMEText(f"Nova narudžba od: {firma}\n\n{detalji}")
            msg['Subject'] = f"Nova Narudžba - {firma}"
            msg['From'] = sender
            msg['To'] = sender
            with smtplib.SMTP_SSL("://gmail.com", 465) as server:
                server.login(sender, pwd)
                server.sendmail(sender, sender, msg.as_string())
    except:
        pass

# --- 5. LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.sidebar.header("🔐 Prijava za Firme")
    u = st.sidebar.text_input("Korisničko ime")
    p = st.sidebar.text_input("Lozinka", type="password")
    if st.sidebar.button("Prijavi se", use_container_width=True):
        if u in users and users[u] == p:
            st.session_state["logged_in"] = True
            st.session_state["user"] = u
            st.rerun()
        else:
            st.sidebar.error("Pogrešni podaci")
else:
    # --- 6. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Panel - Pregled Kuhinje")
        df_n = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
        
        if not df_n.empty:
            zbirno = df_n.groupby(['Dan', 'Jelo'])['Kolicina'].sum().reset_index()
            izbor_dana = st.selectbox("Izaberi dan:", list(meni.keys()))
            plan = zbirno[zbirno['Dan'] == izbor_dana]
            st.subheader(f"Plan za {izbor_dana}")
            st.table(plan)
            st.metric("Ukupno obroka", plan['Kolicina'].sum())
        else:
            st.info("Nema narudžbi.")

    # --- 7. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 Dobrodošli, {st.session_state['user']}")
        
        # INFO TRAKA (DATUM I ROK)
        c_info1, c_info2 = st.columns(2)
        with c_info1:
            st.info(f"📅 **Meni za period:**\n\n{sed_tekst}")
        with c_info2:
            st.warning(f"⏰ **Rok za narudžbu:**\n\n{rok_tekst}")
        
        t1, t2 = st.tabs(["🛒 Nova Narudžba", "📜 Istorija"])
        
        with t1:
            with st.form("narudzba_f", clear_on_submit=True):
                nove_n = []
                for dan, jela in meni.items():
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}")
                        for jelo in jela:
                            c1, c2 = st.columns([3, 1])
                            with c1:
                                st.markdown(f"<div style='padding-top: 8px;'><b>{jelo}</b></div>", unsafe_allow_html=True)
                            with c2:
                                kol = st.number_input("Kol.", 0, 100, step=1, key=f"{dan}_{jelo}", label_visibility="collapsed")
                            if kol > 0:
                                nove_n.append({"Firma": st.session_state['user'], "Dan": dan, "Jelo": jelo, "Kolicina": int(kol)})
                
                st.markdown("<br>", unsafe_allow_html=True)
                _, col_b, _ = st.columns([1, 2, 1])
                if col_b.form_submit_button("🚀 POŠALJI NARUDŽBU", use_container_width=True):
                    if nove_n:
                        stari = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0).dropna(how='all')
                        updated = pd.concat([stari, pd.DataFrame(nove_n)], ignore_index=True)
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=updated)
                        posalji_email(st.session_state['user'], nove_n)
                        st.success("✅ Narudžba uspješno poslana!")
                        st.balloons()
                    else:
                        st.warning("⚠️ Unesite količinu.")

        with t2:
            try:
                hist = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
                st.dataframe(hist[hist['Firma'] == st.session_state['user']], use_container_width=True, hide_index=True)
            except:
                st.error("Greška pri učitavanju istorije.")

    if st.sidebar.button("Odjavi se", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()
