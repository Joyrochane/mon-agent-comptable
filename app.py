import streamlit as st
import pandas as pd
import datetime

class CreancesAnalyticsAgent:
    def __init__(self):
        self.agent_name = "SmartCreances-Auditor"

    def analyser_creances(self, df):
        df_calc = df.copy()
        
        # Standardisation des colonnes (Gestion des synonymes)
        for col in df_calc.columns:
            if col.lower() in ['client', 'nom', 'customer', 'raison sociale']:
                df_calc.rename(columns={col: 'Client'}, inplace=True)
            if col.lower() in ['montant', 'montant dû', 'creance', 'amount', 'solde']:
                df_calc.rename(columns={col: 'Montant Dû (SAR)'}, inplace=True)
            if col.lower() in ['date', 'echeance', 'date d\'échéance', 'due date']:
                df_calc.rename(columns={col: 'Date d\'Échéance'}, inplace=True)

        # Vérification des colonnes critiques
        if 'Client' not in df_calc.columns: df_calc['Client'] = "Inconnu"
        if 'Montant Dû (SAR)' not in df_calc.columns: df_calc['Montant Dû (SAR)'] = 0.0
        
        # Nettoyage numérique
        df_calc['Montant Dû (SAR)'] = pd.to_numeric(df_calc['Montant Dû (SAR)'], errors='coerce').fillna(0.0)
        
        # Calcul du retard si la date d'échéance existe
        today = datetime.date.today()
        if 'Date d\'Échéance' in df_calc.columns:
            df_calc['Date d\'Échéance'] = pd.to_datetime(df_calc['Date d\'Échéance'], errors='coerce').dt.date
            df_calc['Jours de Retard'] = df_calc['Date d\'Échéance'].apply(
                lambda x: (today - x).days if isinstance(x, datetime.date) and x < today else 0
            )
        else:
            df_calc['Jours de Retard'] = 0

        # Catégorisation du risque
        def evaluer_risque(jours):
            if jours == 0: return "1. À jour (Sain)"
            elif jours <= 30: return "2. Risque Faible (1-30j)"
            elif jours <= 90: return "3. Risque Modéré (31-90j)"
            else: return "4. Risque Critique (>90j)"
            
        df_calc['Statut Risque'] = df_calc['Jours de Retard'].apply(evaluer_risque)
        
        # Indicateurs globaux
        total_creances = df_calc['Montant Dû (SAR)'].sum()
        total_retard = df_calc[df_calc['Jours de Retard'] > 0]['Montant Dû (SAR)'].sum()
        top_debiteur = df_calc.sort_values(by='Montant Dû (SAR)', ascending=False).iloc[0]['Client'] if len(df_calc) > 0 else "Aucun"

        # Génération du rapport d'audit et du Workflow
        rapport_txt = f"""
============================================================
           AUDIT DES CRÉANCES CLIENTS & WORKFLOW AI         
============================================================
Agent d'Audit     : {self.agent_name}
Date de l'Analyse : {today.strftime('%d/%m/%Y')}
Statut du Portefeuille : {"⚠️ ALERTE LIQUIDITÉ" if total_retard > (total_creances * 0.5) else "✅ SAIN"}

1. DIAGNOSTIC DU PORTEFEUILLE DE CRÉANCES :
------------------------------------------------------------
- Encours Client Global      : {total_creances:,.2f} SAR
- Total des Sommes En Retard : {total_retard:,.2f} SAR
- Taux d'Impayés / Retards   : {(total_retard/total_creances*100) if total_creances > 0 else 0:.1f} %
- Plus Grand Débiteur        : {top_debiteur}

2. WORKFLOW RECOMMANDÉ DE RECOUVREMENT :
------------------------------------------------------------
[ÉTAPE 1] 🟢 CRÉANCES SAINES (Échéance non dépassée) :
 -> Action : Envoi automatique d'un relevé de compte de courtoisie 5 jours avant l'échéance.
 
[ÉTAPE 2] 🟡 RETARD 1-30 JOURS (Risque Faible) :
 -> Action : Relance par Email n°1 amicale + appel téléphonique de suivi par le service comptable.
 
[ÉTAPE 3] 🟠 RETARD 31-90 JOURS (Risque Modéré) :
 -> Action : Envoi d'une lettre de mise en demeure formelle en recommandé. Suspension des encours.
 
[ÉTAPE 4] 🔴 RETARD >90 JOURS (Risque Critique) :
 -> Action : Transfert immédiat du dossier au service contentieux ou à une société de recouvrement.
============================================================
"""
        return df_calc, rapport_txt, total_creances, total_retard, top_debiteur

# --- INTERFACE ---
st.set_page_config(page_title="AI Customer Receivables", page_icon="🏦", layout="wide")
st.title("🏦 AI Customer Receivables & Recovery Workflow Agent")
st.write("Déposez votre fichier Excel pour extraire les données, générer les graphiques de risque et le workflow.")

# Bouton d'importation hybride Excel / CSV
fichier = st.file_uploader("Importer le fichier des créances clients (Format .xlsx ou .csv)", type=["xlsx", "csv"])

if fichier is not None:
    try:
        # Lecture automatique du format
        if fichier.name.endswith('.xlsx'):
            df_input = pd.read_excel(fichier)
        else:
            df_input = pd.read_csv(fichier)
            
        st.success("✅ Fichier chargé avec succès ! Analyse en cours...")
        
        agent = CreancesAnalyticsAgent()
        df_res, rapport, total_c, total_r, top_d = agent.analyser_creances(df_input)
        
        st.divider()
        
        # KPIs
        k1, k2, k3 = st.columns(3)
        k1.metric("Encours Total Clients", f"{total_c:,.2f} SAR")
        k2.metric("Total en Retard de Paiement", f"{total_r:,.2f} SAR", delta=f"{(total_r/total_c*100) if total_c > 0 else 0:.1f}% du total", delta_color="inverse")
        k3.metric("Principal Débiteur", str(top_d))
        
        # Graphiques
        st.subheader("📊 Graphiques et Répartition du Risque")
        g1, g2 = st.columns(2)
        
        with g1:
            st.write("**Volume des créances par niveau de risque (SAR)**")
            # Groupement par statut de risque pour le graphique
            df_chart = df_res.groupby('Statut Risque')['Montant Dû (SAR)'].sum().reset_index()
            st.bar_chart(data=df_chart, x="Statut Risque", y="Montant Dû (SAR)", color="#FF4B4B")
            
        with g2:
            st.write("**Top 10 des clients par encours (SAR)**")
            df_top10 = df_res.sort_values(by='Montant Dû (SAR)', ascending=False).head(10)
            st.bar_chart(data=df_top10, x="Client", y="Montant Dû (SAR)", color="#29B5E8")
            
        # Rapport & Workflow
        st.subheader("📋 Rapport d'Audit & Workflow de Recouvrement")
        st.text_area("", value=rapport, height=400)
        
        # Téléchargement
        st.download_button("💾 Exporter le Rapport & Workflow (TXT)", data=rapport, file_name="workflow_recouvrement.txt")
        
        st.subheader("🔍 Table des données extraites et qualifiées")
        st.dataframe(df_res, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erreur lors de l'extraction des données : {e}. Assurez-vous que le fichier contient des entêtes lisibles.")
else:
    st.info("💡 En attente de votre fichier. Veuillez glisser-déposer votre document Excel ci-dessus pour lancer l'agent.")
