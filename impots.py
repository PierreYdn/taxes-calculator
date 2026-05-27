import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import unicodedata

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
# BARÈMES D'IMPOSITION PAR ANNÉE
# ============================================================================

BAREMES_IMPOSITION = {
    2026: [
        {"min": 0, "max": 11600, "taux": 0.00, "label": "0%"},
        {"min": 11600, "max": 29579, "taux": 0.11, "label": "11%"},
        {"min": 29579, "max": 84577, "taux": 0.30, "label": "30%"},
        {"min": 84577, "max": 181917, "taux": 0.41, "label": "41%"},
        {"min": 181917, "max": float('inf'), "taux": 0.45, "label": "45%"}
    ],
    2025: [
        {"min": 0, "max": 11497, "taux": 0.00, "label": "0%"},
        {"min": 11497, "max": 29315, "taux": 0.11, "label": "11%"},
        {"min": 29315, "max": 83823, "taux": 0.30, "label": "30%"},
        {"min": 83823, "max": 180294, "taux": 0.41, "label": "41%"},
        {"min": 180294, "max": float('inf'), "taux": 0.45, "label": "45%"}
    ],
    2024: [
        {"min": 0, "max": 11294, "taux": 0.00, "label": "0%"},
        {"min": 11294, "max": 28797, "taux": 0.11, "label": "11%"},
        {"min": 28797, "max": 82341, "taux": 0.30, "label": "30%"},
        {"min": 82341, "max": 177106, "taux": 0.41, "label": "41%"},
        {"min": 177106, "max": float('inf'), "taux": 0.45, "label": "45%"}
    ]
}

MOIS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]


# ============================================================================
# FONCTIONS DE CALCUL
# ============================================================================

def calculer_impot(revenu_imposable, nb_parts=1, tranches=None):
    """Calcule l'impôt sur le revenu selon le barème progressif français"""
    if tranches is None:
        tranches = BAREMES_IMPOSITION[max(BAREMES_IMPOSITION.keys())]

    quotient = revenu_imposable / nb_parts
    impot_par_part = 0
    detail_tranches = []

    for tranche in tranches:
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


def normaliser_texte(texte):
    """Normalise un texte pour comparaison souple (minuscules, sans accents)."""
    if texte is None:
        return ""
    txt = str(texte).strip().lower()
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return txt


def index_mois_depuis_valeur(valeur):
    """Retourne l'index de mois (0-11) depuis un nom ou un numéro."""
    if pd.isna(valeur):
        return None

    if isinstance(valeur, (int, float)):
        mois_num = int(valeur)
        return mois_num - 1 if 1 <= mois_num <= 12 else None

    valeur_norm = normaliser_texte(valeur)
    if valeur_norm.isdigit():
        mois_num = int(valeur_norm)
        return mois_num - 1 if 1 <= mois_num <= 12 else None

    for idx, mois_nom in enumerate(MOIS):
        mois_norm = normaliser_texte(mois_nom)
        if valeur_norm == mois_norm or valeur_norm.startswith(mois_norm[:3]):
            return idx

    return None


def mapper_colonnes_import(colonnes):
    """Mappe les noms de colonnes importées vers les champs attendus."""
    mapping = {}
    alias = {
        "mois": ["mois", "month", "mois_numero", "numero_mois"],
        "revenu_net": ["revenu_net", "revenu_net_imposable", "net_imposable", "net_fiscal"],
        "impot_preleve": ["impot_preleve", "impot", "pas", "prelevement_source", "prelevement_a_la_source"],
        "revenu_exceptionnel": ["revenu_exceptionnel", "revenus_exceptionnels", "exceptionnel"]
    }

    colonnes_norm = {normaliser_texte(col): col for col in colonnes}

    for cible, aliases in alias.items():
        for a in aliases:
            if a in colonnes_norm:
                mapping[cible] = colonnes_norm[a]
                break

    return mapping


