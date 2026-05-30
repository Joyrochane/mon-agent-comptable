import streamlit as st
import pandas as pd
import numpy as np
import datetime

class MultiSheetReceivablesAgent:
    def __init__(self):
        self.agent_name = "SmartAudit-Consolidated"

    def consolider_et_analyser(self, dict_dfs):
        liste_df_nettoyes = []
        today = datetime.date.today()

        # 1. Parcours de chaque feuille Excel
        for nom_feuille, df_feuille in dict_dfs.items():
            if df_feuille.empty:
                continue
                
            df_calc = df_feuille.copy()
            
            # Normalisation des en-têtes pour cette feuille
            for col in df_calc.columns:
                c_low = str(col).lower().strip()
                if c_low in ['client', 'nom', 'customer', 'raison sociale', 'débiteur']:
                    df_calc.rename(columns={col: 'Client'}, inplace=True)
                if c_low in ['chiffre d\'affaires', 'ca', 'revenu', 'sales', 'facturé', 'revenue', 'montant']:
                    df_calc.rename(columns={col: 'Chiffre d\'Affaires'}, inplace=True)
                if c_low in ['recouvré', 'montant payé', 'recouvrement', 'paid', 'encaissement']:
                    df_calc.rename(columns={col: 'Montant Recouvré'}, inplace=True)
                if c_low in ['date', 'echeance', 'date d\'échéance', 'due date', 'facture date']:
                    df_calc.rename(columns={col: 'Date Échéance'}, inplace=True)

            # Si le nom du client n'est pas en colonne mais est le nom de la feuille
            if 'Client' not in df_calc.columns:
                df_calc['Client'] = nom_feuille
            
            if 'Chiffre d\'Affaires' not in df_calc.columns:
                df_calc['Chiffre d\'Affaires'] = 0.0
            if 'Montant Recouvré' not in df_calc.columns:
                df_calc['Montant Recouvré'] = df_calc['Chiffre d\'Affaires']

            # Forcer le typage numérique
            df_calc['Chiffre d\'Affaires'] = pd.to_numeric(df_calc['Chiffre d\'Affaires'], errors='coerce').fillna(0.0)
            df_calc['Montant Recouvré'] = pd.to_numeric(df_calc['Montant Recouvré'], errors='coerce').fillna(0.0)
            
            # Calcul de la créance sur cette feuille
            df_calc['Créance Totale'] = df_calc['Chiffre d\'Affaires'] - df_calc['Montant Recouvré']
            df_calc['Créance Totale'] = df_calc['Créance Totale'].apply(lambda x: x if x > 0 else 0.0)

            # Gestion des dates et retards > 3 mois (90 jours)
            if 'Date Échéance' in df_calc.columns:
                df_calc['Date Échéance'] = pd.to_datetime(df_calc['Date Échéance'], errors='coerce').dt.date
                df_calc['Jours de Retard'] = df_calc['Date Échéance'].apply(
                    lambda x: (today - x).days if isinstance(x, datetime.date) and x < today else 0
                )
            else:
                df_calc['Date Échéance'] = today
                df_calc['Jours de Retard'] = 0

            df_calc['Créance > 3 Mois'] = np.where(df_calc['Jours de Retard'] > 90, df_calc['Créance Totale'], 0.0)
            
            # Conserver le nom de l'onglet d'origine pour l'audit
            df_calc['Source (Onglet)'] = nom_feuille
            
            liste_df_nettoyes.append(df_calc)

        # 2. Consolidation globale de toutes les feuilles
        if not liste_df_nettoyes:
            return pd.DataFrame(), "", 0, 0, 0, 0

        df_total = pd.concat(liste_df_nettoyes, ignore_index=True)

        # 3. Calcul des métriques consolidées
        total_ca = df_total['Chiffre d\'Affaires'].sum()
        total_recouvrement = df_total['Montant Recouvré'].sum()
        total_creances = df_total['Créance Totale'].sum()
        total_critique_90j = df_total['Créance > 3 Mois'].sum()
        
        taux_recouvrement = (total_recouvrement / total_ca * 100) if total_ca > 0 else 100.0

        # Génération du rapport d'audit consolidé
        rapport = f"""
============================================================
      RAPPORT D'AUDIT FINANCIER CONSOLIDÉ (MULTI-ONGLETS)
============================================================
Agent Auditeur    : {self.agent_name}
Nombre d'onglets  : {len(dict_dfs)} feuilles analysées
Date d'exécution  : {today.strftime('%d/%m/%Y')}
Statut Risque     : {"🔴 ALERTE LIQUIDITÉ CRITIQUE" if total_critique_90j > (total_creances * 0.25) else "🟢 RECOUVREMENT SOUS CONTRÔLE"}

SYNTHÈSE DE TOUS LES ÉTATS CLIENTS :
------------------------------------------------------------
- Chiffre d'Affaires Cumulé (HT)  : {total_ca:,.2f} SAR
- Total Encaissé / Recouvré       : {total_recouvrement:,.2f} SAR
- Taux de Recouvrement Global     : {taux_recouvrement:.2f} %
- Encours Total des Créances      : {total_creances:,.2f} SAR
- Créances Critiques (> 3 mois)   : {total_critique_90j:,.2f} SAR

NOTE ANALYTIQUE :
Les créances de plus de 3 mois représentent { (total_critique_90j/total_creances*100) if total_creances > 0 else 0:.1f}% de votre encours de trésorerie.
L'agent a regroupé les données de chaque onglet pour créer les classements ci-dessous.
============================================================
"""
        return df_total, rapport, total_ca, total_recouvrement, total_creances, total_critique_90j

