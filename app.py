import streamlit as st
import pandas as pd
import numpy as np

class FinancialAnalyticsAgent:
    def __init__(self):
        self.agent_name = "SmartCompta-Analytics"

    def analyser_donnees(self, df_depenses, df_revenus, taux_tva):
        # 1. Calculs Comptables Standards
        df_dep_calc = df_depenses.copy()
        df_dep_calc['TVA (SAR)'] = df_dep_calc['Montant HT (SAR)'] * (taux_tva / 100)
        df_dep_calc['Total TTC (SAR)'] = df_dep_calc['Montant HT (SAR)'] + df_dep_calc['TVA (SAR)']
        
        total_depenses_ht = df_dep_calc['Montant HT (SAR)'].sum()
        total_tva_depenses = df_dep_calc['TVA (SAR)'].sum()
        total_revenus_ht = df_revenus['Montant HT (SAR)'].sum()
        
        # 2. Analyse Financière (Indicateurs Clés)
        resultat_net_ht = total_revenus_ht - total_depenses_ht
        marge_beneficiaire = (resultat_net_ht / total_revenus_ht * 100) if total_revenus_ht > 0 else 0.0
        ratio_depense_revenu = (total_depenses_ht / total_revenus_ht * 100) if total_revenus_ht > 0 else 0.0
        
        # 3. Analyse de Données (Statistiques & Audit)
        alerte_anomalie = ""
        if len(df_dep_calc) > 0:
            moyenne_depenses = df_dep_calc['Montant HT (SAR)'].mean()
            # Détection d'anomalie : dépense supérieure à 2x la moyenne des autres dépenses
            depenses_hautes = df_dep_calc[df_dep_calc['Montant HT (SAR)'] > (moyenne_depenses * 1.8)]
            if not depenses_hautes.empty:
                categories_alert = ", ".join(depenses_hautes['Catégorie'].tolist())
                alerte_anomalie = f"⚠️ [ANOMALIE DE DONNÉES DETECTÉE] : Les catégories suivantes ({categories_alert}) ont des montants anormalement élevés par rapport à la moyenne de vos coûts."
        
        # Génération du rapport d'audit analytique
        rapport_txt = f"""
============================================================
             RAPPORT D'ANALYSE FINANCIÈRE & AUDIT             
============================================================
Agent Analyste    : {self.agent_name}
Mode Opérationnel : Audit Statistique & Financier

1. INDICES DE PERFORMANCE FINANCIÈRE :
------------------------------------------------------------
- Chiffre d'Affaires Global (HT) : {total_revenus_ht:,.2f} SAR
- Total des Charges Opérat. (HT) : {total_depenses_ht:,.2f} SAR
- Résultat Net Estimé (HT)       : {resultat_net_ht:,.2f} SAR
- Marge Bénéficiaire Net         : {marge_beneficiaire:.2f} %
- Ratio Charges / Revenus        : {ratio_depense_revenu:.2f} %

2. AUDIT ET ANALYSE STATISTIQUE DES DONNÉES :
------------------------------------------------------------
- Nombre total de transactions   : {len(df_dep_calc) + len(df_revenus)}
- Coût Moyen par Poste           : {df_dep_calc['Montant HT (SAR)'].mean():,.2f} SAR
- Écart-Type des Dépenses        : {df_dep_calc['Montant HT (SAR)'].std():,.2f} SAR

{alerte_anomalie if alerte_anomalie else "✅ [RAS] : La distribution de vos dépenses est statistiquement équilibrée."}

NOTE STRATÉGIQUE :
{"Attention, votre structure de coûts consomme une trop grande part de vos revenus." if ratio_depense_revenu > 70 else "Votre santé financière est excellente. Vos charges sont bien maîtrisées."}
============================================================
"""
        return df_dep_calc, rapport_txt, total_revenus_ht, total_depenses_ht, resultat_net_ht, marge_beneficiaire

# --- INTERFACE DE L'APPLICATION (MODE WIDE) ---
st.set_page_config(page_title="AI Financial Analytics", page_icon="📈", layout="wide")

st.title("📈 AI Accounting & Financial Analytics Agent")
st.write("Plateforme d'aide à la décision : Analyse de données comptables et indicateurs de performance.")

# Initialisation des données de simulation
if 'init' not in st.session_state:
    st.session_state.df_rev = pd.DataFrame({"Source de Revenu": ["Ventes Boutique", "Abonnements SaaS", "Prestations de Service"], "Montant HT (SAR)": [12000.0, 8500.0, 4500.0]})
    st.session_state.df_dep = pd.DataFrame({"Catégorie": ["Logistique", "Marketing & Pub", "Salaires", "Hébergement IT"], "Montant HT (SAR)": [1500.0, 7800.0, 8500.0, 1200.0]})
    st.session_state.init = True

# Organisation de la saisie sur deux colonnes
col_rev, col_dep = st.columns(2)

with col_rev:
    st.subheader("💰 1. Registre des Revenus (HT)")
    df_rev_edite = st.data_editor(st.session_state.df_rev, num_rows="dynamic", use_container_width=True, key="rev_edit")

with col_dep:
    st.subheader("💸 2. Registre des Dépenses (HT)")
    df_dep_edite = st.data_editor(st.session_state.df_dep, num_rows="dynamic", use_container_width=True, key="dep_edit")

taux_global = st.slider("Configuration - Taux de TVA Fiscal (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.5)

# --- BLOC ANALYTIQUE ---
if st.button("🚀 Exécuter l'Analyse Financière & Dataviz"):
    agent = FinancialAnalyticsAgent()
    
    # Traitement des données par l'agent
    df_dep_res, rapport, tot_rev, tot_dep, net, marge = agent.analyser_donnees(df_dep_edite, df_rev_edite, taux_global)
    
    st.divider()
    st.header("🎯 Tableau de Bord Analytique")
    
    # KPIs financiers
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(label="Chiffre d'Affaires", value=f"{tot_rev:,.2f} SAR")
    kpi2.metric(label="Total Dépenses HT", value=f"{tot_dep:,.2f} SAR")
    kpi3.metric(label="Bénéfice Net (HT)", value=f"{net:,.2f} SAR", delta=f"{marge:.1f}% Marge")
    kpi4.metric(label="TVA sur Dépenses", value=f"{df_dep_res['TVA (SAR)'].sum():,.2f} SAR")
    
    # Section Graphiques (Analyse visuelle des données)
    st.subheader("📊 Visualisation & Répartition des Flux")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.write("**Répartition des Dépenses Opérationnelles (SAR)**")
        st.bar_chart(data=df_dep_res, x="Catégorie", y="Montant HT (SAR)", color="#FF4B4B")
        
    with col_g2:
        st.write("**Comparatif Global : Revenus vs Dépenses (SAR)**")
        df_compare = pd.DataFrame({
            'Flux Financier': ['Total Revenus', 'Total Dépenses'],
            'Montant (SAR)': [tot_rev, tot_dep]
        })
        st.bar_chart(data=df_compare, x="Flux Financier", y="Montant (SAR)", color="#29B5E8")
        
    # Section Rapport d'Audit écrit
    st.subheader("📋 Rapport d'Audit Textuel")
    st.text_area(label="", value=rapport, height=320)
    
    st.download_button(
        label="💾 Exporter le rapport d'analyse (.txt)",
        data=rapport,
        file_name="rapport_analyse_financiere.txt",
        mime="text/plain"
    )
    
    # Affichage de la table de données enrichie
    st.subheader("🔍 Données comptables consolidées (Dépenses)")
    st.dataframe(df_dep_res, use_container_width=True)
