import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Management", layout="centered")

st.markdown("""
<style>
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

# --- 2. KORISNICI ---
users = {
    "admin": "admin123",
    "Lattonedil": "lattonedil321",
    "PVA Group": "pvagroup321",
    "Esintec": "esintec321",
    "ActivBH": "activbh321"
}

# --- 3. FUNKCIJE ---
def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        df = df.dropna(how='all')
        return df
    except:
        return pd.DataFrame()

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns:
        return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    return df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict(), {}

# --- 4. LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔐 Prijava")
    u = st.text_input("Korisnik")
    p = st.text_input("Lozinka", type="password")

    if st.button("Login"):
        if u in users and users[u] == p:
            st.session_state["logged_in"] = True
            st.session_state["user"] = u
            st.rerun()
        else:
            st.error("Greška login")

else:
    st.sidebar.write(f"Korisnik: {st.session_state['user']}")
    if st.sidebar.button("Odjavi se"):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- ADMIN ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin")

        tab1, tab2 = st.tabs(["📊 Kuhinja", "📝 Meni"])

        # KUHINJA (sigurna)
        with tab1:
            df = ucitaj_sheet("Sheet1")

            if not df.empty:
                dan = st.selectbox("Dan", dani_std)
                df_dan = df[df["Dan"] == f"Ova-{dan}"]

                for jelo in df_dan["Jelo"].unique():
                    df_j = df_dan[df_dan["Jelo"] == jelo]

                    i = df_j[df_j["Smjena"] == "I"]["Kolicina"].sum()
                    ii = df_j[df_j["Smjena"] == "II"]["Kolicina"].sum()
                    iii = df_j[df_j["Smjena"] == "III"]["Kolicina"].sum()

                    st.write(jelo, i, ii, iii)

        # meni samo placeholder (ne diramo dalje)

    # --- KLIJENT ---
    else:
        st.title(f"🍴 {st.session_state['user']}")

        st.write("OVO JE TEST - ako ovo vidiš znači radi")

        df = ucitaj_sheet("Meni_Trenutni")

        if not df.empty:
            for dan in dani_std:
                st.write("###", dan)
                jela = df[df["Dan"] == dan]["Jelo"].tolist()

                for j in jela:
                    st.write(j)
                    st.number_input(f"{j}_{dan}", 0, 100)