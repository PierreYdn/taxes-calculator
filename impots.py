import streamlit as st
import pandas as pd
from datetime import datetime

# ============================================================================
# CONFIGURATION DE LA PAGE ET STYLES RESPONSIVES
# ============================================================================

st.set_page_config(
    page_title="Calculateur d'Impôts",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS pour adaptation mobile/desktop
st.markdown("""
    <style>
    /* Variables globales */
    :root {
        --mobile-breakpoint: 768px;
    }

    /* Adaptation générale */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Mobile */
    @media only screen and (max-width: 768px) {
        .block-container {
            padding: 1rem 0.5rem;
        }

        h1 {
            font-size: 1.8rem !important;
            margin-bottom: 1rem !important;
        }

        h2 {
            font-size: 1.4rem !important;
            margin-top: 1.5rem !important;
        }

        h3 {
            font-size: 1.1rem !important;
            margin-top: 0.5rem !important;
        }

        /* Ajuster les métriques */
        [data-testid="stMetricValue"] {
            font-size: 1.1rem !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.9rem !important;
        }

        /* Inputs plus grands sur mobile */
        input, select, textarea {
            font-size: 16px !important;
            padding: 0.5rem !important;
        }

        /* Boutons plus espacés */
        .stButton button {
            width: 100%;
            padding: 0.75rem !important;
            font-size: 1rem !important;
        }

        /* Tables adaptées */
        .dataframe {
            font-size: 0.85rem !important;
        }

        /* Espacements réduits */
        .element-container {
            margin-bottom: 0.5rem !important;
        }
    }

    /* Desktop */
    @media only screen and (min-width: 769px) {
        .block-container {
            max-width: 1400px;
            padding: 2rem 3rem;
        }
    }

    /* Amélioration des expanders */
    .streamlit-expanderHeader {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }

    /* Alertes plus visibles */
    .stAlert {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# BARÈME D'IMPOSITION 2024
# ============================================================================

TRANCHES_IMPOSITION = [
    {"min": 0, "max": 11294, "taux": 0.00, "label": "0%"},
    {"min": 11294, "max": 28797, "taux": 0.11, "label": "11%"},
    {"min": 28797, "max": 82341, "taux": 0.30, "label": "30%"},
    {"min": 82341, "max": 177106, "taux": 0.41, "label": "41%"},
    {"min": 177106, "max": float('inf'), "taux": 0.45, "label": "45%"}
]

MOIS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]


# ============================================================================
# FONCTIONS DE CALCUL
# ============================================================================

def calculer_impot(revenu_imposable, nb_parts=1):
    """Calcule l'impôt sur le revenu selon le barème progressif français"""
    quotient = revenu_imposable / nb_parts
    impot_par_part = 0
    detail_tranches = []

    for tranche in TRANCHES_IMPOSITION:
        if quotient > tranche["min"]:
            base_tranche = min(quotient, tranche["max"]) - tranche["min"]
            impot_tranche = base_tranche * tranche["taux"]
            impot_par_part += impot_tranche

            detail_tranches.append({
                "tranche": f"{tranche['min']:,.0f} € à {tranche['max']:,.0f} €" if tranche['max'] != float('inf')
                else f"Plus de {tranche['min']:,.0f} €",
                "taux": tranche["label"],
                "base": base_tranche,
                "impot": impot_tranche
            })

    impot_total = impot_par_part * nb_parts

    return {
        "impot_total": impot_total,
        "impot_par_part": impot_par_part,
        "quotient": quotient,
        "detail_tranches": detail_tranches
    }


def formater_euros(montant):
    """Formate un montant en euros"""
    return f"{montant:,.2f} €".replace(",", " ")


def initialiser_session_state():
    """Initialise les variables de session"""
    if 'revenus_mensuels' not in st.session_state:
        st.session_state.revenus_mensuels = [0.0] * 12
    if 'impots_mensuels' not in st.session_state:
        st.session_state.impots_mensuels = [0.0] * 12
    if 'revenus_exceptionnels' not in st.session_state:
        st.session_state.revenus_exceptionnels = []
    if 'mode_affichage' not in st.session_state:
        # Détection automatique du mode (approximatif)
        st.session_state.mode_affichage = "auto"


def reinitialiser():
    """Réinitialise toutes les données"""
    st.session_state.revenus_mensuels = [0.0] * 12
    st.session_state.impots_mensuels = [0.0] * 12
    st.session_state.revenus_exceptionnels = []


# ============================================================================
# INTERFACE PRINCIPALE
# ============================================================================

# Initialisation
initialiser_session_state()

# En-tête
st.title("💰 Calculateur d'Impôts")
st.caption("Calculez votre impôt sur le revenu 2024")
st.markdown("---")

# ============================================================================
# SECTION 1: CONFIGURATION
# ============================================================================

with st.expander("⚙️ Configuration", expanded=True):
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        nb_parts = st.number_input(
            "Nombre de parts fiscales",
            min_value=1.0,
            max_value=10.0,
            value=1.0,
            step=0.5,
            help="1 part = célibataire, 2 parts = couple, +0.5 par enfant"
        )

    with col2:
        annee = st.selectbox(
            "Année d'imposition",
            [2024, 2023, 2022],
            help="Barème applicable"
        )

    with col3:
        mode = st.selectbox(
            "Affichage",
            ["Auto", "Mobile", "Desktop"],
            help="Mode d'affichage des mois"
        )

# ============================================================================
# SECTION 2: REVENUS MENSUELS
# ============================================================================

st.markdown("---")
st.header("📅 Revenus Mensuels")

# Déterminer le mode d'affichage
afficher_mode_mobile = (mode == "Mobile") or (mode == "Auto")

# Légende
col_leg1, col_leg2 = st.columns(2)
with col_leg1:
    st.markdown("**💵 Revenu net**")
with col_leg2:
    st.markdown("**🏦 Impôt prélevé**")

st.markdown("")

# Affichage des mois
if afficher_mode_mobile:
    # MODE MOBILE: 1 colonne, tous les mois
    for i in range(12):
        with st.container():
            st.markdown(f"**{MOIS[i]}**")
            col_rev, col_imp = st.columns(2)

            with col_rev:
                st.session_state.revenus_mensuels[i] = st.number_input(
                    "Revenu",
                    min_value=0.0,
                    value=st.session_state.revenus_mensuels[i],
                    step=100.0,
                    key=f"rev_{i}",
                    format="%.2f",
                    label_visibility="collapsed"
                )

            with col_imp:
                st.session_state.impots_mensuels[i] = st.number_input(
                    "Impôt",
                    min_value=0.0,
                    value=st.session_state.impots_mensuels[i],
                    step=10.0,
                    key=f"imp_{i}",
                    format="%.2f",
                    label_visibility="collapsed"
                )
else:
    # MODE DESKTOP: 3 colonnes de 4 mois
    cols = st.columns(3)
    for i in range(3):
        with cols[i]:
            for j in range(4):
                mois_idx = i * 4 + j
                st.markdown(f"**{MOIS[mois_idx]}**")

                col_rev, col_imp = st.columns(2)

                with col_rev:
                    st.session_state.revenus_mensuels[mois_idx] = st.number_input(
                        "Revenu",
                        min_value=0.0,
                        value=st.session_state.revenus_mensuels[mois_idx],
                        step=100.0,
                        key=f"rev_{mois_idx}",
                        format="%.2f",
                        label_visibility="collapsed"
                    )

                with col_imp:
                    st.session_state.impots_mensuels[mois_idx] = st.number_input(
                        "Impôt",
                        min_value=0.0,
                        value=st.session_state.impots_mensuels[mois_idx],
                        step=10.0,
                        key=f"imp_{mois_idx}",
                        format="%.2f",
                        label_visibility="collapsed"
                    )

                if j < 3:
                    st.markdown("")

# ============================================================================
# SECTION 3: REVENUS EXCEPTIONNELS
# ============================================================================

st.markdown("---")
st.header("🎁 Revenus Exceptionnels")
st.caption("Primes, bonus, revenus complémentaires imposables...")

col1, col2 = st.columns([3, 1])
with col1:
    nouveau_montant = st.number_input(
        "Montant du revenu exceptionnel",
        min_value=0.0,
        value=0.0,
        step=100.0,
        key="nouveau_except"
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Ajouter", type="primary", use_container_width=True):
        if nouveau_montant > 0:
            st.session_state.revenus_exceptionnels.append(nouveau_montant)
            st.success(f"✅ Ajouté: {formater_euros(nouveau_montant)}")
            st.rerun()

# Liste des revenus exceptionnels
if st.session_state.revenus_exceptionnels:
    st.markdown("**Liste des revenus exceptionnels:**")
    for idx, montant in enumerate(st.session_state.revenus_exceptionnels):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.write(f"#{idx + 1}: **{formater_euros(montant)}**")
        with col2:
            if st.button("🗑️", key=f"del_{idx}", use_container_width=True):
                st.session_state.revenus_exceptionnels.pop(idx)
                st.rerun()

# ============================================================================
# SECTION 4: CALCULS ET RÉSULTATS
# ============================================================================

st.markdown("---")
st.header("📊 Résultats")

# Calculs
total_revenus_mensuels = sum(st.session_state.revenus_mensuels)
total_revenus_exceptionnels = sum(st.session_state.revenus_exceptionnels)
total_revenus_net = total_revenus_mensuels + total_revenus_exceptionnels
revenu_avec_abattement = total_revenus_net * 0.90
resultat_impot = calculer_impot(revenu_avec_abattement, nb_parts)
total_impots_payes = sum(st.session_state.impots_mensuels)
solde_impot = resultat_impot["impot_total"] - total_impots_payes

# Métriques principales (responsive)
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "💵 Revenus totaux",
        formater_euros(total_revenus_net)
    )

with col2:
    st.metric(
        "📉 Revenu imposable",
        formater_euros(revenu_avec_abattement),
        delta="-10% abattement"
    )

with col3:
    st.metric(
        "💰 Impôt dû",
        formater_euros(resultat_impot["impot_total"])
    )

# ============================================================================
# SECTION 5: BILAN PRÉLÈVEMENTS
# ============================================================================

st.markdown("---")
st.subheader("🏦 Bilan des Prélèvements")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "💳 Déjà payé",
        formater_euros(total_impots_payes)
    )

with col2:
    st.metric(
        "💰 À payer",
        formater_euros(resultat_impot["impot_total"])
    )

with col3:
    if solde_impot > 0:
        st.metric(
            "⚠️ Reste à payer",
            formater_euros(solde_impot),
            delta=f"{solde_impot:.2f}",
            delta_color="inverse"
        )
    elif solde_impot < 0:
        st.metric(
            "✅ Remboursement",
            formater_euros(abs(solde_impot)),
            delta=f"{abs(solde_impot):.2f}",
            delta_color="normal"
        )
    else:
        st.metric("✅ Solde", "0,00 €")

# Message contextuel
if solde_impot > 0:
    st.error(f"⚠️ Vous devrez payer **{formater_euros(solde_impot)}** supplémentaires.")
elif solde_impot < 0:
    st.success(f"✅ Vous recevrez un remboursement de **{formater_euros(abs(solde_impot))}**.")
else:
    st.info("✅ Vos prélèvements sont parfaitement ajustés.")

# Indicateurs complémentaires
st.markdown("")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Revenus mensuels", formater_euros(total_revenus_mensuels))

with col2:
    st.metric("Revenus except.", formater_euros(total_revenus_exceptionnels))

with col3:
    taux_moyen = (resultat_impot["impot_total"] / revenu_avec_abattement * 100) if revenu_avec_abattement > 0 else 0
    st.metric("Taux moyen", f"{taux_moyen:.2f}%")

with col4:
    st.metric("Quotient familial", formater_euros(resultat_impot["quotient"]))

# ============================================================================
# SECTION 6: DÉTAIL DU CALCUL
# ============================================================================

if revenu_avec_abattement > 0:
    st.markdown("---")
    with st.expander("📋 Détail du calcul par tranche"):
        st.info(f"💡 Calcul basé sur **{nb_parts} part(s)** - Quotient: {formater_euros(resultat_impot['quotient'])}")

        df_tranches = pd.DataFrame(resultat_impot["detail_tranches"])
        if not df_tranches.empty:
            df_tranches['base'] = df_tranches['base'].apply(formater_euros)
            df_tranches['impot'] = df_tranches['impot'].apply(formater_euros)
            df_tranches.columns = ["Tranche", "Taux", "Base imposable", "Impôt"]

            st.dataframe(df_tranches, use_container_width=True, hide_index=True)

            st.success(f"**Impôt par part:** {formater_euros(resultat_impot['impot_par_part'])}")
            st.success(f"**Impôt total ({nb_parts} part(s)):** {formater_euros(resultat_impot['impot_total'])}")

# ============================================================================
# SECTION 7: RÉCAPITULATIF MENSUEL
# ============================================================================

with st.expander("📊 Récapitulatif mensuel détaillé"):
    recap_data = []
    for i, mois_nom in enumerate(MOIS):
        recap_data.append({
            "Mois": mois_nom,
            "Revenu net": formater_euros(st.session_state.revenus_mensuels[i]),
            "Impôt prélevé": formater_euros(st.session_state.impots_mensuels[i])
        })

    df_recap = pd.DataFrame(recap_data)
    st.dataframe(df_recap, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total revenus", formater_euros(total_revenus_mensuels))
    with col2:
        st.metric("Total prélevé", formater_euros(total_impots_payes))

# ============================================================================
# SECTION 8: BARÈME D'IMPOSITION
# ============================================================================

with st.expander("📖 Barème d'imposition 2024"):
    st.markdown(f"### Barème de l'impôt {annee}")

    for tranche in TRANCHES_IMPOSITION:
        if tranche['max'] == float('inf'):
            st.markdown(f"- Plus de **{tranche['min']:,.0f} €** → **{tranche['label']}**".replace(",", " "))
        else:
            st.markdown(
                f"- De **{tranche['min']:,.0f} €** à **{tranche['max']:,.0f} €** → **{tranche['label']}**".replace(",",
                                                                                                                   " "))

    st.info("ℹ️ Barème appliqué au quotient familial (revenu imposable / nombre de parts)")

# ============================================================================
# SECTION 9: ACTIONS
# ============================================================================

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Réinitialiser", type="secondary", use_container_width=True):
        reinitialiser()
        st.success("✅ Données réinitialisées!")
        st.rerun()

with col2:
    # Possibilité d'export CSV
    if total_revenus_net > 0:
        recap_export = pd.DataFrame({
            "Catégorie": ["Revenus mensuels", "Revenus exceptionnels", "Total revenus nets",
                          "Revenu imposable (après abattement)", "Impôt dû", "Impôt déjà payé", "Solde"],
            "Montant (€)": [total_revenus_mensuels, total_revenus_exceptionnels, total_revenus_net,
                            revenu_avec_abattement, resultat_impot["impot_total"], total_impots_payes, solde_impot]
        })

        csv = recap_export.to_csv(index=False, encoding='utf-8')
        st.download_button(
            "📥 Télécharger le résumé",
            data=csv,
            file_name=f"impots_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("*💰 Calculateur d'impôts - Barème 2024 - France*")
st.caption("⚠️ Outil indicatif. Pour un calcul officiel, consultez impots.gouv.fr")
