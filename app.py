import streamlit as st
import pandas as pd
import datetime

class ReceivablesIntelligenceAgent:
    def __init__(self):
        self.agent_name = "SmartAudit-Pro"

    def extraire_et_analyser(self, df):
        df_calc = df.copy()
        
        # 1. Cartographie et nettoyage intelligent des en-têtes
        for col in df_calc.columns:
            c_low = col.lower().strip()
            if c_low in ['client', 'nom', 'customer', 'raison sociale', 'débiteur']:
                df_calc.rename(columns={col: 'Client'}, inplace=True)
            if c_low in ['chiffre d\'affaires', 'ca', 'revenu', 'sales', 'facturé', 'revenue']:
                df_calc.rename(columns={col: 'Chiffre d\'Affaires'}, inplace=True)
            if c_low in ['recouvré', 'montant payé', 'recouvrement', 'paid', 'encaissement']:
                df_calc.rename(columns={col: 'Montant Recouvré'}, inplace=True)
            if c_low in ['date', 'echeance', 'date d\'échéance', 'due date', 'facture date']:
                df_calc.rename(columns={col: 'Date Échéance'}, inplace=True)

        # Vérification et injection des colonnes par défaut si manquantes
        if 'Client' not in df_calc.columns: df_calc['Client'] = "Client Anonyme"
        if 'Chiffre d\'Affaires' not in df_calc.columns: df_calc['Chiffre d\'Affaires'] = 0.0
        if 'Montant Recouvré' not in df_calc.columns: df_calc['Montant Recouvré'] = df_calc['Chiffre d\'Affaires']
        
        # Forcer le typage numérique
        df_calc['Chiffre d\'Affaires'] = pd.to_numeric(df_calc['Chiffre d\'Affaires'], errors='coerce').fillna(0.0)
        df_calc['Montant Recouvré'] = pd.to_numeric(df_calc['Montant Recouvré'], errors='coerce').fillna(0.0)
        
        # Calcul du solde restant dû (Créance)
        df_calc['Créance Totale'] = df_calc['Chiffre d\'Affaires'] - df_calc['Montant Recouvré']
        df_calc['Créance Totale'] = df_calc['Créance Totale'].apply(lambda x: x if x > 0 else 0.0)

        # 2. Analyse temporelle des retards (> 3 mois / 90 jours)
        today = datetime.date.today()
        if 'Date Échéance' in df_calc.columns:
            df_calc['Date Échéance'] = pd.to_datetime(df_calc['Date Échéance'], errors='coerce').dt.date
            df_calc['Jours de Retard'] = df_calc['Date Échéance'].apply(
                lambda x: (today - x).days if isinstance(x, datetime.date) and x < today else 0
            )
        else:
            # Si aucune date n'est fournie, on simule une colonne de base pour éviter le crash
            df_calc['Date Échéance'] = today
            df_calc['Jours de Retard'] = 0

        # Extraction des créances > 3 mois
        df_calc['Créance > 3 Mois'] = np.where(df_calc['Jours de Retard'] > 90, df_calc['Créance Totale'], 0.0)

        # 3. Métriques de performance globales
        total_ca = df_calc['Chiffre d\'Affaires'].sum()
        total_recouvrement = df_calc['Montant Recouvré'].sum()
        total_creances = df_calc['Créance Totale'].sum()
        total_critique_90j = df_calc['Créance > 3 Mois'].sum()
        
        taux_recouvrement = (total_recouvrement / total_ca * 100) if total_ca > 0 else 100.0

        # Génération du rapport d'audit exécutif
        rapport = f"""
============================================================
          RAPPORT AUDIT : CHIFFRE D'AFFAIRES & CRÉANCES
============================================================
Analyseur Optionnel : {self.agent_name}
Date d'exécution   : {today.strftime('%d/%m/%Y')}
Niveau d'Alerte    : {"🔴 CRITIQUE" if total_critique_90j > (total_creances * 0.3) else "🟢 MAÎTRISÉ"}

SUMMARY DES INDICATEURS FINANCIERS :
------------------------------------------------------------
- Chiffre d'Affaires Global (HT)  : {total_ca:,.2f} SAR
- Total des Flux Recouvrés        : {total_recouvrement:,.2f} SAR
- Taux de Performance Recouvrement: {taux_recouvrement:.2f} %
- Solde Global Créances Clients   : {total_creances:,.2f} SAR
- Créances Toxiques (> 3 mois)    : {total_critique_90j:,.2f} SAR

PLAN D'ACTION CRÉANCES ANCIENNES (> 90 JOURS) :
Les sommes qui dépassent 3 mois représentent { (total_critique_90j/total_creances*100) if total_creances > 0 else 0:.1f}% de votre encours global. 
-> Action immédiate requise : Lancement d'une procédure pré-contentieuse pour les clients concernés.
============================================================
"""
        return df_calc, rapport, total_ca, total_recouvrement, total_creances, total_critique_90j

