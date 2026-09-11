#!/usr/bin/env python3
"""
Agent de contenu — Nexus Growth

Génère automatiquement, chaque semaine, un pack de contenu marketing pour
faire connaître https://nexustechnologies.cloud/ autour du concept produit :
Intent -> Quote -> Routing -> Execution -> Settlement.

Fonctionne en deux modes :
  1. Mode "IA" : si OPENAI_API_KEY est présent dans l'environnement (.env),
     utilise un LLM pour rédiger un contenu original à chaque exécution.
  2. Mode "local" (par défaut, sans clé) : génère un pack de contenu complet
     à partir de modèles éditoriaux structurés (aucune dépendance externe,
     fonctionne hors-ligne).

Usage :
    python agents/content_agent.py                # pack de la semaine courante
    python agents/content_agent.py --weeks 4       # calendrier sur 4 semaines
    python agents/content_agent.py --corridor "France,Sénégal"

Sortie : fichiers Markdown dans ../content/
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"

SITE_URL = os.environ.get("SITE_URL", "https://nexustechnologies.cloud")

# Corridors de transfert d'argent pertinents pour la cible diaspora francophone.
DEFAULT_CORRIDORS = [
    ("France", "Sénégal"),
    ("France", "Côte d'Ivoire"),
    ("France", "Cameroun"),
    ("Belgique", "RD Congo"),
    ("Canada", "Congo-Brazzaville"),
    ("USA", "Nigéria"),
]

PAIN_POINTS = [
    "des frais cachés qui grignotent jusqu'à 8% du montant envoyé",
    "un taux de change annoncé... différent du taux réellement appliqué",
    "un délai de réception de 3 à 5 jours pour un virement classique",
    "l'obligation de choisir à l'aveugle entre banque, Western Union ou une app crypto",
    "aucune transparence sur qui détient l'argent pendant le transfert",
]

PROOF_POINTS = [
    "Nexus compare les routes en temps réel avant chaque envoi",
    "Nexus ne détient jamais vos fonds : zéro custody, transparence totale",
    "chaque mouvement est une écriture traçable dans un ledger double-entrée",
    "vous voyez le montant reçu, les frais et le délai avant de confirmer",
    "le moteur choisit automatiquement la route la plus rapide et la moins chère",
]


def _try_llm_generate(prompt: str) -> str | None:
    """Tente une génération via OpenAI si une clé API est configurée. Retourne None sinon."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        import requests
    except ImportError:
        return None

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Tu es le copywriter growth de Nexus, une plateforme "
                            "d'orchestration financière (transfert d'argent international). "
                            "Ton ton est direct, confiant, orienté preuve chiffrée, jamais "
                            "condescendant. Tu écris en français."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.8,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # réseau, quota, etc. -> fallback silencieux
        print(f"[content_agent] LLM indisponible ({exc}), bascule en mode local.", file=sys.stderr)
        return None


LINKEDIN_ANGLES = [
    "probleme_solution",
    "comparatif_chiffre",
    "coulisses_produit",
]


