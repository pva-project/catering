import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import smtplib
from email.mime.text import MIMEText

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Sistem", layout="wide")
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. KORISNICI (Dodaj sebe kao admina) ---
users = {
    "admin": "tvoja_admin_sifra_123", # PROMIJENI OVO
    "Lattonedil": "lattonedil321",
    "PVA Group": "pvagroup321",
    "Esintec": "esintec321",
    "ActivBH": "activbh321"
}

meni = {
    "Ponedjeljak": ["Grah sa mesom", "Piletina u curry sosu", "Falafel salata"],
    "Utorak": ["Musaka", "Bečka šnicla", "Rižoto sa povrćem"],
    "Srijeda": ["Sarma", "Piletina na žaru", "Pohovani sir"],
    "Četvrtak": ["Gulaš", "Pastrmka", "Pasta Napoli"],
    "Petak": ["Oslić sa krompirom", "Lignje", "Povrtni đuveč"]
}

# --- 3. LOGIN ---
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
    # --- 4. ADMIN PANEL (Samo za tebe) ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Panel - Pregled Kuhinje")
        try:
            df = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
            
            if not df.empty:
                st.subheader("Ukupno porcija za napraviti (po danima):")
                # Grupisanje podataka: Sabira količine za isto jelo istog dana
                zbirno = df.groupby(['Dan', 'Jelo'])['Kolicina'].sum().reset_index()
                
                # Prikaz po danima radi lakšeg kuhanja
                za_dan = st.selectbox("Izaberi dan za pregled:", list(meni.keys()))
                danasnji_plan = zbirno[zbirno['Dan'] == za_dan]
                
                if not danasnji_plan.empty:
                    st.table(danasnji_plan)
                    st.metric("Ukupno obroka za ovaj dan", danasnji_plan['Kolicina'].sum())
                else:
                    st.info("Nema narudžbi za ovaj dan.")
                
                st.divider()
                st.subheader("Sve pojedinačne narudžbe (Log):")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Tabela je trenutno prazna.")
        except Exception as e:
            st.error(f"Greška pri učitavanju: {e}")

    # --- 5. KORISNIČKI PANEL (Za firme) ---
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
                        kol = c2.number_input("Kol.", 0, 100, key=f"{dan}_{jelo}")
                        c1.write(jelo)
                        if kol > 0:
                            nove.append({"Firma": st.session_state['user'], "Dan": dan, "Jelo": jelo, "Kolicina": int(kol)})
                if st.form_submit_button("POŠALJI"):
                    if nove:
                        stari = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.concat([stari, pd.DataFrame(nove)], ignore_index=True))
                        st.success("Poslano!")
                        st.balloons()
        
        with t2:
            df = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
            st.dataframe(df[df['Firma'] == st.session_state['user']], use_container_width=True)

    if st.sidebar.button("Odjavi se"):
        st.session_state["logged_in"] = False
        st.rerun()
