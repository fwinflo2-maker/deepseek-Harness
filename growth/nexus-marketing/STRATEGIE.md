# Nexus — Stratégie de croissance pilotée par agents IA

**Site :** https://nexustechnologies.cloud/
**Produit :** Orchestration financière — comparaison en temps réel des routes de transfert d'argent international (taux, frais, vitesse) + exécution automatique. Zéro custody, ledger auditable.
**Objectif :** Faire connaître le site, automatiser l'acquisition + la relance avec des agents IA, générer des revenus (inscriptions → premier transfert → transferts récurrents).

---

## 1. Le concept créatif : "L'argent a une meilleure route. Nexus la trouve."

Le produit a déjà un narratif fort intégré : **Intent → Quote → Routing → Execution → Settlement**. On réutilise EXACTEMENT ce framework comme fil rouge de toute la communication, y compris marketing :

- **Intent** : "Vous ne devriez pas avoir à choisir entre Western Union, une banque ou une crypto. Dites juste ce que vous voulez faire."
- **Quote** : transparence radicale — on montre en permanence des comparatifs chiffrés (ex. "Envoyer 500€ vers Douala : Nexus vs Banque vs Wise vs Western Union").
- **Routing** : storytelling "coulisses" — comment le moteur choisit la meilleure route (contenu éducatif/tech qui rassure).
- **Execution** : preuve sociale, rapidité, témoignages.

**Positionnement différenciant à marteler** : *"Nexus n'est pas une banque, ni un service de transfert de plus. C'est le pilote automatique qui trouve la meilleure route pour votre argent."*

**Cible prioritaire (funnel à fort volume, cohérent avec "transfert international")** :
1. Diaspora africaine/francophone en Europe/USA envoyant de l'argent au pays (forte douleur : frais élevés, taux opaques, lenteur).
2. PME/freelances facturant à l'international (paiements récurrents, multi-devises).
3. Early adopters "fintech/crypto-curious" intéressés par l'automatisation IA elle-même (angle "product-led growth" via la nouveauté technique).

---

## 2. Les agents IA à mettre en place (par ordre de priorité)

### Agent 1 — Agent de contenu & acquisition (priorité choisie)
**Rôle :** génère chaque semaine du contenu prêt à publier (LinkedIn, X/Twitter, TikTok/Reels scripts, blog SEO) autour du concept Intent→Quote→Routing→Execution, sans intervention humaine autre que validation finale.

Ce que l'agent produit automatiquement :
- 3 posts LinkedIn/X par semaine (storytelling, comparatifs chiffrés, coulisses techniques).
- 1 article de blog SEO par semaine ciblant des requêtes comme "envoyer de l'argent à [pays] pas cher", "comparateur transfert d'argent international", "meilleur taux transfert Europe Afrique".
- 1 script de vidéo courte (Reels/TikTok/Shorts) par semaine.
- Un calendrier éditorial glissant sur 30 jours.

→ **Livré aujourd'hui** dans `agents/content_agent.py` (voir section 4, fonctionne dès maintenant, avec ou sans clé API IA).

### Agent 2 — Agent de relance email (nurturing + reconquête)
**Rôle :** surveille les leads (inscrits, visiteurs ayant laissé leur email, utilisateurs inactifs) et déclenche automatiquement la bonne séquence email.

Segments et séquences (voir `templates/emails/`) :
1. **`signup_no_transfer`** — s'est inscrit mais n'a jamais fait de premier transfert (3 emails sur 7 jours).
2. **`abandoned_quote`** — a demandé un devis (Quote) mais n'a pas exécuté (2 emails sur 48h, urgence sur le taux).
3. **`dormant_user`** — a fait un transfert il y a >30 jours, pas de récidive (2 emails sur 10 jours, réactivation + parrainage).
4. **`newsletter_lead`** — a laissé son email sans compte (nurture éducatif 4 emails sur 14 jours → pousse à l'inscription).

→ **Livré aujourd'hui** dans `agents/relance_agent.py` : moteur de règles + templates, branchable sur Brevo (gratuit jusqu'à 300 emails/jour) dès que vous avez des leads réels.