def gen_linkedin_post(corridor: tuple[str, str], pain: str, proof: str, angle: str = "probleme_solution") -> str:
    origin, dest = corridor
    prompt = (
        f"Écris un post LinkedIn (120-180 mots, pas de hashtags génériques, 1 CTA vers {SITE_URL}), "
        f"angle '{angle}', qui parle d'envoyer de l'argent de {origin} vers {dest}, en dénonçant ce problème : "
        f"'{pain}', et en amenant Nexus comme solution car '{proof}'. Termine par une question ouverte."
    )
    llm = _try_llm_generate(prompt)
    if llm:
        return llm

    if angle == "comparatif_chiffre":
        return f"""On a fait le calcul pour un envoi {origin} → {dest}.

Sur un transfert classique, {pain}. Sur le papier ça paraît anodin. En pratique, sur plusieurs
envois dans l'année, ça représente souvent l'équivalent d'un mois de courses en moins pour la
famille qui reçoit l'argent.

Chez Nexus, {proof}. Concrètement : vous indiquez votre intention (montant, {dest}), on affiche
un devis unique et clair — montant reçu, frais, délai — avant que vous confirmiez quoi que ce soit.

Pas de calcul à faire de votre côté. Pas de mauvaise surprise à l'arrivée.

👉 Comparez votre prochain envoi {origin}-{dest} sur {SITE_URL}

Et vous, avez-vous déjà comparé ce que vous recevez réellement d'un envoi à l'autre ?"""

    if angle == "coulisses_produit":
        return f"""Ce qui se passe réellement quand vous envoyez de l'argent {origin} → {dest} avec Nexus :

1. Vous déclarez votre intention — montant, destination, éventuelle contrainte de délai.
2. Nexus compare en temps réel les routes disponibles (banques, réseaux spécialisés, rails crypto).
3. Le moteur sélectionne la route optimale et vous montre le résultat : montant reçu, frais, délai.
4. Vous confirmez. Nexus orchestre l'exécution — {proof}.

Pas de compte à jongler entre plusieurs apps pour comparer à la main. Pas de fonds détenus par
Nexus à aucun moment : zéro custody, un ledger traçable pour chaque mouvement.

Le vrai problème que ça résout : {pain}, sans que vous ayez à devenir expert en transferts
internationaux pour vous en rendre compte.

👉 Voir la route optimale pour votre prochain envoi : {SITE_URL}

Qu'est-ce qui vous ferait le plus hésiter à essayer un nouveau service de transfert ?"""

    # angle par défaut : probleme_solution
    return f"""📍 {origin} → {dest} : combien vous coûte vraiment votre transfert ?

La plupart des gens qui envoient de l'argent de {origin} vers {dest} subissent {pain}.

Le problème n'est pas le manque d'options — Western Union, banques, apps crypto, il y en a partout.
Le problème, c'est qu'aucune de ces options ne vous dit *avant* d'envoyer laquelle est la meilleure pour VOTRE transfert, à CET instant.

Chez Nexus, {proof}. Vous déclarez votre intention (montant, corridor), on compare les routes disponibles en temps réel, et on exécute la meilleure. Vous confirmez, c'est tout.

Pas de compte à jongler entre 3 apps. Pas de calculatrice mentale pour deviner le "vrai" taux.

👉 Testez votre prochain envoi {origin}-{dest} sur {SITE_URL}

Question pour vous : la dernière fois que vous avez envoyé de l'argent à l'international, avez-vous comparé les taux avant, ou fait confiance à l'habitude ?"""


def gen_tweet(corridor: tuple[str, str], proof: str) -> str:
    origin, dest = corridor
    prompt = (
        f"Écris un tweet (max 260 caractères) percutant sur le transfert d'argent {origin}->{dest}, "
        f"mettant en avant que {proof}. CTA vers {SITE_URL}."
    )
    llm = _try_llm_generate(prompt)
    if llm:
        return llm[:280]

    return (
        f"Envoyer de l'argent {origin} → {dest} ne devrait pas être une loterie sur le taux.\n\n"
        f"Nexus compare les routes en temps réel et exécute la meilleure automatiquement.\n"
        f"{proof.capitalize()}.\n\n"
        f"👉 {SITE_URL}"
    )


def gen_blog_outline(corridor: tuple[str, str]) -> str:
    origin, dest = corridor
    prompt = (
        f"Écris le plan détaillé (H2/H3) + intro (150 mots) d'un article de blog SEO ciblant "
        f"la requête 'envoyer de l'argent {origin} {dest} pas cher', qui compare les méthodes "
        f"classiques et positionne Nexus ({SITE_URL}) comme solution."
    )
    llm = _try_llm_generate(prompt)
    if llm:
        return llm

    return f"""# Envoyer de l'argent de {origin} vers {dest} : le comparatif complet ({dt.date.today().year})

**Requête cible :** "envoyer de l'argent {origin} {dest} pas cher" / "meilleur taux transfert {origin} {dest}"

## Introduction (~150 mots)
Chaque année, des milliards d'euros/dollars transitent de {origin} vers {dest} via des virements
familiaux ou professionnels. Pourtant, la majorité des expéditeurs paient plus cher que
nécessaire — souvent sans le savoir — à cause d'un taux de change majoré ou de frais cachés.
Dans cet article, on compare objectivement les options disponibles pour envoyer de l'argent
de {origin} vers {dest}, et on montre comment une plateforme d'orchestration comme Nexus
permet de systématiquement choisir la route la moins chère et la plus rapide, sans effort.

## Plan de l'article
### 1. Les options classiques pour envoyer de l'argent {origin} → {dest}
- Virement bancaire international (SWIFT)
- Services spécialisés (Western Union, MoneyGram, Ria)
- Apps fintech (Wise, Remitly)
- Crypto / stablecoins

### 2. Ce qui plombe réellement le montant reçu
- Le taux de change appliqué vs le taux "mid-market"
- Les frais fixes et frais cachés
- Le délai de réception (coût d'opportunité)

### 3. Comparatif chiffré : envoyer 100€ / 500€ / 1000€ de {origin} vers {dest}
(Tableau à remplir avec des taux réels au moment de la publication — donnée qui devient
elle-même un aimant à partage et à backlinks.)

### 4. Pourquoi une orchestration automatique change la donne
- Le principe Intent → Quote → Routing → Execution de Nexus
- Zéro custody : la sécurité sans complexité
- Un seul devis clair au lieu de devoir comparer 4 apps à la main

### 5. Comment envoyer votre premier transfert {origin} → {dest} avec Nexus
- Étapes concrètes + capture d'écran
- CTA : {SITE_URL}/register

## Méta-description suggérée
"Comparatif 2026 : le meilleur moyen d'envoyer de l'argent de {origin} vers {dest}. Taux, frais,
délais — et comment Nexus trouve automatiquement la route la moins chère."
"""


