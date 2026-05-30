import streamlit as st
import pandas as pd
import numpy as np

class MultiSheetReceivablesAgent:
    def __init__(self):
        self.agent_name = "SmartAudit-Consolidated"

    def consolider_et_analyser(self, dict_dfs):
        liste_df_nettoyes = []
        today_pandas = pd.Timestamp.now().normalize()

        # Identifier le nom de la première feuille pour l'ignorer
        nom_premiere_feuille = list(dict_dfs.keys()) if dict_dfs else None
        onglets_ignores = []

        for nom_feuille, df_feuille in dict_dfs.items():
            nom_clean = str(nom_feuille).lower().strip()
            
            # 1. Ignorer la première feuille (Sommaire/Index)
            if nom_feuille == nom_premiere_feuille:
                onglets_ignores.append(f"{nom_feuille} (Première feuille)")
                continue
                
            # 2. SECOURS ANTI-DOUBLE : Ignorer l'état global / récapitulatif
            mots_cles_globaux = ['total', 'global', 'synthese', 'synthèse', 'balance', 'recap', 'récap', 'all', 'cumul']
            if any(mot in nom_clean for mot in mots_cles_globaux):
                onglets_ignores.append(f"{nom_feuille} (État Global détecté)")
                continue
                
            if df_feuille.empty:
                continue
                
            df_calc = df_feuille.copy()
            
            # Normalisation des en-têtes
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

            if 'Client' not in df_calc.columns:
                df_calc['Client'] = nom_feuille
            
            if 'Chiffre d\'Affaires' not in df_calc.columns:
                df_calc['Chiffre d\'Affaires'] = 0.0
            if 'Montant Recouvré' not in df_calc.columns:
                df_calc['Montant Recouvré'] = df_calc['Chiffre d\'Affaires']

            df_calc['Chiffre d\'Affaires'] = pd.to_numeric(df_calc['Chiffre d\'Affaires'], errors='coerce').fillna(0.0)
            df_calc['Montant Recouvré'] = pd.to_numeric(df_calc['Montant Recouvré'], errors='coerce').fillna(0.0)
            
            df_calc['Créance Totale'] = df_calc['Chiffre d\'Affaires'] - df_calc['Montant Recouvré']
            df_calc['Créance Totale'] = df_calc['Créance Totale'].apply(lambda x: x if x > 0 else 0.0)

            # Gestion des dates (Correctif NaT)
            if 'Date Échéance' in df_calc.columns:
                df_calc['Date Échéance'] = pd.to_datetime(df_calc['Date Échéance'], errors='coerce')
                df_calc['Jours de Retard'] = 0
                masque_valide = df_calc['Date Échéance'].notnull()
                retards = (today_pandas - df_calc.loc[masque_valide, 'Date Échéance']).dt.days
                df_calc.loc[masque_valide, 'Jours de Retard'] = retards.apply(lambda x: x if x > 0 else 0)
            else:
                df_calc['Date Échéance'] = today_pandas
                df_calc['Jours de Retard'] = 0

            df_calc['Créance > 3 Mois'] = np.where(df_calc['Jours de Retard'] > 90, df_calc['Créance Totale'], 0.0)
            df_calc['Source (Onglet)'] = nom_feuille
            
            liste_df_nettoyes.append(df_calc)

        if not liste_df_nettoyes:
            return pd.DataFrame(), "", 0, 0, 0, 0, onglets_ignores

        df_total = pd.concat(liste_df_nettoyes, ignore_index=True)

        total_ca = df_total['Chiffre d\'Affaires'].sum()
        total_recouvrement = df_total['Montant Recouvré'].sum()
        total_creances = df_total['Créance Totale'].sum()
        total_critique_90j = df_total['Créance > 3 Mois'].sum()
        
        taux_recouvrement = (total_recouvrement / total_ca * 100) if total_ca > 0 else 100.0

        rapport = f"""
============================================================
      RAPPORT D'AUDIT FINANCIER CONSOLIDÉ (FEUILLES CLIENTS)
============================================================
Agent Auditeur    : {self.agent_name}
Nombre d'onglets  : {len(liste_df_nettoyes)} feuilles clients analysées
Feuilles ignorées : {", ".join(onglets_ignores)}
Date d'exécution  : {today_pandas.strftime('%d/%m/%Y')}
Statut Risque     : {"🔴 ALERTE LIQUIDITÉ CRITIQUE" if total_critique_90j > (total_creances * 0.25) else "🟢 RECOUVREMENT SOUS CONTRÔLE"}

SYNTHÈSE DE TOUS LES ÉTATS CLIENTS :
------------------------------------------------------------
- Chiffre d'Affaires Cumulé (HT)  : {total_ca:,.2f} SAR
- Total Encaissé / Recouvré       : {total_recouvrement:,.2f} SAR
- Taux de Recouvrement Global     : {taux_recouvrement:.2f} %
- Encours Total des Créances      : {total_creances:,.2f} SAR
- Créances Critiques (> 3 mois)   : {total_critique_90j:,.2f} SAR

NOTE ANALYTIQUE :
Les doublons d'états généraux ont été purgés. Les calculs ci-dessus 
reflètent uniquement l'addition stricte des fiches clients individuelles.
============================================================
"""
        return df_total, rapport, total_ca, total_recouvrement, total_creances, total_critique_90j, onglets_ignores

