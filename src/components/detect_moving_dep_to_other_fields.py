import json

from pathlib import Path

from src.interfaces.result import Move_Dep_Scenario


def extract_dependency_events(
    json_dir: Path
) -> dict[str, list[dict]]:
    json_files = sorted(json_dir.rglob("*.json"), key=lambda x: x.name)

    installed = []
    removed = []
    moved = []
    updated = []

    previous_deps = {}
    previous_meta = {}
    previous_date = None

    for file in json_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                with open(file, 'r', encoding='latin1') as f:
                    data = json.load(f)
            except Exception:
                continue

        dependencies = data.get("dependencies", {})
        meta_fields = {
            "devDependencies": data.get("devDependencies", {}),
            "peerDependencies": data.get("peerDependencies", {}),
            "optionalDependencies": data.get("optionalDependencies", {}),
        }
        current_date, commit_sha = file.stem.split('_')

        for dep, version in dependencies.items():
            if dep not in previous_deps:
                installed.append({
                    "name": dep,
                    "version": version,
                    "installed_date": current_date
                })
            elif previous_deps[dep] != version:
                updated.append({
                    "name": dep,
                    "old_version": previous_deps[dep],
                    "new_version": version,
                    "updated_date": current_date
                })

        for dep, version in previous_deps.items():
            if dep not in dependencies:
                moved_flag = False
                for field_name, field_deps in meta_fields.items():
                    if dep in field_deps:
                        moved.append({
                            "name": dep,
                            "moved_to": field_name,
                            "version": field_deps[dep],
                            "moved_date": current_date
                        })
                        moved_flag = True
                        break
                if not moved_flag:
                    installed_entry = next(
                        (i for i in installed if i["name"] == dep), None)
                    removed.append({
                        "name": dep,
                        "version": version,
                        "removed_date": current_date,
                        "installed_date": installed_entry["installed_date"] if installed_entry else None
                    })

        previous_deps = dependencies
        previous_meta = meta_fields
        previous_date = current_date

        res = {
            "installed": installed,
            "removed": removed,
            "moved": moved,
            "updated": updated
        }

    return res

def detect_moving_dependency_to_other_fields(
    folder_path: Path
) -> dict[Move_Dep_Scenario]:

    res = extract_dependency_events(folder_path)


    return {
        'moved': res['moved'],
        'removed': res['removed'],
        'installed': res['installed'],
        'updated': res['updated']
    }
