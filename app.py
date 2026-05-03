import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURACIJA I STIL ---
st.set_page_config(page_title="Catering Management", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"], header, footer {display: none !important;}
    .block-container {padding-top: 1rem !important;}
    .star-ratings { color: #ccc; position: relative; display: inline-block; font-size: 20px; }
    .star-ratings-fill { color: #ffca08; padding: 0; position: absolute; z-index: 1; display: block; top: 0; left: 0; overflow: hidden; white-space: nowrap; }
    </style>
""", unsafe_allow_html=True)

spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}

# --- 2. FUNKCIJE ---
def prikazi_zvjezdice(ocjena):
    procenat = (ocjena / 5) * 100
    return f"""
    <div style="display: inline-block; vertical-align: middle;">
        <span style="font-weight: bold; font-size: 1.1rem; margin-right: 8px;">{ocjena}</span>
        <div class="star-ratings">
            <div class="star-ratings-fill" style="width: {procenat}%;"><span>★★★★★</span></div>
            <div><span>★★★★★</span></div>
        </div>
    </div>
    """

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

# --- 3. LOGIN ---
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}
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
else:
    # --- 4. ADMIN PANEL ---
    if st.session_state["user"] == "admin":
        st.title("👨‍🍳 Admin Upravljanje")
        t_a1, t_a2, t_a3, t_a4 = st.tabs(["📊 Kuhinja", "📝 Izmjena Menija", "⭐ Ocjene", "🔄 Reset"])
        
        df_m_t = ucitaj_sheet("Meni_Trenutni")
        p_jela, p_kuvari = izracunaj_prosjeke()

        # Povlačenje oba kuvara
        k1_ime = df_m_t[df_m_t['Dan'] == 'Kuvar 1']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 1'].empty else "N/A"
        k2_ime = df_m_t[df_m_t['Dan'] == 'Kuvar 2']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 2'].empty else "N/A"

        with t_a1: # KUHINJA
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Glavni kuvar 1: {k1_ime}**")
                    st.markdown(prikazi_zvjezdice(p_kuvari.get(k1_ime, 0.0)), unsafe_allow_html=True)
                with c2:
                    st.write(f"**Glavni kuvar 2: {k2_ime}**")
                    st.markdown(prikazi_zvjezdice(p_kuvari.get(k2_ime, 0.0)), unsafe_allow_html=True)

            df_nar = ucitaj_sheet("Sheet1")
            if not df_nar.empty:
                d_sel = st.selectbox("Dan za kuhanje:", dani_std)
                prikaz = df_nar[df_nar['Dan'] == f"Ova-{d_sel}"]
                for smjena in ["I", "II", "III"]:
                    sm_data = prikaz[prikaz['Smjena'] == smjena]
                    if not sm_data.empty:
                        with st.container(border=True):
                            st.subheader(f"🕒 SMJENA {smjena}")
                            for jelo, j_data in sm_data.groupby("Jelo"):
                                r = p_jela.get(jelo, "0.0")
                                st.markdown(f"<div style='background:#1E1E1E;padding:8px;border-radius:5px;'><b>{jelo}</b> ⭐ {r}</div>", unsafe_allow_html=True)
                                for _, row in j_data.iterrows():
                                    st.write(f"🏢 {row['Firma']}: {int(row['Kolicina'])} kom")
                                st.success(f"Ukupno: {int(j_data['Kolicina'].sum())}")

        with t_a2: # IZMJENA MENIJA
            odabir_m = st.radio("Meni:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(odabir_m)
            with st.form(f"form_{odabir_m}"):
                novi = []
                # Izmjena za dva kuvara
                for meta in ["Sedmica", "Rok", "Kuvar 1", "Kuvar 2"]:
                    v = df_m[df_m['Dan'] == meta]['Jelo'].values[0] if not df_m[df_m['Dan'] == meta].empty else ""
                    nv = st.text_input(f"{meta}:", value=v)
                    novi.append({"Dan": meta, "Jelo": nv})
                st.divider()
                for dan in dani_std:
                    st.write(f"**{dan}**")
                    postojeca = df_m[df_m['Dan'] == dan]['Jelo'].tolist()
                    for i in range(3):
                        val = postojeca[i] if i < len(postojeca) else ""
                        nj = st.text_input(f"{dan} {i+1}", value=val, key=f"{dan}_{i}_{odabir_m}")
                        if nj: novi.append({"Dan": dan, "Jelo": nj})
                if st.form_submit_button("💾 Sačuvaj"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=odabir_m, data=pd.DataFrame(novi))
                    st.rerun()

        with t_a3: # OCJENE
            st.subheader("⭐ Rang lista")
            col_k1, col_k2 = st.columns(2)
            col_k1.markdown(f"**{k1_ime}**\n{prikazi_zvjezdice(p_kuvari.get(k1_ime, 0.0))}", unsafe_allow_html=True)
            col_k2.markdown(f"**{k2_ime}**\n{prikazi_zvjezdice(p_kuvari.get(k2_ime, 0.0))}", unsafe_allow_html=True)
            st.divider()
            st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)

    # --- 5. KLIJENT PANEL (Ostaje isti kao tvoj, samo dodajemo Kuvar 1/2 u ocjenu) ---
    else:
        # ... tvoj kod za naručivanje ...
        with st.form("forma_ocjena"):
            # Kod za ocjenjivanje treba da šalje k1_ime ili k2_ime u kolonu "Kuvar"
            # na osnovu toga ko je pravio to jelo
            pass
