# Assistant AM TRANSIT — Contrôle de gestion

Chatbot web basé sur l'API Claude (Anthropic), qui exploite vos documents de
contrôle de gestion (grand livre, balances, budgets, factures — Excel, CSV,
PDF) pour répondre à vos questions.

## Fonctionnalités

- **Bibliothèque de documents persistante** : uploadez une fois vos fichiers
  (grand livre Sage 100, balances, budgets, factures PDF...), ils restent
  disponibles pour toutes vos conversations futures.
- **Plusieurs fichiers à la fois**, croisés dans une même conversation.
- **Calculs exacts** : l'assistant interroge vos données avec des requêtes
  pandas réelles (comme une vraie balance ou un vrai filtre), il n'invente
  jamais de chiffres.
- **Historique des conversations**, consultable et rechargeable à tout moment.
- **Export** de chaque conversation en Excel (.xlsx) ou PDF.

## 1. Obtenir une clé API Anthropic (gratuit à la création)

1. Allez sur **https://console.anthropic.com**
2. Créez un compte (ou connectez-vous)
3. Menu **API Keys** → **Create Key**
4. Copiez la clé (elle commence par `sk-ant-...`) — elle ne sera plus
   affichée en entier ensuite, conservez-la en lieu sûr
5. Ajoutez un moyen de paiement dans **Billing** pour activer l'utilisation
   (l'usage d'un assistant personnel reste généralement de quelques dollars
   par mois selon le volume de questions)

Vous collerez cette clé directement dans l'application (barre latérale,
section "🔑 Clé API Anthropic") — elle n'est jamais envoyée ailleurs qu'à
l'API Anthropic, et n'est pas stockée sur le serveur au-delà de votre session
sauf si vous l'ajoutez en variable d'environnement (voir plus bas).

## 2. Lancer en local (pour tester avant de déployer)

```bash
cd am-transit-assistant
python3 -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`.

## 3. Déployer en ligne (recommandé : Streamlit Community Cloud, gratuit)

1. Créez un dépôt GitHub (public ou privé) et poussez-y ce dossier :
   ```bash
   cd am-transit-assistant
   git init
   git add .
   git commit -m "Assistant AM TRANSIT"
   git branch -M main
   git remote add origin https://github.com/<votre-compte>/am-transit-assistant.git
   git push -u origin main
   ```
2. Allez sur **https://share.streamlit.io**, connectez votre compte GitHub
3. **New app** → sélectionnez le dépôt, la branche `main`, le fichier
   `app.py`
4. Dans **Advanced settings → Secrets**, ajoutez :
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-votre-cle"
   ```
   (ainsi vous n'aurez plus besoin de la ressaisir à chaque visite — sinon
   vous pouvez toujours la coller dans la barre latérale de l'app)
5. **Deploy** — vous obtenez une URL publique du type
   `https://am-transit-assistant.streamlit.app`, utilisable depuis
   n'importe quel navigateur (ordinateur ou téléphone).

**Important — persistance des documents et de l'historique sur Streamlit
Cloud** : le stockage du dossier `storage/` (documents + historique SQLite)
est réinitialisé si l'application redémarre après une longue inactivité,
comme tout hébergement gratuit sans base de données externe. Pour un usage
personnel avec des sessions rapprochées, cela ne pose généralement pas de
problème. Si vous voulez une persistance garantie à long terme, deux options
simples :
- héberger sur un service avec disque persistant (ex: Render.com, un plan
  payant à quelques dollars/mois, avec un "disk" monté sur `storage/`) ;
- ou faire tourner l'application en local / sur un serveur interne AM
  TRANSIT (option "En local" que vous pouvez toujours demander).

## 4. Utilisation

1. Dans la barre latérale, section **📁 Bibliothèque de documents**, uploadez
   vos fichiers (grand livre, balances, budgets, factures PDF...).
2. Posez vos questions dans la zone de chat, par exemple :
   - *"Quel est le solde du compte 401110 dans le grand livre ?"*
   - *"Compare le budget carburant et les dépenses réelles de janvier."*
   - *"Résume les points clés de l'audit CAC dans le PDF fourni."*
3. L'assistant appelle vos documents en coulisses (SUMIF/pandas réel) et vous
   répond avec les chiffres exacts.
4. Utilisez **➕ Nouvelle conversation** pour repartir sur un sujet différent
   sans mélanger le contexte, et retrouvez vos anciennes conversations dans
   la liste.
5. Exportez une conversation en Excel ou PDF via la barre latérale.

## Limites connues (MVP)

- Les fichiers PDF sont lus en extraction de texte simple (pas d'OCR sur des
  scans image) — un PDF scanné sans couche texte ne sera pas exploitable.
- Les très gros fichiers Excel (plusieurs centaines de milliers de lignes)
  peuvent ralentir les requêtes pandas selon la puissance du serveur choisi.
- Le modèle Claude utilisé par défaut est `claude-sonnet-4-5-20250929` ;
  vous pouvez changer l'identifiant du modèle dans la barre latérale si un
  modèle plus récent est disponible sur votre compte (voir
  https://docs.claude.com/en/docs/about-claude/models).

## Structure du projet

```
am-transit-assistant/
├── app.py              # Interface Streamlit + boucle de chat avec Claude
├── backend.py          # Logique métier (documents, requêtes, historique, export)
├── requirements.txt
├── .streamlit/config.toml
└── storage/             # Bibliothèque de documents + historique (créé automatiquement)
```