def generer_resume_pdf(annee, nb_parts, total_revenus_mensuels, total_revenus_exceptionnels,
                       total_revenus_net, revenu_avec_abattement, resultat_impot,
                       total_impots_payes, solde_impot):
    """Génère un PDF récapitulatif lisible du calcul d'impôt"""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Calculateur d'impots - Resume", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Date d'edition: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(0, 6, f"Annee du bareme applique: {annee}", ln=True)
    pdf.cell(0, 6, f"Nombre de parts: {nb_parts}", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Synthese", ln=True)
    pdf.set_font("Helvetica", "", 10)

    lignes_synthese = [
        ("Revenus mensuels", formater_euros(total_revenus_mensuels)),
        ("Revenus exceptionnels", formater_euros(total_revenus_exceptionnels)),
        ("Total revenus nets", formater_euros(total_revenus_net)),
        ("Revenu imposable (abattement 10%)", formater_euros(revenu_avec_abattement)),
        ("Impot du", formater_euros(resultat_impot["impot_total"])),
        ("Impot deja preleve", formater_euros(total_impots_payes)),
        ("Solde", formater_euros(solde_impot))
    ]

    for libelle, valeur in lignes_synthese:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(120, 7, libelle)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, valeur, ln=True)

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Detail par tranche", ln=True)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(80, 7, "Tranche", border=1)
    pdf.cell(20, 7, "Taux", border=1)
    pdf.cell(40, 7, "Base", border=1)
    pdf.cell(0, 7, "Impot", border=1, ln=True)

    pdf.set_font("Helvetica", "", 9)
    for ligne in resultat_impot["detail_tranches"]:
        pdf.cell(80, 7, str(ligne["tranche"]).replace("€", "EUR"), border=1)
        pdf.cell(20, 7, ligne["taux"], border=1)
        pdf.cell(40, 7, formater_euros(ligne["base"]).replace("€", "EUR"), border=1)
        pdf.cell(0, 7, formater_euros(ligne["impot"]).replace("€", "EUR"), border=1, ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, "Document indicatif. Pour un calcul officiel, utilisez le simulateur de impots.gouv.fr")

    contenu = pdf.output(dest="S")
    if isinstance(contenu, bytearray):
        return bytes(contenu)
    if isinstance(contenu, str):
        return contenu.encode("latin-1", errors="replace")
    return contenu


def afficher_contenu_bienvenue():
    """Contenu explicatif affiché dans la pop-up de bienvenue et dans l'aide."""
    st.markdown("""
    Bienvenue sur ce calculateur d'impôt sur le revenu (France).

    **Objectif de l'outil**
    - Estimer l'impôt selon le barème progressif sélectionné
    - Comparer l'impôt théorique avec le prélèvement à la source déjà payé
    - Voir le détail par tranche et exporter un rapport

    **Comment l'utiliser**
    1. Choisissez l'année de barème et votre nombre de parts.
    2. Renseignez, mois par mois, le **net imposable** et le **PAS prélevé**.
    3. Ajoutez vos revenus exceptionnels si nécessaire.
    4. Consultez le solde: reste à payer ou remboursement estimé.

    **Important**
    - Outil indicatif, non officiel.
    - Pour un calcul opposable, vérifiez sur impots.gouv.fr.
    """)


if hasattr(st, "dialog"):
    @st.dialog("👋 Bienvenue")
    def afficher_popup_bienvenue():
        afficher_contenu_bienvenue()
        if st.button("Entrer dans l'application", type="primary", use_container_width=True):
            st.session_state.bienvenue_validee = True
            st.rerun()
else:
    def afficher_popup_bienvenue():
        st.info("Bienvenue")
        afficher_contenu_bienvenue()
        if st.button("Entrer dans l'application", type="primary", use_container_width=True):
            st.session_state.bienvenue_validee = True
            st.rerun()


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
    if 'bienvenue_validee' not in st.session_state:
        st.session_state.bienvenue_validee = False


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
annee_par_defaut = max(BAREMES_IMPOSITION.keys())
st.caption(f"Calculez votre impôt sur le revenu {annee_par_defaut}")
st.markdown("---")

