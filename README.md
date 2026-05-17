# 🚀 Déploiement Odoo 19 — MOBACH

> Instance Odoo 19 déployée avec Docker, PostgreSQL natif sur VPS, et modules personnalisés montés via volumes.

---

## 🏗️ Architecture

| Composant | Déploiement |
|---|---|
| **PostgreSQL** | Installé directement sur le VPS (hors Docker) |
| **Odoo 19** | Conteneur Docker |
| **Modules custom** | Montés via volumes Docker |
| **Sources Odoo** | Clonées depuis ce dépôt GitHub |

---

## 📋 Prérequis

- Ubuntu / Debian sur le VPS
- Accès root ou sudo
- Git installé

---

## 1. Installer Docker

```bash
sudo apt update
sudo apt install -y docker.io docker-compose git
```

Activer et vérifier Docker :

```bash
sudo systemctl enable docker
sudo systemctl start docker
docker --version
docker compose version
```

---

## 2. Installer et configurer PostgreSQL

### Installation

```bash
sudo apt install -y postgresql postgresql-contrib
```

### Créer l'utilisateur et la base de données

```bash
sudo -u postgres psql
```

```sql
CREATE USER odoo WITH PASSWORD 'odoo';
ALTER USER odoo CREATEDB;
CREATE DATABASE bd_mobach_odoo19 OWNER odoo;
\q
```

### Autoriser les connexions depuis Docker

Modifier `postgresql.conf` :

```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
```

```ini
listen_addresses = '*'
```

Modifier `pg_hba.conf` :

```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

Ajouter à la fin :

```ini
host    all             all             0.0.0.0/0               md5
```

Redémarrer PostgreSQL :

```bash
sudo systemctl restart postgresql
```

Vérifier que le port écoute :

```bash
sudo ss -lntp | grep 5432
```

---

## 3. Cloner les dépôts

### Créer le dossier de travail

```bash
mkdir -p ~/WORKSPACE/MOBACH_ENV
cd ~/WORKSPACE/MOBACH_ENV
```

### Cloner les sources Odoo 19

```bash
git clone --branch 19.0 https://github.com/odoo/odoo.git odoo
```

### Cloner les sources du depot mobach

```bash
git clone git@github.com:Manasdedieu/MOBACH.git
```

### créer le repertoir des modules personnalisés MOBACH si inexistant

```bash
mkdir -p MOBACH_ODOO_CUSTOM
```

### Structure attendue après clonage

```
~/WORKSPACE/MOBACH_ENV
├── MOBACH/
|   ├── MOBACH_ODOO_CUSTOM/
│   ├── docker-compose.yml
│   └── config/
│       └── odoo.conf
├── odoo/
├── mobach_odoo19_logs/
└── mobach_odoo19_filestore/
```

---

## 4. Créer les dossiers de données

```bash
mkdir -p ~/WORKSPACE/MOBACH_ENV/mobach_odoo19_logs
mkdir -p ~/WORKSPACE/MOBACH_ENV/mobach_odoo19_filestore
```

---

## 5. Créer le fichier `docker-compose.yml`

---

## 6. Créer le fichier `odoo.conf`

---

## 7. Démarrer l'instance

```bash
cd ~/WORKSPACE/MOBACH_ENV/MOBACH
docker compose up -d
```

Vérifier que le conteneur tourne :

```bash
docker ps
```

Suivre les logs :

```bash
docker logs -f odoo19-mobach
```

---

## 8. Accéder à Odoo

Ouvrir dans un navigateur :

```
http://IP_DU_SERVEUR:8019
```

---

## 9. Mise à jour des modules

### Récupérer les dernières modifications

```bash
cd ~/WORKSPACE/MOBACH_ENV/odoo
cd ~/WORKSPACE/MOBACH_ENV/MOBACH_ODOO_CUSTOM
```

### Redémarrer Odoo

```bash
cd ~/WORKSPACE/MOBACH_ENV/MOBACH
docker compose restart
```

### Mettre à jour un module spécifique

```bash
docker exec -it odoo19-mobach bash
odoo --config=/etc/odoo/odoo.conf -u nom_module -d bd_mobach_odoo19
```

---

## 🔧 Commandes utiles

| Action | Commande |
|---|---|
| Démarrer | `docker compose up -d` |
| Arrêter | `docker compose down` |
| Redémarrer | `docker compose restart` |
| Logs en direct | `docker logs -f odoo19-mobach` |
| Shell dans le conteneur | `docker exec -it odoo19-mobach bash` |

---

## 💾 Sauvegardes

### Base de données PostgreSQL

```bash
pg_dump -U odoo bd_mobach_odoo19 > backup_$(date +%Y%m%d).sql
```

### Filestore

```bash
tar -czf filestore_$(date +%Y%m%d).tar.gz ~/mobach_odoo19/mobach_odoo19_filestore/
```

### Configuration

```bash
cp ~/mobach_odoo19/docker/config/odoo.conf odoo.conf.bak
```

---

## 🔒 Recommandations production

- Désactiver la liste des bases : `list_db = False` dans `odoo.conf`
- Mettre en place un reverse proxy **Nginx** avec **HTTPS** (Certbot)
- Automatiser les sauvegardes PostgreSQL et du filestore
- Restreindre l'accès au port 5432 via le pare-feu

---

## 🛠️ Dépannage

### Le conteneur redémarre en boucle

```bash
docker logs -f odoo19-mobach
```

### Erreur de connexion PostgreSQL

```bash
psql -h localhost -U odoo -d bd_mobach_odoo19
```

---

## 📦 Stack technique

- **Odoo 19** — ERP
- **Docker** — Conteneurisation
- **PostgreSQL** — Base de données (natif VPS)
- **GitHub** — Gestion des sources et modules custom
