import json
import os
import re
import subprocess
import sys

def get_latest_tag():
    try:
        output = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], stderr=subprocess.STDOUT).decode().strip()
        return output
    except subprocess.CalledProcessError:
        return None

def get_changelog(since_tag):
    if since_tag:
        cmd = ["git", "log", f"{since_tag}..HEAD", "--oneline"]
    else:
        cmd = ["git", "log", "--oneline"]
    
    try:
        output = subprocess.check_output(cmd).decode().strip()
        return output
    except subprocess.CalledProcessError:
        return "No commits found."

def update_file(path, pattern, replacement):
    if not os.path.exists(path):
        print(f"Warning: {path} not found.")
        return False
    
    with open(path, 'r') as f:
        content = f.read()
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content == content:
        print(f"No changes made to {path} (pattern not found or already matches).")
        return False

    with open(path, 'w') as f:
        f.write(new_content)
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 bump.py <new_version>")
        sys.exit(1)
    
    new_version = sys.argv[1]
    # Strip leading 'v' if present
    if new_version.startswith('v'):
        new_version = new_version[1:]
    
    # Paths
    pyproject_path = "pyproject.toml"
    # Find manifest.json in custom_components
    manifest_path = None
    for root, dirs, files in os.walk("custom_components"):
        if "manifest.json" in files:
            manifest_path = os.path.join(root, "manifest.json")
            break
    
    if not manifest_path:
        print("Error: could not find manifest.json in custom_components/")
        sys.exit(1)
    
    print(f"Bumping version to {new_version}...")
    
    changed = False
    # Update pyproject.toml
    if update_file(pyproject_path, r'version = ".*"', f'version = "{new_version}"'):
        changed = True
    
    # Update manifest.json
    if update_file(manifest_path, r'"version": ".*"', f'"version": "{new_version}"'):
        changed = True
    
    if not changed:
        print("No files were updated. Maybe version is already correct?")
        # We might still want to tag if the user wants to re-tag current state, 
        # but usually we expect a bump.
    
    # Commit changes
    try:
        subprocess.check_call(["git", "add", pyproject_path, manifest_path])
        # Check if there are staged changes
        try:
            subprocess.check_call(["git", "diff", "--cached", "--quiet"])
            print("No changes to commit.")
        except subprocess.CalledProcessError:
            # diff returns non-zero if there are changes
            subprocess.check_call(["git", "commit", "-m", f"Bump version to {new_version}"])
            print("Committed version changes.")
    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e}")

    # Tagging
    latest_tag = get_latest_tag()
    changelog = get_changelog(latest_tag)
    
    tag_name = f"v{new_version}"
    tag_message = f"Version {new_version}\n\nChangelog:\n{changelog}"
    
    # Check if tag already exists
    try:
        subprocess.check_call(["git", "rev-parse", tag_name], stderr=subprocess.DEVNULL)
        print(f"Error: Tag {tag_name} already exists.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        pass

    print(f"Creating tag {tag_name}...")
    try:
        subprocess.check_call(["git", "tag", "-a", tag_name, "-m", tag_message])
        print(f"Successfully tagged {tag_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating tag: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
