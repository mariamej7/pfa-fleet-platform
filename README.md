
# Fleet Analytics — Plateforme Data

## Présentation

Projet de fin d'année (PFA) réalisé dans le cadre d'un stage chez Oritech.

**Sujet :** Conception d'une plateforme Data pour l'analyse des performances de la flotte et la détection d'anomalies liées au carburant.

L'objectif est de transformer des données télématiques de véhicules en indicateurs, de détecter des événements atypiques liés au carburant et de faciliter leur investigation.

## Fonctionnalités

- Importation et vérification de fichiers de données.
- Préparation et analyse des données de flotte.
- Visualisation des indicateurs de performance.
- Analyse des niveaux de carburant et des ravitaillements potentiels.
- Détection d'événements suspects par règles métier.
- Détection de candidats atypiques avec Isolation Forest.
- Consultation et suivi des alertes.
- Analyse de la qualité et de la couverture des données.

## Technologies

- **Frontend :** Next.js, React, TypeScript.
- **Backend :** Python, FastAPI.
- **Base de données :** PostgreSQL.
- **Analyse des données :** Python et pipeline de traitement.
- **Détection d'anomalies :** règles métier et Isolation Forest.

## Organisation du projet

- `frontend/` : interface web.
- `backend/` : API et accès à la base de données.
- `pipeline/` : préparation des données et analyses.
- `database/` : schémas SQL.
- `docs/` : documentation du projet.



## Confidentialité

Les données réelles de flotte, les fichiers de configuration contenant des secrets et les identifiants de connexion ne sont pas destinés à être publiés dans ce dépôt.

Ce projet est destiné à être partagé uniquement dans le respect des autorisations de l'entreprise.
