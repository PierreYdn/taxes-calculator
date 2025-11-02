import streamlit as st
import pandas as pd
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Calculateur d'Impôts",
    page_icon="💰",
    layout="wide"
)

# === BARÈME D'IMPOSITION 2024 (France) ===
# Les tranches sont définies pour 1 part fiscale
TRANCHES_IMPOSITION = [
    {"min": 0, "max": 11294, "taux": 0.00, "label": "0%"},
    {"min": 11294, "max": 28797, "taux": 0.11, "label": "11%"},
    {"min": 28797, "max": 82341, "taux": 0.30, "label": "30%"},
    {"min": 82341, "max": 177106, "taux": 0.41, "label": "41%"},
    {"min": 177106, "max": float('inf'), "taux": 0.45, "label": "45%"}
]


def calculer_impot(revenu_imposable, nb_parts=1):
    """
    Calcule l'impôt sur le revenu selon le barème progressif français

    Args:
        revenu_imposable: Montant du revenu imposable (après abattement 10%)
        nb_parts: Nombre de parts fiscales

    Returns:
        dict: Détails du calcul (impôt total et détail par tranche)
    """
    # Calculer le quotient familial
    quotient = revenu_imposable / nb_parts

    impot_par_part = 0
    detail_tranches = []

    for i, tranche in enumerate(TRANCHES_IMPOSITION):
        if quotient > tranche["min"]:
            # Montant imposable dans cette tranche
            base_tranche = min(quotient, tranche["max"]) - tranche["min"]
            impot_tranche = base_tranche * tranche["taux"]
            impot_par_part += impot_tranche

            detail_tranches.append({
                "tranche": f"{tranche['min']:,.0f} € à {tranche['max']:,.0f} €" if tranche['max'] != float(
                    'inf') else f"Plus de {tranche['min']:,.0f} €",
                "taux": tranche["label"],
                "base": base_tranche,
                "impot": impot_tranche
            })

    # Impôt total (reconstitution avec le nombre de parts)
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


def reinitialiser():
    """Réinitialise tous les champs"""
    # Réinitialiser les revenus mensuels
    for i in range(12):
        if f"mois_{i}" in st.session_state:
            st.session_state[f"mois_{i}"] = 0.0
        if f"impot_mois_{i}" in st.session_state:
            st.session_state[f"impot_mois_{i}"] = 0.0

    # Réinitialiser les revenus exceptionnels
    st.session_state.revenus_exceptionnels = []

    # Réinitialiser le champ de saisie nouveau revenu
    if "nouveau_exceptionnel" in st.session_state:
        st.session_state["nouveau_exceptionnel"] = 0.0


# === INTERFACE PRINCIPALE ===
st.title("💰 Calculateur d'Impôts sur le Revenu")
st.markdown("---")

# === SECTION 1: Configuration ===
st.header("⚙️ Configuration")

col1, col2 = st.columns(2)
with col1:
    nb_parts = st.number_input(
        "Nombre de parts fiscales",
        min_value=1.0,
        max_value=10.0,
        value=1.0,
        step=0.5,
        help="1 part = célibataire, 2 parts = couple, +0.5 par enfant..."
    )

with col2:
    annee = st.selectbox(
        "Année d'imposition",
        [2024, 2023, 2022],
        help="Barème applicable (actuellement 2024)"
    )

st.markdown("---")

# === SECTION 2: Revenus mensuels et impôts prélevés ===
st.header("📅 Revenus Mensuels et Prélèvements à la Source")

# Initialiser les revenus mensuels et impôts dans session_state
if 'revenus_mensuels' not in st.session_state:
    st.session_state.revenus_mensuels = [0.0] * 12
if 'impots_mensuels' not in st.session_state:
    st.session_state.impots_mensuels = [0.0] * 12

# Afficher 3 colonnes de 4 mois chacune
mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

# Légende
col_legend1, col_legend2 = st.columns(2)
with col_legend1:
    st.markdown("**💵 Revenu net (avant prélèvement)**")
with col_legend2:
    st.markdown("**🏦 Impôt prélevé à la source**")

st.markdown("---")

