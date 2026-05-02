import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- CONFIG ---
st.set_page_config(page_title="Catering", layout="wide")

# CLEAN UI + BIG FONT (tablet)
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stToolbar"] {display:none;}

h1 { font-size: 50px !important; }
h2 { font-size: 35px !important; }
p  { font-size: 24px !important; }

.block-container {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()

users = {
    "admin": "admin123",
    "Lattonedil": "lattonedil321",
    "PVA Group": "pvagroup321",
    "Esintec": "esintec321",
    "ActivBH": "activbh321"
}

# --- FUNCTIONS ---
def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# --- LOGIN ---
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
    if st.session_state["user"] == "admin":

        st.title("📺 KUHINJA")

        df_nar = ucitaj_sheet("Sheet1")

        if not df_nar.empty:

            d_sel = st.selectbox("Dan", dani_std)

            df_dan = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"]

            if not df_dan.empty:

                grupa = df_dan.groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
                pivot = grupa.pivot(index="Jelo", columns="Smjena", values="Kolicina").fillna(0)

                pivot["UKUPNO"] = pivot.sum(axis=1)
                pivot = pivot.sort_values("UKUPNO", ascending=False)

                cols = st.columns(2)

                for i, (jelo, row) in enumerate(pivot.iterrows()):
                    with cols[i % 2]:

                        ukupno = int(row["UKUPNO"])

                        # boja po količini
                        if ukupno > 30:
                            boja = "#00ff9f"
                        elif ukupno > 10:
                            boja = "#ffaa00"
                        else:
                            boja = "#ff4444"

                        st.markdown(f"""
                        <div style="
                            background:#1e1e1e;
                            padding:20px;
                            border-radius:20px;
                            margin-bottom:15px;
                        ">
                            <h2>{jelo}</h2>
                            <p>I: {int(row.get('I',0))}</p>
                            <p>II: {int(row.get('II',0))}</p>
                            <p>III: {int(row.get('III',0))}</p>
                            <hr>
                            <h1 style="color:{boja}">UKUPNO: {ukupno}</h1>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("### 📊 Ukupno svih jela")
                st.write(int(pivot["UKUPNO"].sum()))

            else:
                st.info("Nema narudžbi")

        else:
            st.info("Nema podataka")

        # AUTO REFRESH
        time.sleep(10)
        st.rerun()

    else:
        st.title(f"🍴 {st.session_state['user']}")
        st.info("Korisnički panel ostaje kako si već napravio 👍")