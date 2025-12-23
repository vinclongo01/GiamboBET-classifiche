import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Title
st.set_page_config(page_title="Classifiche GiamboBET", layout="centered")


st.logo(
    "./logo/jp.png", 
    #link="https://www.google.com", # redirect link (opzionale)
    size="large" # Opzionale
)

st.title("🏆 Classifiche GiamboBET")

conn = st.connection("gsheets", type=GSheetsConnection)

# Membri
try:
    df_membri = conn.read(worksheet="Membri", ttl=0) # ttl=0 per avere dati sempre freschi
    
    # Dizionario: Nome Cognome -> Tesserato (True/False)
    dict_membri = {}
    for index, row in df_membri.iterrows():
        nome_completo = f"{str(row['Nome']).strip()} {str(row['Cognome']).strip()}"
        is_tesserato = str(row['Tesserato']).strip().upper() == "SI"
        dict_membri[nome_completo] = is_tesserato

except Exception as e:
    st.error(f"Errore nella lettura del foglio Membri: {e}")
    st.stop()

# Funzione per applicare lo stile (Verde/Rosso)
def color_rows(row):
    # Se è tesserato VERDE, altrimenti ROSSO chiaro
    color = '#d4edda' if row['IsTesserato'] else '#f8d7da' 
    # Applica il colore a tutte le celle della riga
    return [f'background-color: {color}; color: black'] * len(row)

# LISTA COMPLETA MEMBRI TESSERATI
with st.expander("👥 Clicca qui per vedere tutti i Membri Tesserati"):
    if not df_membri.empty:
        # 1. Creiamo una copia per lavorare
        df_view_membri = df_membri.copy()

        # 2. Filtra i membri: AGGIUNTO .copy() QUI SOTTO PER RISOLVERE IL WARNING
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
                "Tesserato": None    # Nasconde la colonna
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
            return dict_membri.get(nome_completo, False)


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

        # 3. Style
        styled_df = df.style.apply(color_rows, axis=1)

        # 4. Formattazione finale per Streamlit
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

# --- VISUALIZZAZIONE CLASSIFICHE ---

show_standings("Serie A", "🇮🇹 Classifica Serie A")
st.markdown("---") # Separatore
show_standings("Champions League", "🇪🇺 Classifica Champions League")

# Legenda
st.caption("Legenda: 🟩 Tesserato | 🟥 Non Tesserato")