cols = st.columns(3)
for i in range(3):
    with cols[i]:
        for j in range(4):
            mois_index = i * 4 + j

            # Afficher le nom du mois
            st.markdown(f"### {mois[mois_index]}")

            # Deux colonnes pour revenu et impôt
            col_rev, col_imp = st.columns(2)

            with col_rev:
                valeur_revenu = st.number_input(
                    "Revenu",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    key=f"mois_{mois_index}",
                    format="%.2f",
                    label_visibility="collapsed"
                )
                st.session_state.revenus_mensuels[mois_index] = valeur_revenu

            with col_imp:
                valeur_impot = st.number_input(
                    "Impôt",
                    min_value=0.0,
                    value=0.0,
                    step=10.0,
                    key=f"impot_mois_{mois_index}",
                    format="%.2f",
                    label_visibility="collapsed"
                )
                st.session_state.impots_mensuels[mois_index] = valeur_impot

            st.markdown("---")

st.markdown("---")

# === SECTION 3: Revenus exceptionnels ===
st.header("🎁 Revenus Exceptionnels Imposables")

st.markdown("*Primes, bonus, revenus complémentaires imposables...*")

# Initialiser les revenus exceptionnels dans session_state
if 'revenus_exceptionnels' not in st.session_state:
    st.session_state.revenus_exceptionnels = []

# Bouton pour ajouter un revenu exceptionnel
col1, col2 = st.columns([3, 1])
with col1:
    nouveau_montant = st.number_input(
        "Montant du revenu exceptionnel (net)",
        min_value=0.0,
        value=0.0,
        step=100.0,
        key="nouveau_exceptionnel"
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Ajouter", type="primary"):
        if nouveau_montant > 0:
            st.session_state.revenus_exceptionnels.append(nouveau_montant)
            st.session_state["nouveau_exceptionnel"] = 0.0
            st.success(f"Ajouté: {formater_euros(nouveau_montant)}")
            st.rerun()

# Afficher les revenus exceptionnels existants
if st.session_state.revenus_exceptionnels:
    st.subheader("Liste des revenus exceptionnels:")
    for idx, montant in enumerate(st.session_state.revenus_exceptionnels):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"• Revenu #{idx + 1}: **{formater_euros(montant)}**")
        with col2:
            if st.button("🗑️", key=f"delete_{idx}"):
                st.session_state.revenus_exceptionnels.pop(idx)
                st.rerun()

st.markdown("---")

# === SECTION 4: Calculs ===
st.header("📊 Résultats")

# Calculer les totaux
total_revenus_mensuels = sum(st.session_state.revenus_mensuels)
total_revenus_exceptionnels = sum(st.session_state.revenus_exceptionnels)
total_revenus_net = total_revenus_mensuels + total_revenus_exceptionnels

# Calcul avec abattement de 10%
revenu_avec_abattement = total_revenus_net * 0.90

# Calculer l'impôt dû
resultat_impot = calculer_impot(revenu_avec_abattement, nb_parts)

# Calculer l'impôt déjà payé
total_impots_payes = sum(st.session_state.impots_mensuels)

# Calculer le solde (à payer ou à rembourser)
solde_impot = resultat_impot["impot_total"] - total_impots_payes

# Afficher les résultats principaux
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "💵 Revenus nets totaux",
        formater_euros(total_revenus_net),
        help="Somme des revenus mensuels + exceptionnels"
    )

with col2:
    st.metric(
        "📉 Revenu imposable",
        formater_euros(revenu_avec_abattement),
        delta=f"-10% (abattement)",
        delta_color="normal",
        help="Revenu après abattement forfaitaire de 10%"
    )

with col3:
    st.metric(
        "💰 Impôt dû pour l'année",
        formater_euros(resultat_impot["impot_total"]),
        help="Montant total de l'impôt calculé"
    )

# === Nouvelle section: Bilan des prélèvements ===
st.markdown("---")
st.subheader("🏦 Bilan des Prélèvements à la Source")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "💳 Impôts déjà payés",
        formater_euros(total_impots_payes),
        help="Total des prélèvements à la source effectués"
    )

with col2:
    st.metric(
        "💰 Impôt dû",
        formater_euros(resultat_impot["impot_total"]),
        help="Montant calculé selon le barème"
    )

with col3:
    if solde_impot > 0:
        st.metric(
            "⚠️ Reste à payer",
            formater_euros(solde_impot),
            delta=f"{solde_impot:.2f}",
            delta_color="inverse",
            help="Vous devrez payer ce montant supplémentaire"
        )
    elif solde_impot < 0:
        st.metric(
            "✅ Remboursement attendu",
            formater_euros(abs(solde_impot)),
            delta=f"{abs(solde_impot):.2f}",
            delta_color="normal",
            help="Vous devriez recevoir un remboursement"
        )
    else:
        st.metric(
            "✅ Solde",
            "0,00 €",
            help="Vos prélèvements correspondent exactement à l'impôt dû"
        )

