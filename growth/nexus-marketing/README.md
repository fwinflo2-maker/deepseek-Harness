# Nexus Growth — Agents IA marketing

Boîte à outils autonome pour faire connaître **https://nexustechnologies.cloud/** et
automatiser l'acquisition + la relance email. Voir [`STRATEGIE.md`](./STRATEGIE.md)
pour le plan complet.

⚠️ Ce dossier est indépendant du reste du dépôt (qui est un framework d'agent de
codage) — il ne touche à aucun code du site Nexus lui-même.

## Installation

```bash
cd growth/nexus-marketing
pip install -r requirements.txt   # (ou: pip install --break-system-packages -r requirements.txt)
cp .env.example .env               # puis renseigner les clés si vous en avez
```

Aucune clé API n'est obligatoire pour commencer : les deux agents fonctionnent
en mode local / dry-run par défaut.

## Agent 1 — Contenu & acquisition

Génère un pack hebdomadaire complet : 3 posts LinkedIn (angles différents),
3 tweets, 1 plan d'article de blog SEO, 1 script vidéo courte, et un
calendrier de publication jour par jour.

```bash
python agents/content_agent.py                       # semaine courante
python agents/content_agent.py --weeks 4              # calendrier sur 4 semaines
python agents/content_agent.py --corridor "France,Sénégal"   # forcer un corridor
```

Sorties dans `content/pack_<date-du-lundi>.md`.

- **Sans `OPENAI_API_KEY`** : contenu généré à partir de modèles éditoriaux
  structurés (fonctionne hors-ligne, résultat directement publiable).
- **Avec `OPENAI_API_KEY`** (dans `.env`) : chaque post est rédigé par un LLM
  pour plus de variété et de fraîcheur.

À automatiser ensuite : brancher une tâche planifiée (cron, GitHub Actions...)
qui exécute ce script chaque lundi et vous envoie le pack généré (Slack,
email, etc.) pour validation avant publication.

## Agent 2 — Relance email

Lit un CSV de leads/utilisateurs déjà segmentés, choisit automatiquement le
bon email de la bonne séquence selon l'ancienneté de l'événement déclencheur,
et l'envoie (ou le prépare en brouillon).

Segments supportés : `signup_no_transfer`, `abandoned_quote`, `dormant_user`,
`newsletter_lead` (détail des séquences dans `templates/emails/`).

```bash
python agents/relance_agent.py --leads data/leads_sample.csv           # dry-run (écrit dans emails_drafts/)
python agents/relance_agent.py --leads data/leads_sample.csv --send    # envoi réel via Brevo si BREVO_API_KEY est défini
```

Format CSV attendu (voir `data/leads_sample.csv`) :

```
email,first_name,segment,signup_date,last_quote_date,last_transfer_date,amount,destination
```

- **Sans `BREVO_API_KEY`** : chaque email est écrit dans `emails_drafts/`
  pour relecture — aucun envoi réel n'a lieu.
- **Avec `BREVO_API_KEY`** (compte Brevo gratuit, jusqu'à 300 emails/jour) et
  `--send` : envoi réel via l'API transactionnelle Brevo.

À automatiser ensuite : brancher ce script sur un export quotidien (ou un
webhook) de votre base utilisateurs réelle, et le planifier en tâche cron
quotidienne.

## Prochaines étapes suggérées

1. Mettre en place la capture d'email sur le site (si pas déjà fait) pour
   alimenter le segment `newsletter_lead`.
2. Créer un compte Brevo gratuit et renseigner `BREVO_API_KEY` + `SENDER_EMAIL`
   (avec un domaine vérifié) dans `.env`.
3. Exporter réellement vos utilisateurs/leads vers un CSV au format attendu
   (ou écrire un petit connecteur vers votre base de données produit).
4. Planifier `content_agent.py` (hebdo) et `relance_agent.py` (quotidien) en
   cron ou GitHub Actions.
5. Une fois validé, envisager l'agent 3 (chatbot IA de conversion sur le
   site) et l'agent 4 (reporting automatique) décrits dans `STRATEGIE.md`.
