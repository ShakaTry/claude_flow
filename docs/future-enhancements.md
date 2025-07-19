 on vas tester en conditions r# Future Enhancements - Système de Documentation Intelligente

## Concept : Tracking et Génération Automatique

### 1. Système de Tracking des Docs

Le script maintiendra un registre (`docs/tests/.registry.json`) contenant :
```json
{
  "generated_docs": [
    {
      "file": "prompts.py",
      "doc_path": "docs/tests/prompts_tests.md",
      "generated_at": "2025-01-19",
      "commit": "a1b2c3d",
      "coverage": ["PROMPT_TEMPLATES", "enhance_prompt_with_examples"]
    }
  ]
}
```

### 2. Analyse Automatique

Quand l'utilisateur demande : `python orchestrator.py prompts.py`

Le script :
1. **Analyse le fichier** : Liste toutes les fonctions/classes
2. **Vérifie le registre** : Quelles parties ont déjà une doc
3. **Identifie les manques** : Ce qui n'est pas documenté
4. **Génère une liste** : Des docs à créer

### 3. Boucle de Génération

```python
# Pseudo-code du futur orchestrateur
files_to_document = analyze_missing_docs("prompts.py")
# Résultat: ["prompt_validation", "error_recovery_prompts", "project_type_handling"]

for component in files_to_document:
    # Le SCRIPT lance un workflow pour chaque composant
    run_workflow(f"{file_name}-{component}", 
                 description=f"Tests for {component} in {file_name}")
    
    # Met à jour le registre après chaque génération
    update_registry(file_name, component, doc_path)
```

### 4. Commandes Futures

```bash
# Documenter un fichier complet (génère plusieurs docs si nécessaire)
python orchestrator.py --file prompts.py

# Vérifier la couverture de documentation
python orchestrator.py --coverage

# Documenter tous les fichiers non documentés
python orchestrator.py --all-missing

# Forcer la régénération même si doc existe
python orchestrator.py --file prompts.py --force
```

### 5. Intelligence du Script

Le script pourra :
- **Détecter les changements** : Si un fichier a changé depuis la dernière doc
- **Prioriser** : Documenter d'abord les fichiers critiques
- **Grouper** : Créer une seule PR avec plusieurs docs liées
- **Éviter les doublons** : Ne pas recréer une doc existante

### 6. Exemple de Workflow Complet

```bash
$ python orchestrator.py --file validators.py

Analyzing validators.py...
Found 5 components:
✓ validate_git_context (already documented)
✓ validate_feature_analysis (already documented)
✗ validate_messages (missing)
✗ get_validation_errors (missing)
✗ suggest_fixes (missing)

Generating documentation for 3 missing components...

[Workflow 1/3] Creating docs/validators-validate_messages...
[Workflow 2/3] Creating docs/validators-get_validation_errors...
[Workflow 3/3] Creating docs/validators-suggest_fixes...

Created PR #42: "docs: add missing test documentation for validators.py"
```

## Points Clés

1. **Le script contrôle tout** : Claude ne fait que générer le contenu demandé
2. **Pas de duplication** : Le registre évite de recréer des docs existantes
3. **Automatisation complète** : Une commande peut générer toute la doc manquante
4. **Traçabilité** : On sait exactement quelle doc existe pour quel composant

C'est exactement l'esprit du projet : l'orchestration externe où les scripts Python dirigent et Claude est juste un moteur de génération.