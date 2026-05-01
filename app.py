import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import smtplib
from email.mime.text import MIMEText

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Sistem", layout="wide")
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

# --- 3. DINAMIČKI MENI IZ GOOGLE TABELE ---
try:
    df_meni = conn.read(spreadsheet=spreadsheet_url, worksheet="Meni", ttl=0)
    # Grupišemo jela po danima u format koji aplikacija koristi
    meni = df_meni.groupby('Dan', sort=False)['Jelo'].apply(list).to_dict()
except Exception as e:
    st.error(f"Greška pri učitavanju menija iz tabele: {e}")
    st.stop()

# --- 4. LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.sidebar.header("Prijava")
    u = st.sidebar.text_input("Korisničko ime")
    p = st.sidebar.text_input("Lozinka", type="password")
    if st.sidebar.button("Prijavi se"):
        if u in users and users[u] == p:
            st.session_state["logged_in"] = True
            st.session_state["user"] = u
            st.rerun()
        else:
            st.sidebar.error("Pogrešni podaci")
else:
    # --- 5. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Panel")
        df_narudzbe = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
        
        if not df_narudzbe.empty:
            zbirno = df_narudzbe.groupby(['Dan', 'Jelo'])['Kolicina'].sum().reset_index()
            izbor_dana = st.selectbox("Izaberi dan:", list(meni.keys()))
            danasnji_plan = zbirno[zbirno['Dan'] == izbor_dana]
            st.table(danasnji_plan)
        else:
            st.info("Nema narudžbi.")

    # --- 6. KORISNIČKI PANEL ---
    else:
        st.title(f"Dobrodošli, {st.session_state['user']}")
        t1, t2 = st.tabs(["🛒 Nova Narudžba", "📜 Istorija"])
        
        with t1:
            with st.form("f"):
                nove = []
                for dan, jela in meni.items():
                    st.subheader(dan)
                    for jelo in jela:
                        c1, c2 = st.columns([3,1])
                        c1.write(f"**{jelo}**")
                        kol = c2.number_input("Količina", 0, 100, key=f"{dan}_{jelo}")
                        if kol > 0:
                            nove.append({"Firma": st.session_state['user'], "Dan": dan, "Jelo": jelo, "Kolicina": int(kol)})
                    st.divider()
                if st.form_submit_button("POŠALJI"):
                    if nove:
                        stari = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.concat([stari, pd.DataFrame(nove)], ignore_index=True))
                        st.success("Narudžba je poslana!")
                        st.balloons()

        with t2:
            df_history = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
            st.dataframe(df_history[df_history['Firma'] == st.session_state['user']], use_container_width=True)

    if st.sidebar.button("Odjavi se"):
        st.session_state["logged_in"] = False
        st.rerun()
