import streamlit as st
import pandas as pd
import os
from datetime import datetime
from scraper import VoituresScraper, MotosScraper, EquipementsScraper
import plotly.express as px


# Configuration des chemins (déclaration globale)
DATA_RAW = "data/raw"
DATA_CLEANED = "data/cleaned"

# Création des répertoires (exécuté au chargement)
os.makedirs(DATA_RAW, exist_ok=True)
os.makedirs(DATA_CLEANED, exist_ok=True)

def get_scraper(category):
    scrapers = {
        "Voitures": VoituresScraper,
        "Motos": MotosScraper,
        "Équipements et pièces": EquipementsScraper
    }
    return scrapers[category]()  # Appel sans paramètre maintenant

def main():
    st.set_page_config(page_title="Expat Dakar", page_icon="🏍️", layout="wide")
    
    st.sidebar.title("Navigation")
    menu = st.sidebar.radio("", ["Scraping", "Téléchargement", "Dashboard", "Évaluation"])

    if menu == "Scraping":
        st.title("Scraping des données")
        col1, col2 = st.columns([1, 2])

        with col1:
            category = st.selectbox("Catégorie", ["Voitures", "Motos", "Équipements et pièces"])
            pages = st.slider("Nombre de pages", 1, 50, 3)

            if st.button("Lancer le scraping"):
                scraper = get_scraper(category)
                with st.spinner("Scraping en cours..."):
                    try:
                        df = scraper.scrape(pages=pages)
                        if not df.empty:
                            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                            raw_path = os.path.join(DATA_RAW, f"{category}_{timestamp}_raw.csv")
                            clean_path = os.path.join(DATA_CLEANED, f"{category}_{timestamp}_clean.csv")
                            
                            df.to_csv(raw_path, index=False)
                            df_clean = scraper.clean_data(df)
                            df_clean.to_csv(clean_path, index=False)
                            
                            st.success(f"✅ {len(df)} annonces scrapées avec succès !")
                            st.balloons()
                        else:
                            st.warning("Aucune donnée trouvée")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")

        with col2:
            st.info("📝 Instructions")
            st.markdown("""
            1. Sélectionnez une catégorie
            2. Choisissez le nombre de pages
            3. Cliquez sur le bouton de scraping
            """)
            st.warning("⚠️ Le scraping peut prendre plusieurs minutes")


    # Page de téléchargement
    elif menu == "Téléchargement":
        st.title("Téléchargement des données")

        tab1, tab2 = st.tabs(["Données brutes", "Données nettoyées"])

        with tab1:
            raw_files = [f for f in os.listdir(DATA_RAW) if f.endswith(".csv")]
            if raw_files:
                selected_file = st.selectbox("Fichiers bruts disponibles", raw_files)
                with open(f"{DATA_RAW}/{selected_file}", "rb") as f:
                    st.download_button(
                        label="Télécharger",
                        data=f,
                        file_name=selected_file,
                        mime="text/csv"
                    )
            else:
                st.warning("Aucun fichier brut disponible !")

        with tab2:
            cleaned_files = [f for f in os.listdir(DATA_CLEANED) if f.endswith(".csv")]
            if cleaned_files:
                selected_file = st.selectbox("Fichiers nettoyés disponibles", cleaned_files)
                with open(f"{DATA_CLEANED}/{selected_file}", "rb") as f:
                    st.download_button(
                        label="Télécharger",
                        data=f,
                        file_name=selected_file,
                        mime="text/csv"
                    )
            else:
                st.warning("Aucun fichier nettoyé disponible !")

    # Page de menu
    elif menu == "Dashboard":
        st.header("Menu")

        cleaned_files = [f for f in os.listdir(DATA_CLEANED) if f.endswith(".csv")]

        if cleaned_files:
            selected_file = st.selectbox("Sélectionnez un jeu de données", cleaned_files)
            try:
                df = pd.read_csv(f"{DATA_CLEANED}/{selected_file}")
                st.subheader("Aperçu des données")
                st.dataframe(df.head(), use_container_width=True)

                st.header("Analyse visuelle")
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Distribution des prix**")
                    st.bar_chart(df.groupby('marque')['prix'].mean())

                with col2:
                    st.write("**Répartition par état**")
                    st.plotly_chart(px.pie(df, names='etat', title='État des véhicules'))

                    with st.expander("**Statistique avancée**"):
                        st.write(df.describe())
            except pd.errors.EmptyDataError:
                st.error("Le fichier sélectionné est vide ou ne contient pas de colonnes valides.")
        else:
            st.warning("Aucun jeu de données disponible !")

    # Page d'évaluation
    elif menu == "Évaluation":
        st.header("⭐ Évaluez notre application")

        with st.form(key="evaluation_form", clear_on_submit=True):
            name = st.text_input("Votre nom (facultatif)")
            email = st.text_input("Votre email (facultatif)")
            rating = st.slider("Notez notre application", 0, 5, 0, help="0: Mauvais, 5: Excellent")
            feedback = st.text_area("Votre avis", help="Comment pouvons-nous améliorer notre application ?")

            if st.form_submit_button("Envoyer"):
                evaluation = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "name": name,
                    "email": email,
                    "rating": rating,
                    "feedback": feedback
                }
                pd.DataFrame([evaluation]).to_csv(
                    "evaluations.csv",
                    mode="a",
                    index=False,
                    header=not os.path.exists("evaluations.csv")
                )

                st.success("🎉 Merci pour votre évaluation !")

if __name__ == "__main__":
    main()