if not st.session_state.bienvenue_validee:
    afficher_popup_bienvenue()
    st.stop()

with st.expander("ℹ️ Aide et message de bienvenue", expanded=False):
    afficher_contenu_bienvenue()

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
            sorted(BAREMES_IMPOSITION.keys(), reverse=True),
            help="Année du barème appliqué. Exemple: revenus 2025 déclarés en 2026 = barème 2026."
        )

    with col3:
        mode = st.selectbox(
            "Affichage",
            ["Auto", "Mobile", "Desktop"],
            help="Mode d'affichage des mois"
        )

    mode_saisie = st.radio(
        "Mode de saisie",
        ["Mensuel (détail par mois)", "Annuel (cumul fiche de paie de décembre)"],
        index=1,
        help="Choisissez soit la saisie mois par mois, soit les cumuls annuels indiqués sur la fiche de paie de décembre.",
        horizontal=True
    )

# ============================================================================
# SECTION 2: SAISIE DES REVENUS ET PRÉLÈVEMENTS
# ============================================================================

st.markdown("---")
st.header("📅 Revenus et Prélèvements")

if mode_saisie == "Mensuel (détail par mois)":
    revenu_annuel_saisi = 0.0
    impot_annuel_saisi = 0.0

    with st.expander("📥 Importer un fichier CSV/Excel", expanded=False):
        st.markdown("""
        **Structure attendue (colonnes obligatoires):**
        - `mois`: numéro de mois (`1` à `12`) ou nom du mois (`Janvier`, `Fevrier`, etc.)
        - `revenu_net`: net imposable du mois
        - `impot_preleve`: prélèvement à la source du mois

        **Colonne optionnelle:**
        - `revenu_exceptionnel`: montant exceptionnel à ajouter

        Unités attendues: montants en euros, avec point ou virgule décimale selon votre fichier.
        """)

        template_df = pd.DataFrame({
            "mois": MOIS,
            "revenu_net": [0.0] * 12,
            "impot_preleve": [0.0] * 12,
            "revenu_exceptionnel": [0.0] * 12
        })
        st.download_button(
            "⬇️ Télécharger le template CSV",
            data=template_df.to_csv(index=False),
            file_name="template_import_impots.csv",
            mime="text/csv"
        )

        fichier_import = st.file_uploader(
            "Choisissez un fichier CSV ou Excel",
            type=["csv", "xlsx"],
            accept_multiple_files=False,
            help="Le fichier doit contenir les colonnes décrites ci-dessus"
        )

        if fichier_import is not None:
            try:
                if fichier_import.name.lower().endswith(".csv"):
                    df_import = pd.read_csv(fichier_import, sep=None, engine="python")
                else:
                    df_import = pd.read_excel(fichier_import)

                mapping = mapper_colonnes_import(df_import.columns)
                champs_obligatoires = ["mois", "revenu_net", "impot_preleve"]
                champs_manquants = [c for c in champs_obligatoires if c not in mapping]

                if champs_manquants:
                    st.error(
                        "Colonnes obligatoires manquantes: " + ", ".join(champs_manquants) +
                        ". Utilisez le template pour éviter les erreurs."
                    )
                else:
                    revenus_importes = [0.0] * 12
                    impots_importes = [0.0] * 12
                    exceptionnels_importes = []
                    lignes_ignorees = 0

                    for _, ligne in df_import.iterrows():
                        idx_mois = index_mois_depuis_valeur(ligne[mapping["mois"]])
                        if idx_mois is None:
                            lignes_ignorees += 1
                            continue

                        revenu = pd.to_numeric(ligne[mapping["revenu_net"]], errors="coerce")
                        impot = pd.to_numeric(ligne[mapping["impot_preleve"]], errors="coerce")

                        revenus_importes[idx_mois] += float(0 if pd.isna(revenu) else revenu)
                        impots_importes[idx_mois] += float(0 if pd.isna(impot) else impot)

                        if "revenu_exceptionnel" in mapping:
                            rev_exc = pd.to_numeric(ligne[mapping["revenu_exceptionnel"]], errors="coerce")
                            if not pd.isna(rev_exc) and float(rev_exc) > 0:
                                exceptionnels_importes.append(float(rev_exc))

                    st.dataframe(df_import.head(10), use_container_width=True)

                    if st.button("✅ Appliquer cet import", use_container_width=True, type="primary"):
                        st.session_state.revenus_mensuels = revenus_importes
                        st.session_state.impots_mensuels = impots_importes
                        st.session_state.revenus_exceptionnels = exceptionnels_importes
                        if lignes_ignorees > 0:
                            st.warning(f"Import appliqué avec {lignes_ignorees} ligne(s) ignorée(s) (mois non reconnu).")
                        else:
                            st.success("Import appliqué avec succès.")
                        st.rerun()
            except Exception as exc:
                st.error(f"Impossible de lire le fichier: {exc}")

    col_help1, col_help2 = st.columns(2)
    with col_help1:
        with st.popover("ℹ️ Où trouver le revenu net à saisir ?"):
            st.markdown("""
            Saisissez le **net imposable du mois** (et non le net à payer).

            Votre cas: si votre bulletin affiche **NET IMPOSABLE POUR BP**, c'est bien
            le montant attendu dans cette application.

            Cette ligne se trouve souvent dans la section de calcul du
            **prélèvement à la source**, avec le montant du mois en cours et le
            cumul depuis le début de l'année.

            Sur le bulletin de paie, cherchez une ligne du type :
            - Net imposable
            - NET IMPOSABLE POUR BP
            - Net fiscal
            - Cumul net imposable (puis faites la différence avec le mois précédent)

            À ne pas utiliser :
            - Net à payer avant impôt
            - Net payé
            """)

    with col_help2:
        with st.popover("ℹ️ Où trouver l'impôt prélevé ?"):
            st.markdown("""
            Saisissez le **montant du prélèvement à la source (PAS)** déjà retenu ce mois.

            Sur le bulletin de paie, cherchez :
            - Prélèvement à la source
            - Impôt sur le revenu prélevé à la source
            - PAS

            Si le mois est exonéré ou sans retenue, laissez **0**.
            """)

    afficher_mode_mobile = (mode == "Mobile") or (mode == "Auto")

    col_leg1, col_leg2 = st.columns(2)
    with col_leg1:
        st.markdown("**💵 Revenu net**")
    with col_leg2:
        st.markdown("**🏦 Impôt prélevé**")

    st.markdown("")

    if afficher_mode_mobile:
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
else:
    st.info("Mode annuel: renseignez les cumuls de votre fiche de paie de décembre.")

    col_ann1, col_ann2 = st.columns(2)
    with col_ann1:
        revenu_annuel_saisi = st.number_input(
            "Revenu net imposable cumulé depuis le début de l'année",
            min_value=0.0,
            value=0.0,
            step=100.0,
            key="revenu_cumule_annuel",
            help="Exemple de libellé: NET IMPOSABLE POUR BP (cumul annuel)."
        )

    with col_ann2:
        impot_annuel_saisi = st.number_input(
            "Impôt prélevé cumulé depuis le début de l'année",
            min_value=0.0,
            value=0.0,
            step=10.0,
            key="impot_cumule_annuel",
            help="Montant cumulé du prélèvement à la source depuis janvier."
        )

    with st.expander("ℹ️ Où trouver ces montants sur la fiche de décembre ?", expanded=False):
        st.markdown("""
        Sur la fiche de paie de décembre, récupérez les **cumuls annuels** :
        - le net imposable cumulé (souvent proche de `NET IMPOSABLE POUR BP`),
        - le prélèvement à la source cumulé depuis le début d'année.

        Ces deux valeurs permettent une saisie rapide sans détail mois par mois.
        """)

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
if mode_saisie == "Mensuel (détail par mois)":
    total_revenus_mensuels = sum(st.session_state.revenus_mensuels)
    total_impots_payes = sum(st.session_state.impots_mensuels)
