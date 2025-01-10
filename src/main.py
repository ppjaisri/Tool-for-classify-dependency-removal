import json
from pathlib import Path

from src.components.detect_moving_dep_to_other_fileds import detect_moving_dependency_to_other_fields


def read_file(file_path: Path) -> dict:
    with open(file_path, 'r') as file:
        res = json.load(file)

    return res

def main(root_dataset_path):
    database_path = root_database_path.joinpath('package_json_history')

    project_removed_deps_path = root_database_path.joinpath('dependency_removed_with_dependents.json')
    project_removed_deps = read_file(project_removed_deps_path)

    # Case 1: Replace the depednency with built-ins function or custom function

    # Case 2: Replace the dependency with another dependency

    # Case 3: Remove the bloat dependency

    # Case 4: Shrink library

    # Case 5: Move the dependency to other fields

    # projects = database_path.glob('*')
    for removed_dependency, project_which_remove in project_removed_deps.items():
        print(f'Removed dependency name: {removed_dependency}')
        for item in project_which_remove:
            project_name = item['repo_link'].rsplit('/', 2)[1:]
            project_name = ':'.join(project_name)
            print(f'Project name: {project_name}')

            version_before_change = item['version_before_change']['version']
            version_after_change = item['version_after_change']['version']

            path_to_project = database_path.joinpath(project_name)

            try:
                detect_moving_dependency_to_other_fields(
                    removed_dependency=removed_dependency, 
                    # version_before_change=version_before_change,
                    # version_after_change=version_after_change,
                    file_path=path_to_project
                )
            except ValueError:
                print(f'Error in {project_name}')
                continue

    # Case 6: Unknown


if __name__ == '__main__':
    current_path = Path(__file__).parent
    root_database_path = Path('/mnt/ext-hdd2/npm_self_contained_2024_P/current_dataset/not_self_contained_and_self_contained')
    
    main(root_dataset_path=root_database_path)