### Agent 3 — Agent chatbot de conversion (à activer ensuite)
**Rôle :** widget IA sur le site répondant aux questions ("combien ça coûte d'envoyer 200€ au Sénégal ?"), lève les objections (sécurité, "zéro custody"), pousse vers `/register`. Non codé aujourd'hui (nécessite accès au repo du site) — recommandation d'outil : Chatbase, Crisp+IA, ou un petit widget custom branché sur une API LLM.

### Agent 4 — Agent d'analyse & reporting
**Rôle :** agrège chaque semaine les métriques (visiteurs, inscriptions, taux de conversion signup→transfert, revenu) et génère un résumé + recommandations. À brancher plus tard sur Google Analytics/Plausible + votre base de données produit.

---

## 3. Canaux et calendrier (30 premiers jours)

| Semaine | Focus | Actions clés |
|---|---|---|
| 1 | Fondations | Configurer capture d'email sur le site (si absent), créer comptes LinkedIn/X dédiés "Nexus", brancher Brevo (ou équivalent gratuit), lancer l'agent de contenu. |
| 2 | Preuve de valeur | Publier 3 comparatifs chiffrés taux réels (Nexus vs Wise vs banque vs Western Union) sur 3 corridors différents (ex : France→Sénégal, USA→Cameroun, France→Côte d'Ivoire). Premier article de blog SEO. |
| 3 | Distribution communautaire | Poster dans groupes Facebook/WhatsApp/Telegram diaspora (avec consentement des règles du groupe), partenariats micro-influenceurs diaspora (nano-influenceurs, 5-20k abonnés, rémunération à la performance/parrainage). |
| 4 | Automatiser la relance | Activer les 4 séquences email sur les premiers leads collectés, mesurer taux d'ouverture/clic/conversion, itérer. |

**Budget minimal viable (V1) :** 0 à 50 €/mois — Brevo gratuit, comptes sociaux gratuits, contenu généré par agent IA. Budget publicitaire optionnel dès que la conversion organique est validée (Meta Ads ciblé diaspora, coût par lead à tester).

---

## 4. Mécanique de génération de revenus

```
Contenu IA (acquisition) → Landing (Quote comparatif) → Inscription → Devis (Quote) → Relance IA si pas d'exécution → Transfert (revenu) → Réactivation IA pour le prochain transfert (récurrence = LTV)
```

Le point de bascule vers le revenu se situe à 2 endroits, tous deux couverts par l'agent de relance :
1. **Inscription → premier transfert** (le plus gros point de fuite typique en fintech).
2. **Premier transfert → transferts récurrents** (LTV, via l'email `dormant_user` + parrainage).

---

## 5. KPIs à suivre dès la semaine 1

- Trafic organique (site + réseaux) — objectif indicatif : x2 en 30 jours.
- Taux de capture email sur le site (visiteur → lead).
- Taux inscription → 1er transfert (à faire remonter par l'agent de relance).
- Taux d'ouverture / clic des séquences email (benchmark fintech : ouverture ~25-35%, clic ~3-6%).
- Coût d'acquisition (si publicité activée) vs valeur d'un transfert.

---

## 6. Ce qui est livré concrètement aujourd'hui dans ce dossier

```
growth/nexus-marketing/
├── STRATEGIE.md                 ← ce document
├── README.md                    ← comment lancer les agents
├── requirements.txt
├── .env.example
├── agents/
│   ├── content_agent.py         ← agent 1 : génère contenu (marche sans clé API)
│   └── relance_agent.py         ← agent 2 : moteur de relance email par segment
├── templates/emails/*.txt       ← les 4 séquences email prêtes à l'emploi
├── data/leads_sample.csv        ← exemple de fichier leads à adapter
├── content/                     ← sorties générées par l'agent de contenu
└── emails_drafts/               ← sorties (dry-run) de l'agent de relance
```

**Prochaine étape recommandée :** brancher une vraie source de leads (export CSV du site ou webhook) et une clé Brevo, puis programmer les deux agents en tâche planifiée (cron / GitHub Actions) pour un fonctionnement 100% automatique.
