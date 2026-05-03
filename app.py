import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time

# --- POMOĆNE FUNKCIJE ---
def renderuj_zvezdice(ocjena):
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

# Funkcija za analizu ocjena - povezuje jela sa kuvarom
def analiziraj_kuvare(k1_ime, k2_ime):
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns:
        return {}, 0.0, 0.0
    
    mapa = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa)
    
    # Prosjek po jelima za Kuhinju
    prosjeci_jela = df_o.groupby('Jelo')['Numericka'].mean().round(1).to_dict()
    
    # Računanje prosjeka kuvara filtriranjem kolone 'Kuvar'
    k1_skor = df_o[df_o['Kuvar'] == k1_ime]['Numericka'].mean() if 'Kuvar' in df_o.columns else 0.0
    k2_skor = df_o[df_o['Kuvar'] == k2_ime]['Numericka'].mean() if 'Kuvar' in df_o.columns else 0.0
    
    return prosjeci_jela, round(pd.Series(k1_skor).fillna(0).iloc[0], 1), round(pd.Series(k2_skor).fillna(0).iloc[0], 1)

# --- LOGIKA APLIKACIJE ---
df_m_t = ucitaj_sheet("Meni_Trenutni")

# Automatsko povlačenje imena glavnih kuvara iz Menija
k1_ime = df_m_t[df_m_t['Dan'] == 'Kuvar 1']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 1'].empty else "N/A"
k2_ime = df_m_t[df_m_t['Dan'] == 'Kuvar 2']['Jelo'].values[0] if not df_m_t[df_m_t['Dan'] == 'Kuvar 2'].empty else "N/A"

prosjeci_jela, skor_k1, skor_k2 = analiziraj_kuvare(k1_ime, k2_ime)

# --- KLIJENTSKI DIO (AUTOMATSKO DODJELJIVANJE KUVARA) ---
if st.session_state["user"] != "admin":
    with st.form("f_ocena"):
        st.subheader("Ocijeni obrok")
        j_izbor = st.selectbox("Izaberi jelo koje si jeo:", jela_za_danas)
        ocj = st.select_slider("Tvoja ocjena:", options=["Loše", "Može bolje", "Dobro", "Odlično", "Savršeno"])
        
        # FIX: Sistem sam zna ko je kuvar za ovo jelo/sedmicu
        # Ovdje možete dodati logiku da li jelo sprema Kuvar 1 ili Kuvar 2
        trenutni_kuvar = k1_ime 
        
        if st.form_submit_button("Pošalji ocjenu"):
            nova_ocjena = {
                "Firma": st.session_state['user'],
                "Jelo": j_izbor,
                "Ocjena": ocj,
                "Kuvar": trenutni_kuvar, # Ovo omogućava da Admin vidi prosjek
                "Datum": datetime.now().strftime("%d.%m.%Y")
            }
            # Slanje u bazu...

# --- ADMIN PANEL PRIKAZ ---
with t_a3: # Tab Ocjene
    st.subheader("📊 Rang lista glavnih kuvara")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{k1_ime}**")
        st.markdown(renderuj_zvezdice(skor_k1), unsafe_allow_html=True)
    with c2:
        st.markdown(f"**{k2_ime}**")
        st.markdown(renderuj_zvezdice(skor_k2), unsafe_allow_html=True)
    
    st.divider()
    st.dataframe(ucitaj_sheet("Ocjene"), use_container_width=True, hide_index=True)
