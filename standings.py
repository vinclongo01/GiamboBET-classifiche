import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Title
st.set_page_config(page_title="Classifiche GiamboBET", layout="centered")

# Set Logo
st.logo(
    "./logo/jp.png", 
    #link="https://www.google.com", # redirect link (opzionale)
    size="large" # Opzionale
)

# Title
st.title("🏆 Classifiche GiamboBET")

# Connessione a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Membri
try:
    # Leggiamo i Membri del Gruppo
    df_membri = conn.read(worksheet="Membri", ttl="10m") # cache per 10 minuti
    
    # Dizionario: Nome Cognome -> Tesserato (True/False)
    dict_tesserati = {}
    for index, row in df_membri.iterrows():
        nome_completo = f"{str(row['Nome']).strip()} {str(row['Cognome']).strip()}"
        is_tesserato = str(row['Tesserato']).strip().upper() == "SI"
        dict_tesserati[nome_completo] = is_tesserato

    # id2NomeCognome
    id2NomeCognome = {}
    for index, row in df_membri.iterrows():
        id2NomeCognome[row['ID']] = f"{str(row['Nome']).strip()} {str(row['Cognome']).strip()}"
    
    # NomeCognome2id
    NomeCognome2id = {id2NomeCognome[k]: k for k in id2NomeCognome}

except Exception as e:
    st.error(f"Errore nella lettura del foglio Membri: {e}")
    st.stop()


# Link accetta il parametro uid nell'URL
query_params = st.query_params
id_scansionato = query_params.get("uid", None)
nome_utente_scansionato = None

if id_scansionato:
    # Cerchiamo l'ID nel dizionario
    nome_utente_scansionato = id2NomeCognome.get(id_scansionato)
    
    
    if nome_utente_scansionato:
        is_user_tesserato = dict_tesserati.get(nome_utente_scansionato, False)
        if is_user_tesserato:
            st.success(f"👋 Ciao **{nome_utente_scansionato}**! I tuoi risultati sono evidenziati in ORO.")
        else:
            st.warning(f"👋 Ciao **{nome_utente_scansionato}**! Sei **NON TESSERATO**. I tuoi risultati sono evidenziati in ORO, ma non potrai essere classificato.")
            st.info("Per essere TESSERATO, invia 5€ sul conto paypal clubjuporn@gmail.com.")
    else:
        st.warning(f"ID {id_scansionato} non trovato nel sistema.")


# Funzione per applicare lo stile (Verde/Rosso)
def color_rows(row):
    nome_riga = f"{str(row['Nome']).strip()} {str(row['Cognome']).strip()}"
    
    # Verifica se la riga corrente corrisponde all'utente scansionato
    is_selected = False
    if nome_utente_scansionato and nome_riga.lower() == nome_utente_scansionato.lower():
        is_selected = True

    if is_selected:
        # ORO per l'utente del QR
        return ['background-color: #FFD700; color: black; font-weight: bold; border: 2px solid red'] * len(row)
    
    # Controllo Tesserato usando il dizionario
    elif dict_tesserati.get(nome_riga, False): 
        # VERDE
        return ['background-color: #d4edda; color: black'] * len(row)
    else:
        # ROSSO
        return ['background-color: #f8d7da; color: black'] * len(row)

# 1. Visualizza lista Membri Tesserati
with st.expander("👥 Clicca qui per vedere tutti i Membri Tesserati"):
    if not df_membri.empty:
        # 1. Creiamo una copia per lavorare
        df_view_membri = df_membri.copy()

        # 2. Filtra i membri
        df_tesserati = df_view_membri[
            df_view_membri['Tesserato'].astype(str).str.strip().str.upper() == "SI"
        ].sort_values(by=['Cognome', 'Nome']).reset_index(drop=True).copy()
        
        # 3. Ora puoi modificare df_tesserati senza errori
        # Dato che abbiamo già filtrato solo i "SI", questa colonna sarà tutta True
        df_tesserati['IsTesserato'] = True 
        
        # 4. Applichiamo lo stile
        st.dataframe(
            df_tesserati.style.apply(color_rows, axis=1),
            hide_index=True,
            width="stretch",
            column_config={
                "IsTesserato": None, # Nasconde la colonna
                "Tesserato": None,    # Nasconde la colonna
                "ID": None          # Nasconde la colonna
            }
        )
    else:
        st.warning("Lista membri vuota.")

st.markdown("---")

# Funzione helper per caricare e mostrare le classifiche
def show_standings(worksheet_name, title):
    st.subheader(title)
    try:
        df = conn.read(worksheet=worksheet_name, ttl=0)
        
        if df.empty:
            st.warning("Nessun dato trovato.")
            return


        # Check Tesserato status
        def check_tesserato(row):
            nome_completo = f"{str(row['Nome']).strip()} {str(row['Cognome']).strip()}"
            return dict_tesserati.get(nome_completo, False)


        df['IsTesserato'] = df.apply(check_tesserato, axis=1)


        def compute_pos(df):
            df = df.sort_values(by=['Punti'], ascending=[False])
            df.insert(0, 'Pos', "")
            pos = 1
            for i in range(len(df)):
                # se tesserato, assegna posizione
                if df.iloc[i]['IsTesserato']:
                    df.at[df.index[i], 'Pos'] = f"{pos} 🏆" if pos == 1 else f"{pos}"
                    pos += 1
                else:
                    # N.C., i.e., Non Classificato
                    df.at[df.index[i], 'Pos'] = 'N.C.'
                
            
            return df
        
        df = compute_pos(df)

        # Style
        styled_df = df.style.apply(color_rows, axis=1)

        # Formattazione finale per Streamlit

        # Nascondiamo l'indice fastidioso e la colonna 'IsTesserato' che serve solo per il colore
        st.dataframe(
            styled_df,
            hide_index=True,
            width="stretch",
            column_config={
                "IsTesserato": None, # Nasconde la colonna
                #"Pos": st.column_config.NumberColumn("Pos", format="%d"),
                "Punti": st.column_config.NumberColumn("Punti", format="%d")
            }
        )
    except Exception as e:
        st.error(f"Errore nel caricamento di {title}: {e}")

# 2. Mostra le classifiche

show_standings("Serie A", "🇮🇹 Classifica Serie A")
st.markdown("---") # Separatore
show_standings("Champions League", "🇪🇺 Classifica Champions League")

# Legenda
st.caption("Legenda: 🟩 Tesserato | 🟥 Non Tesserato")