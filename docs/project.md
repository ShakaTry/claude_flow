# Idée : Orchestration externe de Claude Code

## Concept de base

Au lieu que Claude orchestre tout, avoir un **script maître** (Python/Bash) qui :
1. Lance Claude pour des tâches spécifiques
2. Récupère les résultats dans un format structuré (JSON)
3. Exécute les actions déterministes
4. Relance Claude pour la suite

## Architecture proposée

```
script-orchestrateur.py
    ↓
    ├── Initialisation: créer .claude-workflow/
    │   ├── state.json          # État global du workflow
    │   ├── phase_outputs/      # Outputs de chaque phase
    │   ├── logs/               # Logs détaillés
    │   └── .gitignore          # Pour ne pas commiter ce dossier
    ↓
    ├── Claude Session 0: Analyse du contexte Git
    │   ├── input: état actuel du repo
    │   └── output: git-context.json
    │       - branche actuelle
    │       - changements non commités
    │       - remote configuré
    │       - stratégie de branching
    ↓
    ├── Script: Validation du contexte
    │   └── vérifie que les conditions sont OK pour continuer
    ↓
    ├── Claude Session 1: Analyse de la fonctionnalité
    │   ├── input: nom de la fonctionnalité + git-context.json
    │   └── output: analysis.json
    │       - composants identifiés
    │       - cas de test nécessaires
    │       - dépendances
    ↓
    ├── Script: Applique workflow Git (partie 1)
    │   ├── lit git-context.json
    │   ├── crée la branche selon la stratégie
    │   └── prépare l'environnement
    ↓
    ├── Claude Session 2: Génération documentation
    │   ├── input: analysis.json + template
    │   └── output: docs/tests/{feature}_tests.md
    ↓
    ├── Script: Validation de la documentation
    │   ├── vérifie que le fichier existe
    │   ├── contrôle la structure markdown
    │   └── valide la présence des sections obligatoires
    ↓
    ├── Claude Session 3: Génération message commit/PR
    │   ├── input: changements effectués
    │   └── output: messages.json
    │       - commit message
    │       - PR title
    │       - PR body
    ↓
    └── Script: Finalise workflow Git (partie 2)
        ├── commit avec le message généré
        ├── push selon la stratégie
        ├── crée PR avec les infos générées
        └── nettoie .claude-workflow/
```

## Structure du dossier .claude-workflow/

```bash
.claude-workflow/
├── state.json          # État global du workflow
├── phase_outputs/      # Outputs de chaque phase
│   ├── git-context.json
│   ├── analysis.json
│   └── messages.json
├── logs/               # Logs détaillés
│   └── workflow-{timestamp}.log
└── .gitignore          # Pour ne pas commiter ce dossier
```

## Principe d'implémentation

Le script orchestrateur devrait :

1. **Lancer Claude via stdin** avec des prompts complets et structurés
2. **Capturer les sorties JSON** de chaque phase
3. **Exécuter les actions déterministes** (Git, création de fichiers)
4. **Gérer les erreurs** à chaque étape
5. **Maintenir un état** dans un dossier temporaire `.claude-workflow/` (dans le repo)

### Capture des outputs Claude

```python
# Comment capturer proprement les outputs JSON de Claude
def extract_json_from_claude_output(output):
    """Claude peut retourner du texte + JSON, on extrait le JSON"""
    # Chercher entre ```json et ```
    json_match = re.search(r'```json\n(.*?)\n```', output, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))
    # Sinon essayer de parser tout le output
    return json.loads(output)
```

Technologies possibles :
- Python avec subprocess pour appeler Claude CLI
- Node.js avec le SDK Claude
- Bash avec des fichiers temporaires pour l'état

## Structure des prompts

```python
PROMPT_TEMPLATES = {
    "git_analysis": """
You are analyzing a Git repository state. Return ONLY a JSON object with:
- current_branch: string
- has_uncommitted: boolean  
- remote_url: string
- branching_strategy: "feature-branch" or "git-flow"
- base_branch: string
- warnings: array of strings

Current directory: {cwd}
Git status output: {git_status}
""",
    
    "feature_analysis": """
Given this Git context: {git_context}
Analyze the feature: {feature_name}

Return ONLY a JSON object with:
- feature_name: string
- main_file: string (path)
- components: array of component names
- test_cases: array of test descriptions
- dependencies: array of package names
- edge_cases: array of edge case descriptions
""",

    "doc_generation": """
Given this feature analysis: {analysis}
Generate ONLY the test documentation in Markdown format.

Use this template structure:
- Overview
- Test Cases (from the analysis)
- Edge Cases
- Dependencies
""",

    "commit_messages": """
Given these changes: {changes}
Generate ONLY a JSON object with:
- commit_msg: string (conventional commit format)
- pr_title: string (clear and concise)
- pr_body: string (markdown format with sections)
"""
}
```

