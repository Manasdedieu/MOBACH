"""Génère data/template/account.account-syscohada.csv à partir du plan comptable du client (xlsx).

Usage : python3 generate_account_csv.py <l10n_syscohada>/data/template/account.account-syscohada.csv \
            "PLAN COMPTABLE.xlsx" ../data/template/account.account-syscohada.csv

Colonnes lues dans la première feuille : BASE (code à 4 chiffres), libellé (3e colonne).
- compte présent dans l10n_syscohada : libellé français remplacé par celui du client s'il diffère ;
- compte à 3 chiffres de l10n_syscohada sans sous-compte (111 pour 1111) : même compte, code et libellé du client ;
- sinon : nouveau compte, type et lettrage repris du compte de base le plus proche.
"""
import csv
import sys

import openpyxl

base_path, xlsx_path, out_path = sys.argv[1:4]
base = {r['code']: r for r in csv.DictReader(open(base_path))}
ws = openpyxl.load_workbook(xlsx_path, data_only=True).worksheets[0]
rows = [r for r in list(ws.iter_rows(values_only=True))[1:] if any(r)]

# Corrections du fichier client : doublons et coquilles.
LABEL_FIXES = {
    '1291': 'Perte nette à reporter',  # listé deux fois (« Report à nouveau débiteur » = 129)
    '6161': 'Transports de plis : expédition colis',
}

# Comptes de banque (pas de compte 521 dans l10n_syscohada : Odoo les crée par journal).
ACCOUNT_TYPE_FIXES = {
    '5211': 'asset_cash',
    '5215': 'asset_cash',
}


def nearest(code):
    for n in (3, 2, 1):
        cands = sorted(c for c in base if c.startswith(code[:n]) and len(c) >= n)
        if cands:
            return base[cands[0]]

out, seen = [], set()
for r in rows:
    code = str(r[0]).replace('\xa0', '').strip()
    if code in seen:
        continue
    seen.add(code)
    label = LABEL_FIXES.get(code, str(r[2]).strip())
    parent = code[:3]
    if code in base:
        if label != base[code]['name@fr']:
            out.append({'id': base[code]['id'], 'name@fr': label})
    elif parent in base and not any(c != parent and c.startswith(parent) for c in base):
        # Compte de base à 3 chiffres sans sous-compte (111) : c'est le même compte (1111),
        # on reprend le code et le libellé du client.
        out.append({'id': base[parent]['id'], 'code': code, 'name@fr': label})
        print('REMAP', parent, '->', code, label)
    else:
        ref = nearest(code)
        out.append({'id': f'pcg_{code}', 'name': label, 'code': code,
                    'account_type': ACCOUNT_TYPE_FIXES.get(code, ref['account_type']), 'reconcile': ref['reconcile'],
                    'non_trade': ref['non_trade'], 'name@fr': label, '_ref': ref['code']})
for o in out:
    if '_ref' in o:
        print('NEW', o['code'], o['account_type'], o['reconcile'], 'ref', o['_ref'], o['name'])
print('updates', sum('_ref' not in o for o in out), 'new', sum('_ref' in o for o in out))
fields = ['id', 'name', 'code', 'account_type', 'reconcile', 'non_trade', 'name@fr']
with open(out_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL, extrasaction='ignore')
    w.writeheader()
    w.writerows(out)
