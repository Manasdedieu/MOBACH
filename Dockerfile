FROM odoo:19

USER root

# Installation des dépendances Python requises par les modules tiers et la paie
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

USER odoo