# --- CONFIGURATION INTERFACE GRAPHIQUE ---
st.set_page_config(page_title="AI Financial Dashboard", page_icon="📈", layout="wide")
st.title("📊 AI Corporate Finance & Receivables Dashboard")
st.write("Analyse automatique des balances âgées, du chiffre d'affaires et du recouvrement.")

# Module d'importation
fichier = st.file_uploader("Déposez votre fichier client (Format .xlsx ou .csv)", type=["xlsx", "csv"])

if fichier is not None:
    try:
        import numpy as np # Importation de sécurité locale pour np.where
        
        if fichier.name.endswith('.xlsx'):
            df_brut = pd.read_excel(fichier)
        else:
            df_brut = pd.read_csv(fichier)
            
        st.success("📊 Données extraites avec succès. Génération des tableaux de bord...")
        
        agent = ReceivablesIntelligenceAgent()
        df_analyse, rapport_txt, ca, recov, creance, critique = agent.extraire_et_analyser(df_brut)
        
        st.divider()
        
        # --- BLOC 1 : KPIs COMPTABLES REQUIS ---
        st.header("🎯 1. Indicateurs clés de Performance (KPIs)")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Chiffre d'Affaires Global", f"{ca:,.2f} SAR")
        k2.metric("Total Recouvrement", f"{recov:,.2f} SAR", delta=f"{(recov/ca*100) if ca > 0 else 0:.1f}% encaissé")
        k3.metric("Encours Créances global", f"{creance:,.2f} SAR")
        k4.metric("Créances > 3 Mois", f"{critique:,.2f} SAR", delta="Risque de perte", delta_color="inverse")
        
        st.divider()
        
        # --- BLOC 2 : TABLEAUX DE BORD ET GRAPHIQUES ---
        st.header("📈 2. Graphiques d'Aide à la Décision")
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("🏆 Classement des Meilleurs Clients (Par CA)")
            # Top 10 des clients par Chiffre d'Affaires
            df_top_ca = df_analyse.groupby('Client')['Chiffre d\'Affaires'].sum().reset_index()
            df_top_ca = df_top_ca.sort_values(by='Chiffre d\'Affaires', ascending=False).head(10)
            st.bar_chart(data=df_top_ca, x="Client", y="Chiffre d\'Affaires", color="#29B5E8")
            
        with col_g2:
            st.subheader("⚠️ État des Créances Clients")
            # Comparaison du montant normal vs critique par client
            df_creance_client = df_analyse.groupby('Client')[['Créance Totale', 'Créance > 3 Mois']].sum().reset_index()
            df_creance_top = df_creance_client.sort_values(by='Créance Totale', ascending=False).head(10)
            st.bar_chart(data=df_creance_top, x="Client", y="Créance Totale", color="#FF4B4B")
            
        st.divider()
        
        # --- BLOC 3 : FOCUS ANALYSIS & WORKFLOW ---
        col_t1, col_t2 = st.columns([1, 2])
        
        with col_t1:
            st.subheader("📋 Rapport d'Audit & Recommandations")
            st.text_area("", value=rapport_txt, height=350)
            st.download_button("💾 Exporter Rapport Exécutif", data=rapport_txt, file_name="Rapport_Audit_Financier.txt")
            
        with col_t2:
            st.subheader("🚨 Focus : Créances en retard de plus de 3 mois")
            df_retard_90j = df_analyse[df_analyse['Créance > 3 Mois'] > 0][['Client', 'Date Échéance', 'Jours de Retard', 'Créance > 3 Mois']]
            if not df_retard_90j.empty:
                st.warning(f"Il y a {len(df_retard_90j)} comptes clients dont la dette dépasse les 90 jours réglementaires.")
                st.dataframe(df_retard_90j.sort_values(by='Créance > 3 Mois', ascending=False), use_container_width=True)
            else:
                st.success("✅ Félicitations, aucune créance client ne dépasse les 3 mois d'ancienneté.")

        # Affichage global de la feuille de calcul
        st.subheader("🔍 Grand Livre des Tiers consolidé")
        st.dataframe(df_analyse, use_container_width=True)

    except Exception as e:
        st.error(f"Une erreur est survenue lors de l'analyse automatique : {e}. Assurez-vous que votre tableur possède bien des colonnes nommées explicitement (Client, Chiffre d'Affaires, Recouvré, Échéance).")
else:
    st.info("💡 En attente de votre document. Glissez-déposez votre fichier d'état des créances (.xlsx) ci-dessus pour que l'agent génère le tableau de bord.")
