import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. KONFIGURACIJA ---
st.set_page_config(page_title="Catering Management", layout="centered")
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()

# --- 2. KORISNICI ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. FUNKCIJE ---
def ucitaj_meni_komplet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except:
        return pd.DataFrame(columns=["Dan", "Jelo"])

# --- 4. LOGIN ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

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
    st.sidebar.write(f"Korisnik: **{st.session_state['user']}**")
    if st.sidebar.button("Odjavi se", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- 5. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t1, t2, t3 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "🔄 Kraj Sedmice"])
        
        with t2:
            st.subheader("Izmijeni jela i rokove")
            odabir_m = st.radio("Koji meni mijenjaš?", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_meni_komplet(odabir_m)
            
            v_sedmica = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values[0] if 'Sedmica' in df_m['Dan'].values else ""
            v_rok = df_m[df_m['Dan'] == 'Rok']['Jelo'].values[0] if 'Rok' in df_m['Dan'].values else ""

            with st.form(f"form_admin_{odabir_m}"):
                c_a, c_b = st.columns(2)
                novo_sedmica = c_a.text_input("📅 Period (npr. 04.05-10.05):", value=v_sedmica)
                novo_rok = c_b.text_input("⏰ Rok (npr. Nedjelja 20h):", value=v_rok)
                
                nova_lista = [{"Dan": "Sedmica", "Jelo": novo_sedmica}, {"Dan": "Rok", "Jelo": novo_rok}]
                for dan in dani_std:
                    st.write(f"**{dan}**")
                    postojeca = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    j1 = st.text_input(f"Jelo 1", value=postojeca[0] if len(postojeca) > 0 else "", key=f"{dan}_1")
                    j2 = st.text_input(f"Jelo 2", value=postojeca[1] if len(postojeca) > 1 else "", key=f"{dan}_2")
                    j3 = st.text_input(f"Jelo 3", value=postojeca[2] if len(postojeca) > 2 else "", key=f"{dan}_3")
                    for j in [j1, j2, j3]:
                        if j.strip(): nova_lista.append({"Dan": dan, "Jelo": j.strip()})
                
                if st.form_submit_button("💾 SAČUVAJ SVE IZMJENE"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=odabir_m, data=pd.DataFrame(nova_lista))
                    st.success("Sačuvano!")
                    st.rerun()

        with t1:
            df_nar = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
            if not df_nar.empty:
                d_sel = st.selectbox("Dan za kuhanje:", dani_std)
                prikaz = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"].groupby(['Jelo', 'Smjena'])['Kolicina'].sum().reset_index()
                st.table(prikaz)
            else: st.info("Nema narudžbi.")

        with t3:
            if st.button("🚀 IZVRŠI ROTACIJU (Naredna -> Trenutna)"):
                df_next = ucitaj_meni_komplet("Meni_Naredni")
                conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_next)
                conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=pd.DataFrame(columns=["Firma","Dan","Jelo","Kolicina","Smjena"]))
                st.success("Rotirano i resetovano!")
                st.rerun()

    # --- 6. KORISNIČKI PANEL ---
    else:
        st.title(f"🍴 {st.session_state['user']}")
        t_t, t_n, t_h = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna Sedmica", "📜 Istorija"])
        
        def prikazi_formu(sheet_name, prefix, zakljucaj):
            df_m = ucitaj_meni_komplet(sheet_name)
            info_sed = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values[0] if 'Sedmica' in df_m['Dan'].values else "N/A"
            info_rok = df_m[df_m['Dan'] == 'Rok']['Jelo'].values[0] if 'Rok' in df_m['Dan'].values else "N/A"
            
            c1, c2 = st.columns(2)
            c1.info(f"📅 **Period:** {info_sed}")
            c2.warning(f"⏰ **Rok:** {info_rok}")

            try:
                df_sve = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0).dropna(how='all')
                moja_n = df_sve[df_sve['Firma'] == st.session_state['user']]
            except: 
                df_sve = pd.DataFrame(columns=["Firma", "Dan", "Jelo", "Kolicina", "Smjena"])
                moja_n = pd.DataFrame()

            with st.form(f"f_{prefix}"):
                unose = []
                for dan in dani_std:
                    onemoguci = False
                    status = " 🔓"
                    if zakljucaj and danasnji_dan_index <= 5:
                        if danasnji_dan_index >= dani_std.index(dan): onemoguci, status = True, " 🔒"

                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan}{status}")
                        jela = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                        for j in jela:
                            st.write(f"**{j}**")
                            col1, col2, col3 = st.columns(3)
                            def get_v(d, jl, s):
                                if not moja_n.empty:
                                    v = moja_n[(moja_n['Dan']==f"{prefix}-{d}") & (moja_n['Jelo']==jl) & (moja_n['Smjena']==s)]['Kolicina'].tolist()
                                    return int(v[0]) if v else 0
                                return 0
                            k1 = col1.number_input("I Smjena", 0, 100, get_v(dan, j, "I"), key=f"{prefix}_{dan}_{j}_1", disabled=onemoguci)
                            k2 = col2.number_input("II Smjena", 0, 100, get_v(dan, j, "II"), key=f"{prefix}_{dan}_{j}_2", disabled=onemoguci)
                            k3 = col3.number_input("III Smjena", 0, 100, get_v(dan, j, "III"), key=f"{prefix}_{dan}_{j}_3", disabled=onemoguci)
                            for k, s in zip([k1, k2, k3], ["I", "II", "III"]):
                                unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": j, "Kolicina": int(k), "Smjena": s})
                
                if st.form_submit_button("🚀 SAČUVAJ NARUDŽBU", use_container_width=True):
                    # POPRAVKA: Pretvaranje kolone Dan u string pre pretrage
                    df_sve['Dan'] = df_sve['Dan'].astype(str)
                    mask = ~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))
                    final = pd.concat([df_sve[mask], pd.DataFrame([n for n in unose if n['Kolicina']>0])], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=final)
                    st.success("Uspješno sačuvano!")
                    st.rerun()

        with t_t: prikazi_formu("Meni_Trenutni", "Ova", True)
        with t_n: prikazi_formu("Meni_Naredni", "Naredna", False)
        with t_h: 
            try:
                curr_df = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1", ttl=0)
                st.dataframe(curr_df[curr_df['Firma'] == st.session_state['user']], use_container_width=True, hide_index=True)
            except: st.info("Nema narudžbi.")