## Avantages

1. **Séparation claire** : Claude = intelligence, Script = orchestration
2. **Déterministe** : Le workflow Git est 100% prévisible
3. **Traçabilité** : Chaque étape produit des artefacts (JSON, logs)
4. **Testable** : On peut tester chaque phase indépendamment
5. **Pas de dérive** : Claude ne peut pas "oublier" des étapes

## Inconvénients

1. **Complexité initiale** : Plus de code à écrire
2. **Moins interactif** : Sessions Claude séparées
3. **Gestion d'état** : Besoin de passer le contexte entre sessions

## Variantes possibles

### Variante 1: Avec fichier de workflow

Un fichier YAML ou JSON pourrait définir le workflow de manière déclarative :
- Étapes séquentielles
- Type d'action (claude, bash, validation)
- Inputs/outputs de chaque étape
- Conditions de succès

### Variante 2: Avec hooks d'orchestration
- Des hooks Python dans le workflow pour l'extensibilité
- Permettent d'ajouter du comportement custom à chaque phase
- Points d'extension : before_phase, after_phase, on_error
- Exemple : logging custom, notifications, métriques

## Formats de données entre phases

### git-context.json (Session 0 → Session 1)
```json
{
  "current_branch": "main",
  "has_uncommitted": false,
  "remote_url": "github.com/user/repo",
  "branching_strategy": "feature-branch",
  "base_branch": "main",
  "warnings": []
}
```

### analysis.json (Session 1 → Session 2)
```json
{
  "feature_name": "user-authentication",
  "main_file": "src/auth/login.py",
  "components": ["LoginForm", "AuthService", "SessionManager"],
  "test_cases": [
    "valid credentials",
    "invalid password",
    "session timeout"
  ],
  "dependencies": ["bcrypt", "jwt"],
  "edge_cases": ["concurrent login", "rate limiting"]
}
```

### messages.json (Session 3 → Script final)
```json
{
  "commit_msg": "feat(auth): add user authentication with JWT tokens",
  "pr_title": "Add user authentication feature",
  "pr_body": "## Description\n\nImplements JWT-based authentication...\n\n## Changes\n- Added LoginForm component\n- Created AuthService\n- Implemented SessionManager\n\n## Testing\n- Unit tests for auth logic\n- Integration tests for login flow"
}
```

## Gestion des erreurs

Le script devrait gérer :
1. **Échec de Claude** : Timeout, erreur de parsing JSON
2. **Conflits Git** : Branche existante, merge conflicts
3. **Validation** : Documentation incomplète, format incorrect

### Stratégie de retry avec fallback

```python
def execute_claude_phase_with_retry(phase_name, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            output = run_claude(prompt)
            json_data = extract_json_from_claude_output(output)
            validate_schema(json_data, SCHEMAS[phase_name])
            return json_data
        except (JSONDecodeError, ValidationError) as e:
            if attempt < max_retries - 1:
                # Prompt plus explicite pour le retry
                prompt = make_prompt_more_explicit(prompt, e)
                continue
            else:
                # Fallback: mode interactif ou valeurs par défaut
                return get_fallback_values(phase_name)
```

## Points d'amélioration

1. **Cache des analyses** : Réutiliser l'analyse si on relance
2. **Mode dry-run** : Tester sans faire de changements Git
3. **Configuration** : Fichier de config pour les paramètres
4. **Logs détaillés** : Garder trace de toutes les exécutions

## Critères de succès MVP

1. **Fiabilité** : 95% des workflows se terminent sans intervention manuelle
2. **Traçabilité** : Chaque exécution produit des logs exploitables
3. **Reproductibilité** : Même input = même output (Git permettant)
4. **Performance** : < 2 minutes pour un workflow complet
5. **Maintenabilité** : Ajouter une nouvelle phase en < 30 minutes

## Conclusion

Cette approche transforme Claude en **moteur d'exécution** plutôt qu'en chef d'orchestre. 
C'est potentiellement plus robuste pour des workflows complexes et répétitifs.

L'architecture modulaire permet :
- De remplacer Claude par un autre LLM facilement
- De tester chaque phase indépendamment
- D'avoir une traçabilité complète
- De garantir la reproductibilité du workflow