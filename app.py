import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import re
import time

# --- 1. STILIZACIJA ---
st.set_page_config(page_title="Catering System", layout="centered")

st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    header {visibility: hidden !important; height: 0px !important;}
    footer {display: none !important; visibility: hidden !important;}
    .block-container {padding-top: 1rem !important; background-color: #0E1117;}

    .admin-title { font-size: 1.8rem; font-weight: 800; color: white; margin-bottom: 20px; text-align: center; }
    .status-container { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 15px 0; }
    .status-card { background: #1A1C23; border: 1px solid #333; border-radius: 12px; padding: 12px; text-align: center; }
    .status-f-name { font-size: 0.8rem; color: #999; margin-bottom: 5px; font-weight: 600; text-transform: uppercase; }
    .dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 5px; }
    .dot-green { background-color: #00FF41; box-shadow: 0 0 8px #00FF41; }
    .dot-red { background-color: #FF3131; box-shadow: 0 0 8px #FF3131; }
    .dot-yellow { background-color: #FFD700; box-shadow: 0 0 8px #FFD700; }
    .status-text { font-size: 0.8rem; font-weight: bold; }
    .st-green { color: #00FF41; }
    .st-red { color: #FF3131; }
    .st-yellow { color: #FFD700; }

    .chef-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin-top: 20px; }
    .chef-card { background: linear-gradient(145deg, #1A1C23, #11141C); border: 1px solid #333; border-radius: 20px; padding: 20px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border-bottom: 3px solid #FFD700; }
    .chef-name { color: white; font-size: 1rem; font-weight: bold; margin-bottom: 5px; }
    .chef-rating { color: #FFD700; font-size: 1.3rem; font-weight: 800; text-shadow: 0 0 10px rgba(255, 215, 0, 0.4); }

    .stDownloadButton button { background: linear-gradient(135deg, #E24A4A 0%, #8B0000 100%) !important; color: white !important; border-radius: 10px !important; border: none !important; font-weight: bold !important; padding: 12px !important; width: 100%; text-transform: uppercase; margin-top: 10px; }
    .kuhinja-box { background-color: #161922; border-radius: 15px; padding: 20px; border-left: 5px solid #E24A4A; margin-bottom: 20px; color: white; }
    .jelo-title { background-color: #1A1C23; color: #E24A4A; padding: 10px; border-radius: 5px; font-weight: bold; margin-top: 10px; }
    .row-firma { display: flex; justify-content: space-between; padding: 8px 10px; border-bottom: 1px solid #222; font-size: 0.9rem; }
    .jelo-ukupno { text-align: right; color: #00FF00; font-weight: bold; padding: 10px; }

    /* NOVI IZGLED ZA RESET ZONU */
    .reset-card {
        background: linear-gradient(145deg, #1e1e26, #14141a);
        border: 1px dashed #E24A4A;
        border-radius: 20px;
        padding: 40px 20px;
        text-align: center;
        margin-top: 20px;
    }
    .reset-icon { font-size: 3rem; margin-bottom: 10px; }
    .reset-warning { color: #ff4b4b; font-weight: bold; font-size: 1.2rem; margin-bottom: 5px; }
    .reset-desc { color: #888; font-size: 0.9rem; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. POMOĆNE FUNKCIJE ---
spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)
dani_std = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota"]
sve_firme = ["Lattonedil", "PVA Group", "Esintec", "ActivBH"]
mapa_ocjena = {"Loše": 1, "Može bolje": 2, "Dobro": 3, "Odlično": 4, "Savršeno": 5}
users = {"admin": "admin123", "Lattonedil": "lattonedil321", "PVA Group": "pvagroup321", "Esintec": "esintec321", "ActivBH": "activbh321"}

def ucitaj_sheet(name):
    try: return conn.read(spreadsheet=spreadsheet_url, worksheet=name, ttl=0).dropna(how='all')
    except: return pd.DataFrame()

def izracunaj_prosjeke():
    df_o = ucitaj_sheet("Ocjene")
    if df_o.empty or "Ocjena" not in df_o.columns: return {}, {}
    df_o['Numericka'] = df_o['Ocjena'].map(mapa_ocjena)
    pj = df_o.groupby('Jelo')['Numericka'].mean().round(1).sort_values(ascending=False).to_dict()
    pk = df_o.groupby('Kuvar')['Numericka'].mean().round(1).to_dict() if "Kuvar" in df_o.columns else {}
    return pj, pk

def izvadi_sat_iz_roka(rok_tekst):
    try:
        brojevi = re.findall(r'\d+', str(rok_tekst))
        return int(brojevi[0]) if brojevi else 16
    except: return 16

# --- 3. LOGIN SISTEM ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Prijava</h1>", unsafe_allow_html=True)
    u = st.text_input("Korisnik")
    p = st.text_input("Lozinka", type="password")
    if st.button("Prijavi se", use_container_width=True):
        if u in users and users[u] == p:
            st.session_state["logged_in"], st.session_state["user"] = True, u
            st.rerun()
else:
    if st.session_state["user"] == "admin":
        st.markdown('<div class="admin-title">👨‍🍳 Admin Panel</div>', unsafe_allow_html=True)
        t1, t2, t3, t4 = st.tabs(["📊 Kuhinja", "📝 Meni", "⭐ Ocjene", "🔄 Reset"])
        
        with t1: # KUHINJA (Nepromijenjeno)
            df_nar = ucitaj_sheet("Sheet1")
            df_meni_t = ucitaj_sheet("Meni_Trenutni")
            rok_tekst = df_meni_t[df_meni_t['Dan']=='Rok']['Jelo'].values[0] if not df_meni_t.empty else "16:00"
            sat_limita = izvadi_sat_iz_roka(rok_tekst)
            dan_sel = st.selectbox("Izaberi dan:", dani_std)
            
            st.markdown("### 🕒 Statusi narudžbi")
            status_html = '<div class="status-container">'
            sada = datetime.now() + timedelta(hours=2)
            for f in sve_firme:
                unio = not df_nar[(df_nar['Firma'] == f) & (df_nar['Dan'] == f"Ova-{dan_sel}")].empty if not df_nar.empty else False
                idx = dani_std.index(dan_sel)
                kasni = (idx == sada.weekday() + 1 and sada.hour >= sat_limita) or (idx <= sada.weekday())
                if unio: cls, dot, txt = "st-green", "dot-green", "NARUČENO"
                elif kasni: cls, dot, txt = "st-red", "dot-red", "KASNE"
                else: cls, dot, txt = "st-yellow", "dot-yellow", "ČEKANJE"
                status_html += f'<div class="status-card"><div class="status-f-name">{f}</div><div class="status-text {cls}"><span class="dot {dot}"></span>{txt}</div></div>'
            st.markdown(status_html + '</div>', unsafe_allow_html=True)
            
            if not df_nar.empty:
                dan_data = df_nar[df_nar['Dan'] == f"Ova-{dan_sel}"]
                st.download_button("📥 PREUZMI LISTU ZA ŠTAMPU", data="LISTA", file_name=f"Kuhinja_{dan_sel}.html", use_container_width=True)
                for smj in ["I", "II", "III"]:
                    smj_d = dan_data[dan_data['Smjena'] == smj]
                    if not smj_d.empty:
                        h_box = f'<div class="kuhinja-box"><b>🕒 SMJENA {smj}</b>'
                        for jelo, j_d in smj_d.groupby("Jelo"):
                            h_box += f'<div class="jelo-title">{jelo}</div>'
                            for _, r in j_d.iterrows(): h_box += f'<div class="row-firma"><span>🏢 {r["Firma"]}</span><b>{int(r["Kolicina"])} kom</b></div>'
                            h_box += f'<div class="jelo-ukupno">UKUPNO: {int(j_d["Kolicina"].sum())}</div>'
                        st.markdown(h_box + '</div>', unsafe_allow_html=True)

        with t2: # MENI (Nepromijenjeno)
            od_m = st.radio("Uredi:", ["Meni_Trenutni", "Meni_Naredni"], horizontal=True)
            df_m = ucitaj_sheet(od_m)
            with st.form(f"f_{od_m}"):
                c1, c2, c3 = st.columns(3)
                v_s = df_m[df_m['Dan']=='Sedmica']['Jelo'].values[0] if not df_m.empty and len(df_m[df_m['Dan']=='Sedmica'])>0 else ""
                v_r = df_m[df_m['Dan']=='Rok']['Jelo'].values[0] if not df_m.empty and len(df_m[df_m['Dan']=='Rok'])>0 else "16:00"
                v_k = df_m[df_m['Dan']=='Kuvar']['Jelo'].values[0] if not df_m.empty and len(df_m[df_m['Dan']=='Kuvar'])>0 else ""
                n_s = c1.text_input("Period:", v_s); n_r = c2.text_input("Rok:", v_r); n_k = c3.text_input("Kuvar:", v_k)
                
                novi = [{"Dan": "Sedmica", "Jelo": n_s}, {"Dan": "Rok", "Jelo": n_r}, {"Dan": "Kuvar", "Jelo": n_k}]
                for d in dani_std:
                    st.markdown(f"**{d}**")
                    p_jela = df_m[df_m['Dan']==d]['Jelo'].tolist() if not df_m.empty else []
                    col1, col2, col3 = st.columns(3)
                    for i, col in enumerate([col1, col2, col3]):
                        stara = p_jela[i] if i < len(p_jela) else ""
                        un = col.text_input(f"{d} {i+1}", stara, key=f"{od_m}{d}{i}")
                        if un: novi.append({"Dan": d, "Jelo": un})
                
                if st.form_submit_button("💾 SAČUVAJ"):
                    conn.update(spreadsheet=spreadsheet_url, worksheet=od_m, data=pd.DataFrame(novi))
                    st.success("Sačuvano!"); time.sleep(1); st.rerun()

        with t3: # OCJENE (Nepromijenjeno)
            pj, pk = izracunaj_prosjeke()
            if pj:
                st.subheader("📊 Popularnost jela")
                st.bar_chart(pd.DataFrame(list(pj.items()), columns=['Jelo', 'Ocjena']).set_index('Jelo'))
            if pk:
                st.markdown("### 👨‍🍳 Naši Kuvari")
                c_html = '<div class="chef-container">'
                for ime, oc in pk.items():
                    c_html += f'<div class="chef-card"><div style="color:white; font-weight:bold;">{ime}</div><div class="chef-rating">{oc} ⭐</div></div>'
                st.markdown(c_html + '</div>', unsafe_allow_html=True)

        with t4: # --- NOVI IZGLED ZA RESET ---
            st.markdown(f"""
                <div class="reset-card">
                    <div class="reset-icon">🚀</div>
                    <div class="reset-warning">ROTIRANJE SEDMICE</div>
                    <div class="reset-desc">
                        Ova akcija će postaviti 'Naredni meni' kao 'Trenutni' 
                        i pripremiti sistem za nove narudžbe.
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("POTVRDI I ROTIRAJ ODMAH", use_container_width=True, type="primary"):
                with st.spinner("Rotiram sedmice..."):
                    df_n = ucitaj_sheet("Meni_Naredni")
                    if not df_n.empty:
                        conn.update(spreadsheet=spreadsheet_url, worksheet="Meni_Trenutni", data=df_n)
                        st.balloons()
                        st.success("Uspješno rotirano!"); time.sleep(2); st.rerun()