# --- INTERFACE DE L'APPLICATION ---
st.set_page_config(page_title="AI Multi-Sheet Auditor", page_icon="🏦", layout="wide")
st.title("🏦 AI Multi-Sheet Accounting & Receivables Dashboard")
st.write("Cet agent extrait, combine et analyse automatiquement **toutes les feuilles de calcul** de votre fichier Excel.")

fichier = st.file_uploader("Déposez votre fichier Excel Multi-feuilles (.xlsx)", type=["xlsx"])

if fichier is not None:
    try:
        # ÉTAPE CLÉ : On charge TOUTES les feuilles en mémoire (sheet_name=None)
        # Cela retourne un dictionnaire : { "Nom de Feuille": DataFrame }
        dict_onglets = pd.read_excel(fichier, sheet_name=None)
        
        st.success(f"✅ Fichier détecté ! {len(dict_onglets)} feuilles de calcul ont été extraites avec succès.")
        
        agent = MultiSheetReceivablesAgent()
        df_analyse, rapport_txt, ca, recov, creance, critique = agent.consolider_et_analyser(dict_onglets)
        
        if not df_analyse.empty:
            st.divider()
            
            # --- KPIS CONSOLIDÉS ---
            st.header("🎯 1. Indicateurs clés consolidés (Toutes feuilles)")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Chiffre d'Affaires Cumulé", f"{ca:,.2f} SAR")
            k2.metric("Total Recouvré (Encaissé)", f"{recov:,.2f} SAR", delta=f"{(recov/ca*100) if ca > 0 else 0:.1f}% Recouvré")
            k3.metric("Encours Créances Total", f"{creance:,.2f} SAR")
            k4.metric("Créances > 3 Mois", f"{critique:,.2f} SAR", delta="Retard Critique", delta_color="inverse")
            
            st.divider()
            
            # --- GRAPHES D'ANALYSE ---
            st.header("📈 2. Graphiques d'Aide à la Décision")
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.subheader("🏆 Top Clients / États (Par Chiffre d'Affaires)")
                df_top_ca = df_analyse.groupby('Client')['Chiffre d\'Affaires'].sum().reset_index()
                df_top_ca = df_top_ca.sort_values(by='Chiffre d\'Affaires', ascending=False).head(10)
                st.bar_chart(data=df_top_ca, x="Client", y="Chiffre d\'Affaires", color="#29B5E8")
                
            with col_g2:
                st.subheader("⚠️ Top Risques Clients (Créances Totales)")
                df_creance_client = df_analyse.groupby('Client')['Créance Totale'].sum().reset_index()
                df_creance_top = df_creance_client.sort_values(by='Créance Totale', ascending=False).head(10)
                st.bar_chart(data=df_creance_top, x="Client", y="Créance Totale", color="#FF4B4B")
                
            st.divider()
            
            # --- RAPPORT & DETAILED FOCUS ---
            col_t1, col_t2 = st.columns()
            
            with col_t1:
                st.subheader("📋 Rapport d'Audit Global")
                st.text_area("", value=rapport_txt, height=350)
                st.download_button("💾 Exporter le Rapport Complet", data=rapport_txt, file_name="Rapport_Audit_Consolide.txt")
                
            with col_t2:
                st.subheader("🚨 Focus Restreint : Créances de plus de 3 mois (>90j)")
                df_retard_90j = df_analyse[df_analyse['Créance > 3 Mois'] > 0][['Client', 'Source (Onglet)', 'Date Échéance', 'Jours de Retard', 'Créance > 3 Mois']]
                if not df_retard_90j.empty:
                    st.warning(f"L'agent a isolé {len(df_retard_90j)} lignes en alerte critique à travers vos feuilles de calcul.")
                    st.dataframe(df_retard_90j.sort_values(by='Créance > 3 Mois', ascending=False), use_container_width=True)
                else:
                    st.success("✅ Excellente nouvelle : Aucune feuille ne contient de retard supérieur à 3 mois.")

            # Affichage de la grande table fusionnée
            st.subheader("🔍 Base de Données Consolidée (Fusion de tous les onglets)")
            st.dataframe(df_analyse, use_container_width=True)
            
        else:
            st.error("Les feuilles de calcul lues semblent vides ou mal structurées.")

    except Exception as e:
        st.error(f"Erreur d'analyse multi-feuilles : {e}. Vérifiez que vos onglets partagent des colonnes de données chiffrées similaires.")
else:
    st.info("💡 Mode Multi-Feuilles Prêt. Déposez votre fichier Excel complet contenant les différents onglets clients ci-dessus.")
