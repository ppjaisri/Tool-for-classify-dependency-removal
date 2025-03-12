import json
from packaging import version

def load_package_json(file_path):
    """
    Load a package.json file into a Python dictionary.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def detect_patch_changes(old_pkg, new_pkg):
    """
    Detect patch-level changes in dependencies between two package.json files.
    
    Args:
        old_pkg (dict): Parsed old package.json file.
        new_pkg (dict): Parsed new package.json file.
        
    Returns:
        list: A list of dictionaries containing patch-level changes.
    """
    dependency_fields = ['dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies']
    patch_changes = []

    for field in dependency_fields:
        old_deps = old_pkg.get(field, {})
        new_deps = new_pkg.get(field, {})

        for dep, new_version in new_deps.items():
            old_version = old_deps.get(dep)

            if old_version and is_valid_semver(old_version) and is_valid_semver(new_version):
                if version.parse(old_version) < version.parse(new_version) and version_diff_type(old_version, new_version) == 'patch':
                    patch_changes.append({
                        "dependency": dep,
                        "type": field,
                        "old_version": old_version,
                        "new_version": new_version
                    })

    return patch_changes

def is_valid_semver(ver):
    """
    Check if a version string is a valid semantic version.
    
    Args:
        ver (str): Version string to validate.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        version.parse(ver)
        return True
    except:
        return False

def version_diff_type(old_ver, new_ver):
    """
    Determine the semantic version difference type (major, minor, or patch).
    
    Args:
        old_ver (str): Old version string.
        new_ver (str): New version string.
        
    Returns:
        str: The version difference type ('major', 'minor', 'patch') or None.
    """
    old = version.parse(old_ver)
    new = version.parse(new_ver)

    if new.major != old.major:
        return 'major'
    elif new.minor != old.minor:
        return 'minor'
    elif new.micro != old.micro:
        return 'patch'
    return None

def display_patch_changes(patch_changes):
    """
    Display patch-level changes in a table format.
    
    Args:
        patch_changes (list): A list of dictionaries containing changes.
    """
    if patch_changes:
        print("Patch-Level Dependency Changes:")
        print("{:<20} {:<20} {:<15} {:<10}".format("Dependency", "Type", "Old Version", "New Version"))
        print("-" * 70)
        for change in patch_changes:
            print("{:<20} {:<20} {:<15} {:<10}".format(
                change['dependency'], 
                change['type'], 
                change['old_version'], 
                change['new_version']
            ))
    else:
        print("No patch-level dependency changes found.")