# Message contextuel selon le solde
if solde_impot > 0:
    st.error(
        f"⚠️ **Attention :** Vous devrez régler **{formater_euros(solde_impot)}** supplémentaires lors de la régularisation.")
elif solde_impot < 0:
    st.success(
        f"✅ **Bonne nouvelle :** Vous devriez recevoir un remboursement de **{formater_euros(abs(solde_impot))}**.")
else:
    st.info("✅ **Parfait :** Vos prélèvements sont parfaitement ajustés à votre impôt dû.")

# Indicateurs supplémentaires
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Revenus mensuels",
        formater_euros(total_revenus_mensuels)
    )

with col2:
    st.metric(
        "Revenus exceptionnels",
        formater_euros(total_revenus_exceptionnels)
    )

with col3:
    taux_moyen = (resultat_impot["impot_total"] / revenu_avec_abattement * 100) if revenu_avec_abattement > 0 else 0
    st.metric(
        "Taux moyen d'imposition",
        f"{taux_moyen:.2f}%",
        help="Impôt / Revenu imposable"
    )

with col4:
    st.metric(
        "Quotient familial",
        formater_euros(resultat_impot["quotient"]),
        help="Revenu imposable / Nombre de parts"
    )

# === SECTION 5: Détail du calcul par tranche ===
if revenu_avec_abattement > 0:
    st.markdown("---")
    st.header("📋 Détail du Calcul par Tranche")

    st.info(f"💡 **Calcul basé sur {nb_parts} part(s) fiscale(s)**\n\n"
            f"Quotient familial: {formater_euros(resultat_impot['quotient'])}")

    # Créer un DataFrame pour afficher les tranches
    df_tranches = pd.DataFrame(resultat_impot["detail_tranches"])

    if not df_tranches.empty:
        df_tranches['base'] = df_tranches['base'].apply(lambda x: formater_euros(x))
        df_tranches['impot'] = df_tranches['impot'].apply(lambda x: formater_euros(x))

        df_tranches.columns = ["Tranche", "Taux", "Base imposable", "Impôt"]

        st.dataframe(
            df_tranches,
            use_container_width=True,
            hide_index=True
        )

        st.success(f"**Impôt calculé pour 1 part:** {formater_euros(resultat_impot['impot_par_part'])}")
        st.success(f"**Impôt total pour {nb_parts} part(s):** {formater_euros(resultat_impot['impot_total'])}")

# === SECTION 6: Récapitulatif mensuel ===
st.markdown("---")
with st.expander("📊 Voir le récapitulatif mensuel détaillé"):
    st.subheader("Récapitulatif mois par mois")

    # Créer un DataFrame récapitulatif
    recap_data = []
    for i, mois_nom in enumerate(mois):
        recap_data.append({
            "Mois": mois_nom,
            "Revenu net": formater_euros(st.session_state.revenus_mensuels[i]),
            "Impôt prélevé": formater_euros(st.session_state.impots_mensuels[i])
        })

    df_recap = pd.DataFrame(recap_data)
    st.dataframe(df_recap, use_container_width=True, hide_index=True)

    # Ligne de total
    st.markdown("### Totaux")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total revenus mensuels", formater_euros(total_revenus_mensuels))
    with col2:
        st.metric("Total impôts prélevés", formater_euros(total_impots_payes))

# === SECTION 7: Barème d'imposition ===
st.markdown("---")
with st.expander("📖 Voir le barème d'imposition 2024"):
    st.markdown(f"### Barème de l'impôt sur le revenu {annee}")

    for tranche in TRANCHES_IMPOSITION:
        if tranche['max'] == float('inf'):
            st.markdown(f"- **Plus de {tranche['min']:,.0f} €** → **{tranche['label']}**")
        else:
            st.markdown(f"- **De {tranche['min']:,.0f} € à {tranche['max']:,.0f} €** → **{tranche['label']}**")

    st.info("ℹ️ Ce barème s'applique au quotient familial (revenu imposable / nombre de parts)")

# === SECTION 8: Réinitialisation ===
st.markdown("---")
if st.button("🔄 Réinitialiser tous les champs", type="secondary", on_click=reinitialiser):
    st.success("✅ Tous les champs ont été réinitialisés!")
    st.rerun()


# Footer
st.markdown("---")
st.markdown("*💡 Calculateur d'impôts - Barème 2024 - France*")
st.caption("⚠️ Cet outil est fourni à titre indicatif. Pour un calcul officiel, consultez le site des impôts.")