import json
from pathlib import Path

from src.components.detect_chage_of_dependency_field import load_package_json, detect_patch_changes, display_patch_changes


def detect_moving_dependency_to_other_fields(
    removed_dependency: str,
    # version_before_change: str,
    # version_after_change: str,
    file_path: Path
) -> None:
    # print(json.dumps({
    #     'removed_dependency': removed_dependency,
    #     # 'version_before_change': version_before_change,
    #     # 'version_after_change': version_after_change,
    #     'file_path': str(file_path)
    # }, indent=4))

    # Case 1: Replace the depednency with built-ins function or custom function

    # Case 2: Replace the dependency with another dependency

    # Case 3: Remove the bloat dependency

    # Case 4: Shrink library

    # Case 5: Move the dependency to other fields

    # Case 6: Unknown

    all_package_json_path = file_path.glob('*')

    for each_package_json_path in all_package_json_path:
        package_json = load_package_json(each_package_json_path)

    commits = file_path.glob('*')
    
    has_packages_json = False
    for commit in commits:
        with open(commit, 'r') as file:
            res = json.load(file)

        try:
            changed_files = res['files']
        except KeyError:
            print(json.dumps(res, indent=4))
            break
        for changed_file in changed_files:
            filename = changed_file['filename']
            # print(filename)
            # For JavaScript files
            if 'patch' in changed_file.keys():
                patch = changed_file['patch']
            else:
                continue
            if filename == 'package.json':
                has_packages_json = True
                lines = patch.split('\n')

                additions = []
                deletions = []
                for line in lines:
                    if line.startswith('+') and not line.startswith('+++'):
                        additions.append(line[1:].strip())
                    elif line.startswith('-') and not line.startswith('---'):
                        deletions.append(line[1:].strip())

                for line in additions:
                    pass

                print(json.dumps({
                    'filename': filename,
                    'additions': additions,
                    'deletions': deletions
                }, indent=4))
                # print("Additions:", additions)
                # print("Deletions:", deletions)
                
            if filename.endswith('.js'):
                pass

    return