# --- INTERFACE GRAPHIQUE ---
st.set_page_config(page_title="AI Multi-Sheet Auditor", page_icon="🏦", layout="wide")
st.title("🏦 AI Multi-Sheet Accounting & Receivables Dashboard")
st.write("Analyse consolidée des fiches clients. **Les onglets récapitulatifs globaux (Total, Global, Balance...) sont automatiquement détectés et ignorés pour éviter les doublons.**")

fichier = st.file_uploader("Déposez votre fichier Excel Multi-feuilles (.xlsx)", type=["xlsx"])

if fichier is not None:
    try:
        dict_onglets = pd.read_excel(fichier, sheet_name=None)
        
        agent = MultiSheetReceivablesAgent()
        df_analyse, rapport_txt, ca, recov, creance, critique, ignores = agent.consolider_et_analyser(dict_onglets)
        
        # Affichage des feuilles ignorées pour transparence
        st.warning(f"🚫 Feuilles exclues de l'analyse pour éviter les doublons : {', '.join(ignores)}")
        st.success(f"✅ Analyse finalisée sur les {len(dict_onglets) - len(ignores)} fiches clients individuelles.")
        
        if not df_analyse.empty:
            st.divider()
            
            # KPIs
            st.header("🎯 1. Indicateurs clés consolidés")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Chiffre d'Affaires Cumulé", f"{ca:,.2f} SAR")
            k2.metric("Total Recouvré", f"{recov:,.2f} SAR", delta=f"{(recov/ca*100) if ca > 0 else 0:.1f}% Encaissé")
            k3.metric("Encours Créances Total", f"{creance:,.2f} SAR")
            k4.metric("Créances > 3 Mois", f"{critique:,.2f} SAR", delta="Retard Critique", delta_color="inverse")
            
            st.divider()
            
            # Graphiques
            st.header("📈 2. Graphiques d'Aide à la Décision")
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.subheader("🏆 Top Clients (Par Chiffre d'Affaires)")
                df_top_ca = df_analyse.groupby('Client')['Chiffre d\'Affaires'].sum().reset_index()
                df_top_ca = df_top_ca.sort_values(by='Chiffre d\'Affaires', ascending=False).head(10)
                st.bar_chart(data=df_top_ca, x="Client", y="Chiffre d\'Affaires", color="#29B5E8")
                
            with col_g2:
                st.subheader("⚠️ Top Risques Clients (Créances Totales)")
                df_creance_client = df_analyse.groupby('Client')['Créance Totale'].sum().reset_index()
                df_creance_top = df_creance_client.sort_values(by='Créance Totale', ascending=False).head(10)
                st.bar_chart(data=df_creance_top, x="Client", y="Créance Totale", color="#FF4B4B")
                
            st.divider()
            
            # Rapport et focus
            col_t1, col_t2 = st.columns(2)
            
            with col_t1:
                st.subheader("📋 Rapport d'Audit Épuré")
                st.text_area("", value=rapport_txt, height=350)
                st.download_button("💾 Exporter le Rapport Complet", data=rapport_txt, file_name="Rapport_Audit_Consolide.txt")
                
            with col_t2:
                st.subheader("🚨 Focus : Créances de plus de 3 mois (>90j)")
                df_affichage = df_analyse.copy()
                df_affichage['Date Échéance'] = df_affichage['Date Échéance'].dt.strftime('%d/%m/%Y').fillna('Non spécifiée')
                
                df_retard_90j = df_affichage[df_affichage['Créance > 3 Mois'] > 0][['Client', 'Source (Onglet)', 'Date Échéance', 'Jours de Retard', 'Créance > 3 Mois']]
                if not df_retard_90j.empty:
                    st.warning(f"L'agent a isolé {len(df_retard_90j)} lignes en alerte critique.")
                    st.dataframe(df_retard_90j.sort_values(by='Créance > 3 Mois', ascending=False), use_container_width=True)
                else:
                    st.success("✅ Aucune ligne ne dépasse les 3 mois d'ancienneté.")

            st.subheader("🔍 Base de Données Consolidée Unique")
            df_global_view = df_analyse.copy()
            df_global_view['Date Échéance'] = df_global_view['Date Échéance'].dt.strftime('%d/%m/%Y').fillna('Non spécifiée')
            st.dataframe(df_global_view, use_container_width=True)
            
    except Exception as e:
