# 💰 Calculateur d'Impôts sur le Revenu

Application Streamlit pour calculer vos impôts sur le revenu en France.

## Fonctionnalités
- Saisie des revenus mensuels
- Gestion des revenus exceptionnels
- Suivi des prélèvements à la source
- Barème progressif français par année (ex: revenus 2025 -> barème 2026)
- Détail par tranche d'imposition
- Import CSV/Excel des données mensuelles (template fourni dans l'app)
- Export PDF détaillé + export CSV
- Écran de bienvenue avec explications d'usage
- Infobulles d'aide pour retrouver les bons montants sur la fiche de paie

## Utilisation locale
1. Installer les dépendances:

```bash
python -m pip install -r requirements.txt
```

2. Lancer l'application:

```bash
python -m streamlit run impots.py
```

3. Ouvrir l'URL locale affichée par Streamlit (généralement http://localhost:8501).

## Structure d'import attendue
Colonnes obligatoires:
- `mois` (1-12 ou nom du mois)
- `revenu_net` (net imposable mensuel)
- `impot_preleve` (prélèvement à la source mensuel)

Colonne optionnelle:
- `revenu_exceptionnel`

## Avertissement
Cet outil est indicatif. Pour un calcul officiel, utilisez le simulateur de l'administration fiscale sur impots.gouv.fr.