def gen_video_script(corridor: tuple[str, str], pain: str) -> str:
    origin, dest = corridor
    return f"""[Script vidéo courte — 30-45 sec — Reels / TikTok / Shorts]

HOOK (0-3s) :
"Si tu envoies de l'argent de {origin} vers {dest}, tu perds probablement de l'argent sans le savoir."

PROBLÈME (3-15s) :
Montrer à l'écran une comparaison rapide : montant envoyé vs montant reçu selon 2-3 services,
en insistant sur {pain}.

SOLUTION (15-30s) :
"Nexus compare toutes les routes en temps réel — taux, frais, vitesse — et choisit la meilleure
pour toi. Tu dis juste ce que tu veux faire, Nexus s'occupe du reste."
(Montrer l'écran Intent -> Quote -> Routing -> Execution du produit.)

CTA (30-45s) :
"Teste ton prochain envoi {origin}-{dest} sur nexustechnologies.cloud, lien en bio."
"""


def build_weekly_pack(week_offset: int, corridors: list[tuple[str, str]]) -> str:
    corridor = corridors[week_offset % len(corridors)]
    pain = random.choice(PAIN_POINTS)
    proof = random.choice(PROOF_POINTS)
    monday = dt.date.today() + dt.timedelta(weeks=week_offset)
    monday -= dt.timedelta(days=monday.weekday())

    linkedin_posts = [
        gen_linkedin_post(corridor, random.choice(PAIN_POINTS), random.choice(PROOF_POINTS), angle)
        for angle in LINKEDIN_ANGLES
    ]
    tweets = [gen_tweet(corridor, random.choice(PROOF_POINTS)) for _ in range(3)]
    blog = gen_blog_outline(corridor)
    video = gen_video_script(corridor, pain)

    parts = [
        f"# Pack de contenu Nexus — semaine du {monday.isoformat()}",
        f"\nCorridor mis en avant cette semaine : **{corridor[0]} → {corridor[1]}**\n",
        "## 📅 Calendrier de publication suggéré",
        "| Jour | Canal | Contenu |",
        "|---|---|---|",
        "| Lundi | LinkedIn | Post 1 (storytelling problème/solution) |",
        "| Mardi | X/Twitter | Tweet 1 |",
        "| Mercredi | Blog | Publication article SEO |",
        "| Jeudi | LinkedIn | Post 2 (comparatif chiffré) |",
        "| Vendredi | TikTok/Reels | Vidéo courte |",
        "| Samedi | X/Twitter | Tweet 2 |",
        "| Dimanche | X/Twitter | Tweet 3 |",
        "\n---\n## ✍️ LinkedIn — Post 1\n" + linkedin_posts[0],
        "\n---\n## ✍️ LinkedIn — Post 2\n" + linkedin_posts[1],
        "\n---\n## ✍️ LinkedIn — Post 3 (réserve)\n" + linkedin_posts[2],
        "\n---\n## 🐦 Tweets\n1. " + tweets[0] + "\n\n2. " + tweets[1] + "\n\n3. " + tweets[2],
        "\n---\n## 📝 Article de blog SEO\n" + blog,
        "\n---\n## 🎬 Script vidéo courte\n" + video,
    ]
    return "\n".join(parts)


def parse_corridors(arg: str | None) -> list[tuple[str, str]]:
    if not arg:
        return DEFAULT_CORRIDORS
    pieces = [p.strip() for p in arg.split(",")]
    if len(pieces) != 2:
        raise SystemExit("--corridor attend le format 'Origine,Destination'")
    return [(pieces[0], pieces[1])]


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent de contenu Nexus Growth")
    parser.add_argument("--weeks", type=int, default=1, help="Nombre de semaines de contenu à générer")
    parser.add_argument("--corridor", type=str, default=None, help="Forcer un corridor 'Origine,Destination'")
    args = parser.parse_args()

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    corridors = parse_corridors(args.corridor)

    for week in range(args.weeks):
        pack = build_weekly_pack(week, corridors)
        monday = dt.date.today() + dt.timedelta(weeks=week)
        monday -= dt.timedelta(days=monday.weekday())
        out_path = CONTENT_DIR / f"pack_{monday.isoformat()}.md"
        out_path.write_text(pack, encoding="utf-8")
        print(f"[content_agent] Généré : {out_path}")


if __name__ == "__main__":
    main()
