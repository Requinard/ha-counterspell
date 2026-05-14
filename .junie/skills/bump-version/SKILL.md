---
name: bump-version
description: Bumps the project version in manifest.json and pyproject.toml, then creates a git tag with the changelog.
---

# Bump Version Skill

Use this skill when you need to release a new version of the project. This skill automates updating the version strings in configuration files and creating a git tag that includes the changelog since the last version.

## Key Principles
- Maintain version consistency across `pyproject.toml` and `manifest.json`.
- Automated changelog generation based on git commit history.
- Proper git tagging for releases.

## Guidelines
1. Ensure all changes are committed before bumping the version.
2. The skill expects a semantic version number (e.g., `0.3.0`).
3. It will update:
   - `pyproject.toml`: `version` field in `[project]` section.
   - `custom_components/counterspell/manifest.json`: `version` field.
4. It will create a git tag `v<version>` with a message containing:
   - The version number.
   - A list of commits since the previous tag.

## Usage
You can ask Junie to "bump version to X.Y.Z" or "bump version to the next minor/patch version".
Junie will then use the provided script to perform the updates.

## Automation Script
The skill includes a script to handle the process:
- `scripts/bump.py`: The main automation script.

Run it using:
```bash
python3 .junie/skills/bump-version/scripts/bump.py <new_version>
```
