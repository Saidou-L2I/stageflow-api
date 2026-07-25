# StageFlow — API de gestion sécurisée des stages data

API interne développée avec **FastAPI**, **SQLAlchemy 2.0 (async)**, **Alembic** et
**PostgreSQL**, permettant à un Master DSIA de gérer les offres de stage, les
candidatures des étudiants, les validations pédagogiques et les avis des
encadrants — chaque rôle ne voyant et ne modifiant que ce qu'il doit.

## Sommaire

- [Architecture](#architecture)
- [Rôles et habilitations](#rôles-et-habilitations)
- [Installation](#installation)
- [Variables d'environnement](#variables-denvironnement)
- [Lancement local](#lancement-local)
- [Lancement avec Docker](#lancement-avec-docker)
- [Migrations Alembic](#migrations-alembic)
- [Lancement des tests](#lancement-des-tests)
- [Documentation OpenAPI](#documentation-openapi)
- [Endpoints principaux](#endpoints-principaux)

## Architecture

```
app/
  main.py                  # Point d'entree FastAPI (middlewares, routes, handlers)
  api/routes/
    auth.py                # POST /auth/register, POST /auth/login
    users.py                # GET /users/me, gestion admin des roles
    offers.py                # Cycle de vie des offres + statistiques
    applications.py          # Cycle de vie des candidatures
  core/
    config.py                # Settings (pydantic-settings)
    security.py               # JWT (OAuth2 password flow), get_current_user
    permissions.py             # RBAC centralise (require_student, require_company, ...)
    errors.py                   # Exceptions metier -> 400/401/403/404
  db/
    session.py                # Engine + dependance get_db
    base.py                     # Base declarative SQLAlchemy
  models/                      # user.py, role.py, stage.py (Offer, Application)
  schemas/                      # DTO entree/sortie Pydantic v2
  repositories/                  # Pattern Repository (aucun SQL dans les routes)
  middlewares/                    # request_id.py, security_headers.py
  utils/                           # pagination.py, hashing.py, time.py
tests/
  unit/                             # hashing, JWT, invariants metier
  integration/                       # auth, offres, candidatures (via httpx + SQLite)
alembic/                              # migrations reproductibles
.github/workflows/ci.yml               # tests + couverture Codecov + build Docker
Dockerfile                              # image de production non-root
docker-compose.yml                       # environnement de developpement (API + Postgres)
```

## Rôles et habilitations

| Rôle | Habilitations |
|---|---|
| `student` | consulter les offres publiées, candidater, retirer une candidature tant qu'elle n'est pas acceptée |
| `company` | créer/compléter une offre en brouillon, la soumettre, consulter les candidatures de ses propres offres |
| `program_manager` | publier/refuser une offre soumise, accepter/refuser une candidature, consulter les statistiques |
| `admin` | gérer les comptes utilisateurs et forcer le changement de rôle |

Toute la logique d'autorisation est centralisée dans `app/core/permissions.py` via des
dépendances FastAPI (`require_student`, `require_company`, `require_program_manager`,
`require_admin`, `require_staff`) — aucune route ne contient de logique RBAC dispersée.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env 
```
Apres remplir le vrai fichier `.env` avec les variables d'environnement nécessaires, vous pouvez

> `aiosqlite` a été ajouté à `requirements.txt` par rapport à la liste fournie
> initialement : il est indispensable pour exécuter les tests d'intégration sur
> SQLite en mode asynchrone, comme autorisé par la consigne ("SQLite autorisé
> uniquement pour certains tests"). PostgreSQL reste la base de données de
> référence en développement et en production.

## Variables d'environnement

Voir `.env.example` :

| Variable | Description | Défaut |
|---|---|---|
| `DATABASE_URL` | URL de connexion SQLAlchemy async | `postgresql+asyncpg://...` |
| `SECRET_KEY` | Clé de signature des JWT | à changer en production |
| `ALGORITHM` | Algorithme JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée de validité du token | `60` |
| `DEFAULT_PAGE_SIZE` / `MAX_PAGE_SIZE` | Pagination des listes | `20` / `100` |

## Lancement local

```bash
# Démarrer une base PostgreSQL locale (ou utiliser docker-compose, voir plus bas)
alembic upgrade head
fastapi dev app/main.py
```

L'API est disponible sur `http://localhost:8000`, la documentation interactive sur
`http://localhost:8000/docs`.

## Lancement avec Docker

```bash
docker compose up --build
```

Ceci démarre PostgreSQL et l'API (`http://localhost:8000`). L'image de production
(`Dockerfile`) tourne avec un utilisateur non-root et expose `/health` pour le
`HEALTHCHECK` Docker.

## Migrations Alembic

```bash
# Générer une nouvelle migration après modification des modèles
alembic revision --autogenerate -m "description du changement"

# Appliquer les migrations
alembic upgrade head
```

## Lancement des tests

```bash
pytest --cov=app --cov-report=term-missing
```

Les tests tournent sur une base **SQLite en mémoire** (autorisé par la consigne pour
les tests), avec des fixtures dédiées par rôle (`student_user`, `company_user`,
`other_company_user`, `manager_user`, `admin_user`). Ils couvrent :

- l'authentification (register/login, tokens invalides/expirés) ;
- les permissions par rôle (403 sur les routes non autorisées) ;
- les invariants métier (offre incomplète, transitions de statut invalides,
  candidature active unique, candidature acceptée non retirable) ;
- **le test d'isolation explicitement demandé** : une entreprise ne peut pas
  consulter les candidatures d'une offre qui ne lui appartient pas
  (`test_company_cannot_see_applications_of_another_company`).

## Documentation OpenAPI

La documentation est générée automatiquement par FastAPI (tags, descriptions,
modèles de réponse) et disponible sur `/docs` (Swagger) et `/redoc`.

## Endpoints principaux

| Méthode | Route | Rôle requis |
|---|---|---|
| POST | `/auth/register` | public |
| POST | `/auth/login` | public |
| GET | `/users/me` | authentifié |
| PATCH | `/users/{id}/role` | admin |
| POST | `/offers` | company |
| PATCH | `/offers/{id}` | company (propriétaire, brouillon) |
| PATCH | `/offers/{id}/submit` | company (propriétaire) |
| PATCH | `/offers/{id}/review` | program_manager |
| GET | `/offers/stats` | program_manager / admin |
| GET | `/offers/{id}/applications` | company (propriétaire) / staff |
| POST | `/offers/{id}/applications` | student |
| GET | `/applications/me` | student |
| PATCH | `/applications/{id}/decision` | program_manager |
| DELETE | `/applications/{id}` | student (propriétaire) |
| GET | `/health` | public |

##Resultats des tests pytest --cov=app --cov-report=term-missing

```
==================================================================== tests coverage =====================================================================
____________________________________________________ coverage: platform win32, python 3.14.2-final-0 ____________________________________________________

Name                                   Stmts   Miss  Cover   Missing
--------------------------------------------------------------------
app\__init__.py                            0      0   100%
app\api\__init__.py                        0      0   100%
app\api\routes\__init__.py                 0      0   100%
app\api\routes\applications.py            52      5    90%   63-64, 81, 83, 113
app\api\routes\auth.py                    32      1    97%   59
app\api\routes\offers.py                  93      7    92%   119, 125, 147, 169, 206, 215-216
app\api\routes\users.py                   33     12    64%   36-40, 54-68
app\core\__init__.py                       0      0   100%
app\core\config.py                        18      0   100%
app\core\errors.py                        19      0   100%
app\core\permissions.py                   16      0   100%
app\core\security.py                      38      4    89%   36, 52-53, 58
app\db\__init__.py                         0      0   100%
app\db\base.py                             3      0   100%
app\db\session.py                         16      8    50%   15, 34-40
app\main.py                               25      2    92%   41, 46
app\middlewares\__init__.py                0      0   100%
app\middlewares\request_id.py             14      0   100%
app\middlewares\security_headers.py       10      0   100%
app\models\__init__.py                     0      0   100%
app\models\role.py                         6      0   100%
app\models\stage.py                       45      0   100%
app\models\user.py                        21      0   100%
app\repositories\__init__.py               0      0   100%
app\repositories\base.py                  29      3    90%   35, 43-44
app\repositories\stage_repository.py      31      4    87%   59-66, 69-76
app\repositories\user_repository.py       16      0   100%
app\schemas\__init__.py                    0      0   100%
app\schemas\auth.py                       11      0   100%
app\schemas\stage.py                      22      0   100%
app\schemas\user.py                        6      0   100%
app\utils\__init__.py                      0      0   100%
app\utils\hashing.py                       6      0   100%
app\utils\pagination.py                   11      0   100%
app\utils\time.py                          6      0   100%
--------------------------------------------------------------------
TOTAL                                    579     46    92%
================================================================== 43 passed in 32.11s ==================================================================
