import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering", layout="centered")

# CSS ZA POTPUNU KONTROLU MOBILNOG PRIKAZA
st.markdown("""
    <style>
    /* Glavni kontejner za red jela */
    .row-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 5px 0px;
        border-bottom: 1px solid #eee;
        gap: 5px;
    }
    /* Naziv jela - fiksna širina da ne gura ostale */
    .jelo-box {
        width: 45%;
        font-size: 13px;
        font-weight: bold;
        line-height: 1.2;
    }
    /* Kontejner za input polja - fiksna širina */
    .inputs-box {
        display: flex;
        width: 55%;
        justify-content: space-between;
        gap: 2px;
    }
    /* Smanjenje samog input polja */
    .stNumberInput {
        width: 55px !important;
    }
    input {
        padding: 2px !important;
        font-size: 13px !important;
        text-align: center !important;
    }
    /* Sakrivanje viška prostora */
    [data-testid="column"] { width: auto !important; flex: none !important; }
    [data-testid="stHorizontalBlock"] { gap: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_standard = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota", "Nedjelja"]
danasnji_dan_index = datetime.now().weekday()

# --- 2. KORISNICI ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. DINAMIČKI MENI ---
try:
    df_raw = conn.read(spreadsheet=spreadsheet_url, worksheet="Meni", ttl=0)
    df_raw['Dan'] = df_raw['Dan'].str.strip()
    sed_tekst = df_raw[df_raw['Dan'] == 'Sedmica']['Jelo'].values[0] if 'Sedmica' in df_raw['Dan'].values else ""
    rok_tekst = df_raw[df_raw['Dan'] == 'Rok']['Jelo'].values[0] if 'Rok' in df_raw['Dan'].values else ""
    pravi_dani = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
    meni = {d: df_raw[df_raw['Dan'] == d]['Jelo'].tolist() for d in pravi_dani if not df_raw[df_raw['Dan'] == d].empty}
except:
    st.stop()

# --- 4. LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    with st.form("login"):
        u = st.text_input("Korisnik")
        p = st.text_input("Lozinka", type="password")
        if st.form_submit_button("Prijava"):
            if u in users and users[u] == p:
                st.session_state["logged_in"], st.session_state["user"] = True, u
                st.rerun()
else:
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin")
        df_n = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
        if not df_n.empty:
            dan_sel = st.selectbox("Dan:", list(meni.keys()))
            st.table(df_n[df_n['Dan'] == dan_sel].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index())
    else:
        st.title(f"🍴 {st.session_state['user']}")
        st.caption(f"📅 {sed_tekst} | ⏰ {rok_tekst}")
        
        t1, t2 = st.tabs(["🛒 Narudžba", "📜 Istorija"])
        
        try:
            df_sve = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0).dropna(how='all')
            moja_n = df_sve[df_sve['Firma'] == st.session_state['user']]
        except:
            df_sve, moja_n = pd.DataFrame(), pd.DataFrame()

        with t1:
            with st.form("main_form"):
                sve_inpute = []
                for dan, jela in meni.items():
                    idx_dan = dani_standard.index(dan)
                    onemoguci = (danasnji_dan_index <= 5 and danasnji_dan_index >= idx_dan)
                    status = " 🔒" if onemoguci else ""
                    
                    with st.container(border=True):
                        st.markdown(f"**{dan}{status}**")
                        # Zaglavlje za smjene
                        h1, h2, h3, h4 = st.columns([2, 1, 1, 1])
                        h2.caption("I")
                        h3.caption("II")
                        h4.caption("III")
                        
                        for jelo in jela:
                            # Koristimo kolone sa fiksnim omjerom [2, 1, 1, 1] 
                            # što je jedini način da Streamlit NE lomi red na mobitelu
                            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                            
                            c1.markdown(f"<div class='jelo-box'>{jelo}</div>", unsafe_allow_html=True)
                            
                            def get_v(d, j, s):
                                if not moja_n.empty:
                                    f = moja_n[(moja_n['Dan']==d) & (moja_n['Jelo']==j) & (moja_n['Smjena']==s)]
                                    return int(f['Kolicina'].iloc[0]) if not f.empty else 0
                                return 0

                            v1 = c2.number_input("", 0, 100, get_v(dan, jelo, "I"), key=f"{dan}_{jelo}_1", label_visibility="collapsed", disabled=onemoguci)
                            v2 = c3.number_input("", 0, 100, get_v(dan, jelo, "II"), key=f"{dan}_{jelo}_2", label_visibility="collapsed", disabled=onemoguci)
                            v3 = c4.number_input("", 0, 100, get_v(dan, jelo, "III"), key=f"{dan}_{jelo}_3", label_visibility="collapsed", disabled=onemoguci)
                            
                            for v, smj in zip([v1, v2, v3], ["I", "II", "III"]):
                                sve_inpute.append({"Firma": st.session_state['user'], "Dan": dan, "Jelo": jelo, "Kolicina": int(v), "Smjena": smj})
                
                if st.form_submit_button("🚀 POŠALJI NARUDŽBU", use_container_width=True):
                    dani_upis = [d for d in meni.keys() if dani_standard.index(d) > danasnji_dan_index] if danasnji_dan_index <= 5 else list(meni.keys())
                    mask = ~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].isin(dani_upis)))
                    novi = [n for n in sve_inpute if n['Kolicina'] > 0 and n['Dan'] in dani_upis]
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.concat([df_sve[mask], pd.DataFrame(novi)], ignore_index=True))
                    st.success("Sačuvano!")
                    st.rerun()

        with t2:
            st.dataframe(moja_n, use_container_width=True, hide_index=True)

    if st.sidebar.button("Odjava"):
        del st.session_state["logged_in"]
        st.rerun()

