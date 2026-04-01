import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Classifiche GiamboBET", layout="centered")
st.logo("./logo/jp.png", size="large")

st.markdown("""
<style>
/* ── Brand palette ─────────────────────────────────────
   Pink  : #F07B9B
   Gold  : #C9A227
   Dark  : #141414
   Card  : #1E1E1E
   Border: #2E2E2E
───────────────────────────────────────────────────── */

/* Page background */
.stApp, [data-testid="stAppViewContainer"] {
    background-color: #141414;
    color: #F0F0F0;
}
[data-testid="stHeader"] {
    background-color: #141414;
}
[data-testid="stSidebar"] {
    background-color: #1E1E1E;
}

/* Main title */
h1 {
    color: #F07B9B !important;
    font-size: 2.4rem !important;
    font-weight: 900 !important;
    letter-spacing: 3px !important;
    text-transform: uppercase;
    text-shadow: 0 0 24px rgba(240,123,155,0.35);
    padding-bottom: 0.25rem;
}

/* Subheadings */
h2, h3 {
    color: #C9A227 !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase;
}

/* Dividers */
hr {
    border: none !important;
    border-top: 2px solid #F07B9B !important;
    opacity: 0.3;
    margin: 1.5rem 0 !important;
}

/* Buttons */
.stButton > button {
    background-color: #1E1E1E !important;
    color: #F07B9B !important;
    border: 2px solid #F07B9B !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase;
    transition: all 0.15s ease !important;
}
.stButton > button:hover, .stButton > button:focus {
    background-color: #F07B9B !important;
    color: #141414 !important;
    box-shadow: 0 0 14px rgba(240,123,155,0.5) !important;
}

/* Expander */
[data-testid="stExpander"] {
    background-color: #1E1E1E !important;
    border: 1px solid #2E2E2E !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    color: #F07B9B !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
}

/* Dataframe container */
[data-testid="stDataFrame"] {
    border: 1px solid #2E2E2E !important;
    border-radius: 8px !important;
    overflow: hidden;
}

/* Alert / toast messages */
[data-testid="stAlert"] {
    border-radius: 6px !important;
}

/* Caption */
[data-testid="stCaptionContainer"] {
    color: #888 !important;
    letter-spacing: 0.5px;
}
</style>
""", unsafe_allow_html=True)

st.title("🏆 Classifiche GiamboBET")

conn = st.connection("gsheets", type=GSheetsConnection)


def get_full_name(row):
    return f"{str(row['Nome']).strip()} {str(row['Cognome']).strip()}"


try:
    df_membri = conn.read(worksheet="Membri", ttl="10m")

    dict_tesserati = {}
    id2NomeCognome = {}
    for _, row in df_membri.iterrows():
        nome_completo = get_full_name(row)
        dict_tesserati[nome_completo] = str(row['Tesserato']).strip().upper() == "SI"
        id2NomeCognome[row['ID']] = nome_completo

except Exception as e:
    st.error(f"Errore nella lettura del foglio Membri: {e}")
    st.stop()


id_scansionato = st.query_params.get("uid", None)
nome_utente_scansionato = None

if id_scansionato:
    nome_utente_scansionato = id2NomeCognome.get(id_scansionato)
    if nome_utente_scansionato:
        if dict_tesserati.get(nome_utente_scansionato, False):
            st.success(f"👋 Ciao **{nome_utente_scansionato}**! I tuoi risultati sono evidenziati in ORO.")
        else:
            st.warning(f"👋 Ciao **{nome_utente_scansionato}**! Sei **NON TESSERATO**. I tuoi risultati sono evidenziati in ORO, ma non potrai essere classificato.")
            st.info("Per essere TESSERATO, invia 5€ sul conto paypal clubjuporn@gmail.com.")
    else:
        st.warning(f"ID {id_scansionato} non trovato nel sistema.")


def color_rows(row):
    nome_riga = get_full_name(row)
    if nome_utente_scansionato and nome_riga.lower() == nome_utente_scansionato.lower():
        return ['background-color: #C9A227; color: #141414; font-weight: bold; border-bottom: 2px solid #F07B9B'] * len(row)
    elif dict_tesserati.get(nome_riga, False):
        return ['background-color: #2A1A22; color: #F5A0B8'] * len(row)
    else:
        return ['background-color: #1A1A1A; color: #666666'] * len(row)


