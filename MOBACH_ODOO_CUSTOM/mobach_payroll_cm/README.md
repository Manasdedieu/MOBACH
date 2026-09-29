# Module MOBACH - Paie & Fiscalité Cameroun (SYSCOHADA / CGI)

Ce module fournit l'ensemble des règles salariales, cotisations sociales (CNPS), retenues fiscales (IRPP, CAC, CFC, RAV, TDC) et charges patronales conformes à la législation en vigueur au Cameroun.

---

## 1. Organismes et Registres de Contributions (`hr.contribution.register`)
* **CNPS** : Caisse Nationale de Prévoyance Sociale (Pension Vieillesse PVI, Prestations Familiales PF, Accidents du Travail AT).
* **DGI** : Direction Générale des Impôts (IRPP, RAV / CRTV).
* **CTD / Communes** : Collectivités Territoriales Décentralisées (Taxe Communale TDC, Centimes Additionnels CAC).
* **CFC** : Crédit Foncier du Cameroun (Part salariale 1% et part patronale 1,5%).
* **FNE** : Fonds National de l'Emploi (Part patronale 1%).
* **Salariés** : Règlement des salaires nets.

---

## 2. Décomposition des Règles Salariales

### A. Gains (Rémunération Brute)
| Code | Nom de la Règle | Catégorie | Mode de Calcul |
| :--- | :--- | :--- | :--- |
| `BASIC` | Salaire de Base | `BASIC` | `contract.wage` |
| `SUR_SAL` | Sursalaire | `ALW` | Entrée variable `SURSAL` |
| `ANC` | Prime d'Ancienneté | `ALW` | 4% après 2 ans + 1% par an supplémentaire |
| `PRIME` | Primes diverses imposables | `ALW` | Entrée variable `PRIME` |
| `IND_TRANS` | Indemnité Transport exonérée | `NON_IMP` | Entrée variable `IND_TRANS` |
| `GROSS` | Salaire Brut Imposable | `GROSS` | `BASIC + ALW` |

---

### B. Retenues Salariales (Cotisations & Impôts)
| Code | Nom de la Règle | Assiette / Base | Taux ou Barème | Organisme |
| :--- | :--- | :--- | :--- | :--- |
| `CNPS_PVI_SAL` | CNPS Pension Vieillesse | `GROSS` (plafonné à 750 000 FCFA) | 4,2 % (max 31 500 FCFA) | CNPS |
| `CFC_SAL` | Crédit Foncier Salarial | `GROSS` | 1,0 % | CFC |
| `RAV` | Redevance Audio-Visuelle | `GROSS` | Barème mensuel officiel (0 à 13 000 FCFA) | DGI (CRTV) |
| `TDC` | Taxe Communale | `contract.wage` | Barème mensuel (0 à 3 000 FCFA) | Commune |
| `BASE_IRPP` | Base Nette Imposable IRPP | `(GROSS - CNPS) * 70% - 41 667` | Règle intermédiaire de calcul | - |
| `IRPP` | Impôt sur le Revenu | `BASE_IRPP` | Barème progressif mensuel (10%, 15%, 25%, 35%) | DGI |
| `CAC` | Centimes Additionnels | `abs(IRPP)` | 10 % de l'IRPP | Commune |
| `AVANCE` | Avance sur Salaire / Acompte | Montant saisi | Entrée variable `AVANCE` | - |
| `NET` | **Net à Payer** | `GROSS + NON_IMP - RETENUES` | Net viré sur compte bancaire | Salarié |

---

### C. Charges Patronales (Coût Employeur)
| Code | Nom de la Règle | Assiette / Base | Taux |
| :--- | :--- | :--- | :--- |
| `CNPS_PVI_PAT` | CNPS PVI Patronale | `GROSS` (plafonné à 750 000 FCFA) | 4,2 % |
| `CNPS_PF_PAT` | Prestations Familiales | `GROSS` (plafonné à 750 000 FCFA) | 7,0 % |
| `CNPS_AT_PAT` | Accidents du Travail | `GROSS` (plafonné à 750 000 FCFA) | 2,5 % (taux moyen) |
| `CFC_PAT` | Crédit Foncier Patronal | `GROSS` (non plafonné) | 1,5 % |
| `FNE_PAT` | Fonds National Emploi | `GROSS` (non plafonné) | 1,0 % |

---

## 3. Données de Test Incluses

1. **Paul TCHAMBA** (Technicien) :
   - Salaire de base : `250 000 FCFA`
   - Permet de valider :
     - CNPS 4.2% : `10 500 FCFA`
     - CFC 1% : `2 500 FCFA`
     - RAV : `3 250 FCFA` (tranche 200k-300k)
     - TDC : `2 000 FCFA` (tranche 200k-300k)
     - IRPP : `12 598 FCFA`
     - CAC : `1 260 FCFA`
     - **Net à payer : `217 892 FCFA`**

2. **Aminatou BOUBA** (Cadre Financier) :
   - Salaire de base : `850 000 FCFA` (avec > 3 ans d'ancienneté)
   - Permet de valider le **plafonnement légal de la CNPS à 750 000 FCFA** (`31 500 FCFA` max) et les tranches supérieures de l'IRPP.
