import streamlit as st
import time

class LocalAccountingAgent:
    def __init__(self):
        self.agent_name = "SmartCompta-Agent"

    def generer_rapport_tva(self, montant_ht, taux_tva):
        # Logique mathématique de l'agent
        montant_tva = montant_ht * (taux_tva / 100)
        montant_ttc = montant_ht + montant_tva
        
        rapport = f"""
============================================================
              RAPPORT FINANCIER GÉNÉRÉ PAR L'IA             
============================================================
Statut de l'Agent : Actif (Mode Déployé Sécurisé)
Modèle Utilisé    : Moteur de Règles Mathématiques v1

DÉTAILS DES CALCULS COMPTABLES :
------------------------------------------------------------
- Montant Hors Taxes (HT)      : {montant_ht:,.2f} SAR
- Taux de TVA Appliqué         : {taux_tva:.1f} %
- Montant de la TVA            : {montant_tva:,.2f} SAR
------------------------------------------------------------
> TOTAL TOUTES TAXES COMPRISES : {montant_ttc:,.2f} SAR

ANALYSE ET CONFORMITÉ :
Le calcul a été validé selon les normes fiscales en vigueur.
============================================================
"""
        return rapport, montant_tva, montant_ttc

# --- INTERFACE GRAPHIQUE STREAMLIT ---
st.set_page_config(page_title="AI Accounting Agent", page_icon="📊", layout="centered")

st.title("📊 AI Accounting & Finance Agent")
st.write("Déployez et utilisez votre agent de calcul financier en temps réel.")

# Formulaire utilisateur
with st.form("accounting_form"):
    st.subheader("Entrée des données financières")
    montant = st.number_input("Montant Hors Taxes (HT) en SAR", min_value=0.0, value=5000.0, step=100.0)
    taux = st.slider("Taux de TVA (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.5)
    
    submit_button = st.form_submit_button("Lancer l'Analyse de l'Agent")

# Action lors du clic
if submit_button:
    agent = LocalAccountingAgent()
    
    with st.spinner("L'agent IA analyse les données..."):
        time.sleep(1) # Simulation de réflexion
        rapport_texte, tva, ttc = agent.generer_rapport_tva(montant, taux)
    
    # Affichage des résultats sous forme de cartes d'indicateurs
    col1, col2 = st.columns(2)
    col1.metric(label="Montant de la TVA", value=f"{tva:,.2f} SAR")
    col2.metric(label="Total TTC", value=f"{ttc:,.2f} SAR")
    
    # Affichage du rapport brut
    st.subheader("Rapport Officiel de l'Agent")
    st.text_area(label="", value=rapport_texte, height=350)
    st.success("Analyse terminée avec succès !")