else:
    total_revenus_mensuels = revenu_annuel_saisi
    total_impots_payes = impot_annuel_saisi

total_revenus_exceptionnels = sum(st.session_state.revenus_exceptionnels)
total_revenus_net = total_revenus_mensuels + total_revenus_exceptionnels
revenu_avec_abattement = total_revenus_net * 0.90
bareme_selectionne = BAREMES_IMPOSITION[annee]
resultat_impot = calculer_impot(revenu_avec_abattement, nb_parts, bareme_selectionne)
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
    libelle_revenus = "Revenus mensuels" if mode_saisie == "Mensuel (détail par mois)" else "Revenus cumulés"
    st.metric(libelle_revenus, formater_euros(total_revenus_mensuels))

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
# SECTION 7: RÉCAPITULATIF
# ============================================================================

if mode_saisie == "Mensuel (détail par mois)":
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
else:
    with st.expander("📊 Récapitulatif annuel saisi"):
        st.metric("Revenu net imposable cumulé", formater_euros(total_revenus_mensuels))
        st.metric("Impôt prélevé cumulé", formater_euros(total_impots_payes))

# ============================================================================
# SECTION 8: BARÈME D'IMPOSITION
# ============================================================================

with st.expander(f"📖 Barème d'imposition {annee}"):
    st.markdown(f"### Barème de l'impôt {annee}")

    for tranche in bareme_selectionne:
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
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Réinitialiser", type="secondary", use_container_width=True):
        reinitialiser()
        st.success("✅ Données réinitialisées!")
        st.rerun()

