import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA I STILIZACIJA ---
st.set_page_config(page_title="Catering Management", layout="centered")

# Custom CSS za izgled kao na slikama
st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    .stAppDeployButton {display: none !important;}
    .block-container {padding-top: 2rem !important;}
    
    /* Stilovi za info kartice (Period, Rok, Kuvar) */
    .info-card {
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        color: white;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .blue-card { background-color: #1e3a5f; border: 1px solid #3b82f6; }
    .yellow-card { background-color: #3e3e10; border: 1px solid #ca8a04; }
    .green-card { background-color: #143e2a; border: 1px solid #16a34a; }
    </style>
""", unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
danasnji_dan_index = datetime.now().weekday()
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

# --- 2. KORISNICI ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

# --- 3. FUNKCIJE ---
def ucitaj_sheet(sheet_name):
    try:
        df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl=0)
        return df.dropna(how='all')
    except: return pd.DataFrame(columns=["Dan", "Jelo"])

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    p_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    p_kuvari = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return p_jela, p_kuvari

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
    # --- 5. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene & Kuvari", "🔄 Reset"])
        
        with t_a2: # Izmjena Menija (sl3.png)
            st.subheader("Izmijeni jela, rokove i kuvare")
            odabir_m = st.radio("Koji meni mijenjaš?", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(odabir_m)
            
            v_sed = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Sedmica'].empty else ""
            v_rok = df_m[df_m['Dan'] == 'Rok']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Rok'].empty else ""
            v_kuv = df_m[df_m['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Kuvar'].empty else ""

            with st.form(f"form_admin_{odabir_m}"):
                c1, c2, c3 = st.columns(3)
                n_sed = c1.text_input("📅 Period:", value=v_sed)
                n_rok = c2.text_input("⏰ Rok:", value=v_rok)
                n_kuv = c3.text_input("👨‍🍳 Glavni kuvar:", value=v_kuv)
                
                nova_lista = [{"Dan": "Sedmica", "Jelo": n_sed}, {"Dan": "Rok", "Jelo": n_rok}, {"Dan": "Kuvar", "Jelo": n_kuv}]
                for dan in dani_std:
                    st.markdown(f"### {dan}")
                    postojeca = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    for i in range(3):
                        val = postojeca[i] if i < len(postojeca) else ""
                        n_j = st.text_input(f"Jelo {i+1}", value=val, key=f"{dan}_{i}_{odabir_m}")
                        if n_j.strip(): nova_lista.append({"Dan": dan, "Jelo": n_j.strip()})
                
                if st.form_submit_button("💾 SAČUVAJ SVE", use_container_width=True):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=odabir_m, data=pd.DataFrame(nova_lista))
                    st.success("Sačuvano!"); time.sleep(1); st.rerun()

        with t_a3: # Rang lista kuvara (sl2.png)
            st.subheader("⭐ Rang lista kuvara")
            _, p_kuvari = izracunaj_prosjeke()
            if p_kuvari:
                for k, v in p_kuvari.items():
                    st.markdown(f"👨‍🍳 **{k}: {v} ⭐**")
            st.divider()
            st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)

        # (Ostatak Admin panela ostaje isti za Kuhinju i Reset...)

    # --- 6. KORISNIČKI PANEL ---
    else:
        st.markdown(f"# 🍴 {st.session_state['user']}")
        t_t, t_n, t_h, t_o = st.tabs(["🍱 Ova Sedmica", "🚀 Naredna Sedmica", "📜 Istorija", "⭐ Ocijeni"])
        p_jela, _ = izracunaj_prosjeke()

        def prikazi_formu(sheet_name, prefix, zakljucaj):
            df_m = ucitaj_sheet(sheet_name)
            inf_sed = df_m[df_m['Dan'] == 'Sedmica']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Sedmica'].empty else "N/A"
            inf_rok = df_m[df_m['Dan'] == 'Rok']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Rok'].empty else "N/A"
            inf_kuv = df_m[df_m['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m[df_m['Dan'] == 'Kuvar'].empty else "N/A"
            
            # Info kartice kao na sl1.png
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="info-card blue-card">📅 Period: {inf_sed}</div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="info-card yellow-card">⏰ Rok: {inf_rok}</div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="info-card green-card">👨‍🍳 Kuvar: {inf_kuv}</div>', unsafe_allow_html=True)

            df_sve = ucitaj_sheet("Sheet1")
            with st.form(f"f_{prefix}"):
                unose = []
                for dan in dani_std:
                    idx = dani_std.index(dan)
                    onemoguci = (zakljucaj and danasnji_dan_index <= 5 and danasnji_dan_index >= idx)
                    status_icon = "🔒" if onemoguci else "🔓"
                    
                    with st.container(border=True):
                        st.markdown(f"#### 📅 {dan} {status_icon}")
                        jela = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                        for j in jela:
                            prosjek = p_jela.get(j, None)
                            star_text = f"(⭐ {prosjek})" if prosjek else "(🆕)"
                            st.write(f"**{j}** {star_text}")
                            
                            col1, col2, col3 = st.columns(3)
                            # Logika za dobijanje trenutnih vrijednosti iz Sheet1
                            mask = (df_sve['Firma']==st.session_state['user']) & (df_sve['Dan']==f"{prefix}-{dan}") & (df_sve['Jelo']==j)
                            v1 = df_sve[mask & (df_sve['Smjena']=="I")]['Kolicina'].sum() if not df_sve.empty else 0
                            v2 = df_sve[mask & (df_sve['Smjena']=="II")]['Kolicina'].sum() if not df_sve.empty else 0
                            v3 = df_sve[mask & (df_sve['Smjena']=="III")]['Kolicina'].sum() if not df_sve.empty else 0
                            
                            k1 = col1.number_input("I Smjena", 0, 100, int(v1), key=f"{prefix}_{dan}_{j}_1", disabled=onemoguci)
                            k2 = col2.number_input("II Smjena", 0, 100, int(v2), key=f"{prefix}_{dan}_{j}_2", disabled=onemoguci)
                            k3 = col3.number_input("III Smjena", 0, 100, int(v3), key=f"{prefix}_{dan}_{j}_3", disabled=onemoguci)
                            
                            for k, s in zip([k1, k2, k3], ["I", "II", "III"]):
                                if k > 0: unose.append({"Firma": st.session_state['user'], "Dan": f"{prefix}-{dan}", "Jelo": j, "Kolicina": int(k), "Smjena": s})
                
                if st.form_submit_button("🚀 SAČUVAJ NARUDŽBU", use_container_width=True):
                    mask_del = ~((df_sve['Firma'] == st.session_state['user']) & (df_sve['Dan'].str.startswith(prefix)))
                    final = pd.concat([df_sve[mask_del], pd.DataFrame(unose)], ignore_index=True)
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Sheet1", data=final)
                    st.success("Spremljeno!"); st.balloons(); time.sleep(1); st.rerun()

        with t_t: prikazi_formu("Meni_Trenutni", "Ova", True)
        with t_n: prikazi_formu("Meni_Naredni", "Naredna", False)
        with t_o: # Ocjenjivanje (sl2.png logika)
            st.subheader("⭐ Ocijeni obrok")
            df_m_t = ucitaj_sheet("Meni_Trenutni")
            kuv_tren = df_m_t[df_m_t['Dan'] == 'Kuvar']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar'].empty else "N/A"
            sva_j = df_m_t[df_m_t['Dan'].isin(dani_std)]['Jelo'].unique().tolist()
            with st.form("forma_ocjena", clear_on_submit=True):
                od_j = st.selectbox("Jelo:", sva_j)
                ocj = st.select_slider("Ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"], value="Odlično")
                kom = st.text_area("Komentar:")
                if st.form_submit_button("📩 Pošalji"):
                    df_o_p = ucitaj_sheet("Ocjene")
                    nova_o = pd.DataFrame([{"Firma": st.session_state['user'], "Jelo": od_j, "Ocjena": ocj, "Komentar": kom, "Kuvar": kuv_tren}])
                    conn.update(spreadsheet=spreadsheet_url, worksheet="Ocjene", data=pd.concat([df_o_p, nova_o], ignore_index=True))
                    st.success("Hvala!"); time.sleep(1); st.rerun()
