import json

from pathlib import Path
from collections import defaultdict

from src.interfaces.result import Move_Dep_Scenario


def analyze_package_json_versions_with_dates(
    folder_path: Path
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    moved_dependencies = []
    removed_dependencies = []
    installed_dependencies = []
    updated_dependencies = []

    package_json_files = sorted(
        [file for file in folder_path.iterdir() if file.suffix == '.json'],
        # Sort by full timestamp in filename
        key=lambda x: x.stem.split('_')[0]
    )

    previous_dependencies = {}
    previous_timestamp = None
    install_history = defaultdict(list)

    for file_path in package_json_files:
        with file_path.open('r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                temp = file.read()
                if temp == '':
                    continue
                data = json.loads(temp.strip())

        if isinstance(data, list):
            data = data[0]

        current_timestamp = file_path.stem.split('_')[0]
        if data is None:
            continue

        current_dependencies = {
            "dependencies": data.get("dependencies", {}),
            "devDependencies": data.get("devDependencies", {}),
            "peerDependencies": data.get("peerDependencies", {}),
            "optionalDependencies": data.get("optionalDependencies", {}),
            "bundleDependencies": data.get("bundleDependencies", {}),
        }

        prev_location = {dep: section for section,
                         deps in previous_dependencies.items() for dep in deps}
        curr_location = {dep: section for section,
                         deps in current_dependencies.items() for dep in deps}

        for section, deps in current_dependencies.items():
            for dep, version in deps.items():
                if dep not in prev_location:
                    installed_dependencies.append({
                        'name': dep, 'version': version, 'installed_date': current_timestamp
                    })
                    install_history[dep].append({
                        'version': version, 'installed_date': current_timestamp
                    })
                elif prev_location[dep] != section:
                    moved_dependencies.append({
                        'name': dep, 'moved_to': section, 'version': version, 'moved_date': previous_timestamp
                    })
                elif dep in prev_location and prev_location[dep] == section and previous_dependencies[prev_location[dep]][dep] != version:
                    updated_dependencies.append({
                        'name': dep, 'old_version': previous_dependencies[prev_location[dep]][dep],
                        'new_version': version, 'updated_date': current_timestamp
                    })

        # Improved removal tracking to support multiple usage periods
        for dep, prev_sec in prev_location.items():
            if dep not in curr_location and dep in previous_dependencies[prev_sec]:
                removed_version = previous_dependencies[prev_sec][dep]
                install_match = None
                for install_event in sorted(install_history[dep], key=lambda x: x['installed_date'], reverse=True):
                    if install_event['version'] == removed_version and install_event['installed_date'] <= current_timestamp:
                        install_match = install_event
                        break

                removed_dependencies.append({
                    'name': dep,
                    'version': removed_version,
                    'removed_date': current_timestamp,
                    'installed_date': install_match['installed_date'] if install_match else None
                })

        previous_dependencies = current_dependencies
        previous_timestamp = current_timestamp

        moved_dependencies = [dict(t) for t in {tuple(
            d.items()) for d in moved_dependencies}]
        removed_dependencies = [dict(t) for t in {tuple(
            d.items()) for d in removed_dependencies}]
        installed_dependencies = [dict(t) for t in {tuple(
            d.items()) for d in installed_dependencies}]
        updated_dependencies = [dict(t) for t in {tuple(
            d.items()) for d in updated_dependencies}]

    return moved_dependencies, removed_dependencies, installed_dependencies, updated_dependencies


def detect_moving_dependency_to_other_fields(
    folder_path: Path
) -> dict[Move_Dep_Scenario]:
    moved, removed, installed, updated = analyze_package_json_versions_with_dates(
        folder_path)

    return {
        'moved': moved,
        'removed': removed,
        'installed': installed,
        'updated': updated
    }