with col2:
    if st.button("🧹 Tout effacer", type="secondary", use_container_width=True,
                 help="Supprime toutes les saisies revenus/impôts et revenus exceptionnels"):
        reinitialiser()
        st.warning("Toutes les valeurs ont été effacées.")
        st.rerun()

with col3:
    # Export PDF + CSV
    if total_revenus_net > 0:
        pdf_data = generer_resume_pdf(
            annee=annee,
            nb_parts=nb_parts,
            total_revenus_mensuels=total_revenus_mensuels,
            total_revenus_exceptionnels=total_revenus_exceptionnels,
            total_revenus_net=total_revenus_net,
            revenu_avec_abattement=revenu_avec_abattement,
            resultat_impot=resultat_impot,
            total_impots_payes=total_impots_payes,
            solde_impot=solde_impot
        )

        st.download_button(
            "📄 Télécharger le rapport PDF",
            data=pdf_data,
            file_name=f"rapport_impots_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        recap_export = pd.DataFrame({
            "Catégorie": ["Revenus mensuels", "Revenus exceptionnels", "Total revenus nets",
                           "Revenu imposable (après abattement)", "Impôt dû", "Impôt déjà payé", "Solde"],
            "Montant (€)": [total_revenus_mensuels, total_revenus_exceptionnels, total_revenus_net,
                             revenu_avec_abattement, resultat_impot["impot_total"], total_impots_payes, solde_impot]
        })
        csv = recap_export.to_csv(index=False, encoding='utf-8')

        st.download_button(
            "🧾 Télécharger le CSV",
            data=csv,
            file_name=f"impots_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(f"*💰 Calculateur d'impôts - Barème {annee} - France*")
st.caption("⚠️ Outil indicatif. Pour un calcul officiel, consultez impots.gouv.fr")