def add_tesserato_column(df):
    df = df.copy()
    df['IsTesserato'] = df.apply(get_full_name, axis=1).map(lambda n: dict_tesserati.get(n, False))
    return df


def compute_pos(df):
    df = df.sort_values(by=['Punti'], ascending=False).copy()
    df.insert(0, 'Pos', "")
    pos = 1
    old_points = None
    for i in range(len(df)):
        if df.iloc[i]['IsTesserato']:
            points = df.iloc[i]['Punti']
            if old_points is not None and points != old_points:
                pos += 1
            old_points = points
            df.at[df.index[i], 'Pos'] = f"{pos} 🏆" if pos == 1 else f"{pos}"
        else:
            df.at[df.index[i], 'Pos'] = 'N.C.'
    return df


with st.expander("👥 Clicca qui per vedere tutti i Membri Tesserati"):
    if not df_membri.empty:
        df_tesserati = df_membri[
            df_membri['Tesserato'].astype(str).str.strip().str.upper() == "SI"
        ].sort_values(by=['Cognome', 'Nome']).reset_index(drop=True)
        df_tesserati = add_tesserato_column(df_tesserati)
        st.dataframe(
            df_tesserati.style.apply(color_rows, axis=1),
            hide_index=True,
            width="stretch",
            column_config={
                "IsTesserato": None,
                "Tesserato": None,
                "ID": None,
                "Tipo di tessera": None
            }
        )
    else:
        st.warning("Lista membri vuota.")

st.markdown("---")


def show_standings(df, title):
    st.subheader(title)
    try:
        if df.empty:
            st.warning("Nessun dato trovato.")
            return

        df = add_tesserato_column(df)
        df = compute_pos(df)

        st.dataframe(
            df.style.apply(color_rows, axis=1),
            hide_index=True,
            width="stretch",
            column_config={
                "IsTesserato": None,
                "Punti": st.column_config.NumberColumn("Punti", format="%d")
            }
        )
    except Exception as e:
        st.error(f"Errore nel caricamento di {title}: {e}")


try:
    df_girone_andata = conn.read(worksheet="Classifica Girone di Andata", ttl="10m")
    df_girone_ritorno = conn.read(worksheet="Classifica Girone di Ritorno", ttl="10m")
    df_champions = conn.read(worksheet="Champions League", ttl="10m")
except Exception as e:
    st.error(f"Errore nella lettura delle classifiche: {e}")
    st.stop()


def compute_general_standings(df1, df2):
    df_general = pd.merge(
        df1[['Nome', 'Cognome', 'Punti']],
        df2[['Nome', 'Cognome', 'Punti']],
        on=['Nome', 'Cognome'],
        how='outer',
        suffixes=('_andata', '_ritorno')
    ).fillna(0)
    df_general['Punti'] = df_general['Punti_andata'] + df_general['Punti_ritorno']
    return df_general[['Nome', 'Cognome', 'Punti']]


df_general = compute_general_standings(df_girone_andata, df_girone_ritorno)

if "classifica_scelta" not in st.session_state:
    st.session_state.classifica_scelta = "generale"

st.subheader("Classifiche Serie A:")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📥 Andata", use_container_width=True, key="btn_andata"):
        st.session_state.classifica_scelta = "andata"
with col2:
    if st.button("📤 Ritorno", use_container_width=True, key="btn_ritorno"):
        st.session_state.classifica_scelta = "ritorno"
with col3:
    if st.button("🏅 Generale", use_container_width=True, key="btn_generale"):
        st.session_state.classifica_scelta = "generale"

if st.session_state.classifica_scelta == "andata":
    show_standings(df_girone_andata, "🇮🇹 Classifica Girone di Andata Serie A")
elif st.session_state.classifica_scelta == "ritorno":
    show_standings(df_girone_ritorno, "🇮🇹 Classifica Girone di Ritorno Serie A")
else:
    show_standings(df_general, "🇮🇹 Classifica Generale Serie A")

st.markdown("---")
show_standings(df_champions, "🇪🇺 Classifica Champions League")
st.caption("Legenda: 🌸 Tesserato | ⬛ Non Tesserato | 🥇 Tu")
