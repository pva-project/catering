import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Sistem", layout="centered")
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()

# --- 2. KORISNICI ---
users = {
    "admin": "admin123",
    "Lattonedil": "lattonedil321",
    "PVA Group": "pvagroup321",
    "Esintec": "esintec321",
    "ActivBH": "activbh321"
}

# --- 3. ČITANJE OBA MENIJA ---
try:
    df_trenutni = conn.read(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", ttl=0)
    df_naredni = conn.read(spreadsheet=spreadsheet_url, worksheet="Meni_Naredni", ttl=0)
    
    # Pomoćna funkcija za pretvaranje u rečnik
    def formatiraj(df):
        return {dan: df[df['Dan'] == dan]['Jelo'].tolist() for dan in dani_std if not df[df['Dan'] == dan].empty}

    meni_t = formatiraj(df_trenutni)
    meni_n = formatiraj(df_naredni)
except:
    st.error("Greška: Provjerite listove 'Meni_Trenutni' i 'Meni_Naredni' u Google Tabeli.")
    st.stop()

# --- 4. LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava za Catering</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Korisničko ime")
        p = st.text_input("Lozinka", type="password")
        if st.button("Prijavi se", use_container_width=True):
            if u in users and users[u] == p:
                st.session_state["logged_in"], st.session_state["user"] = True, u
                st.rerun()
            else: st.error("Pogrešni podaci")
else:
    # --- 5. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t_adm1, t_adm2, t_adm3 = st.tabs(["📊 Kuhinja", "📝 Uredi Menije", "⚙️ Reset"])
        
        with t_adm1:
            df_n = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
            if not df_n.empty:
                d_sel = st.selectbox("Izaberi dan:", dani_std)
                # Admin vidi narudžbe za TRENUTNU sedmicu (ono što se kuha)
                prikaz = df_n[df_n['Dan'] == f"Ova-{d_sel}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
                st.table(prikaz)
            else: st.info("Nema narudžbi.")

        with t_adm2:
            st.subheader("📝 Ova Sedmica")
            ed_t = st.data_editor(df_trenutni, use_container_width=True, hide_index=True, key="ed_t")
            if st.button("💾 Sačuvaj Trenutni Meni"):
                conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=ed_t)
                st.success("Trenutni meni ažuriran!")
            
            st.divider()
            
            st.subheader("📝 Naredna Sedmica")
            ed_n = st.data_editor(df_naredni, use_container_width=True, hide_index=True, key="ed_n")
            if st.button("💾 Sačuvaj Naredni Meni"):
                conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Naredni", data=ed_n)
                st.success("Naredni meni ažuriran!")

        with t_adm3:
            if st.button("🗑️ RESETUJ NARUDŽBE (Kraj sedmice)"):
                conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.DataFrame(columns=["Firma","Dan","Jelo","Kolicina","Smjena"]))
                st.success("Sve narudžbe obrisane!")

    # --- 6. KORISNIČKI PANEL ---
    else:
        st.sidebar.button("Odjavi se", on_click=lambda: st.session_state.update({"logged_in": False}))
        st.title(f"🍴 {st.session_state['user']}")
        tab_t, tab_n, tab_h = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna Sedmica", "📜 Istorija"])
        
        try:
            df_sve = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0).dropna(how='all')
            moja_n = df_sve[df_sve['Firma'] == st.session_state['user']]
        except: df_sve, moja_n = pd.DataFrame(), pd.DataFrame()

        def forma(m_dict, prefix, zakljucaj):
            with st.form(f"f_{prefix}"):
                unose = []
                for dan in dani_std:
                    onemoguci = False
                    status = " 🔓"
                    if zakljucaj and danasnji_dan_index <= 5:
                        if danasnji_dan_index >= dani_std.index(dan):
                            onemoguci, status = True, " 🔒"

                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}{status}")
                        jela = m_dict.get(dan, [])
                        for j in jela:
                            st.write(f"**{j}**")
                            c1, c2, c3 = st.columns(3)
                            def get_v(d, jl, s):
                                if not moja_n.empty:
                                    v = moja_n[(moja_n['Dan']==f"{prefix}-{d}") & (moja_n['Jelo']==jl) & (moja_n['Smjena']==s)]['Kolicina'].tolist()
                                    return int(v[0]) if v else 0
                                return 0
                            k1 = c1.number_input("I Smjena", 0, 100, get_v(dan, j, "I"), key=f"{prefix}_{dan}_{j}_1", disabled=onemoguci)
                            k2 = c2.number_input("II Smjena", 0, 100, get_v(dan, j, "II"), key=f"{prefix}_{dan}_{j}_2", disabled=onemoguci)
                            k3 = c3.number_input("III Smjena", 0, 100, get_v(dan, j, "III"), key=f"{prefix}_{dan}_{j}_3", disabled=onemoguci)
                            for k, s in zip([k1, k2, k3], ["I", "II", "III"]):
                                unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": j, "Kolicina": int(k), "Smjena": s})
                
                if st.form_submit_button(f"🚀 SAČUVAJ"):
                    pref_dani = [f"{prefix}-{d}" for d in dani_std]
                    mask = ~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].isin(pref_dani)))
                    final = pd.concat([df_sve[mask] if not df_sve.empty else df_sve, pd.DataFrame([n for n in unose if n['Kolicina']>0])], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=final)
                    st.success("Sačuvano!")
                    st.rerun()

        with tab_t: forma(meni_t, "Ova", True)
        with tab_n: forma(meni_n, "Naredna", False)
        with tab_h: st.dataframe(moja_n, use_container_width=True, hide_index=True)
