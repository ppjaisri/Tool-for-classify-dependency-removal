import json

from pathlib import Path
from datetime import datetime
from typing import Union

from .logging_code import logging_code
from .requests_git_api import request_api
from .compare_code_change_by_ast import compare_replaced_code_with_dependency
from .element_classification import classify_commit_message, classify_python_code, classify_python_code_with_grouping


def extracttion_of_repalcement_and_removal_code(
    code: str
) -> tuple[list, list]:
    
    replaced = []
    deleted = []
    for line in code.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            replaced.append(line[1:].strip())
        elif line.startswith('-') and not line.startswith('---'):
            deleted.append(line[1:].strip())

    return replaced, deleted

def compare_with_keyword(
    patterns_path: Path,
    js_code: str
) -> bool:
    # patterns_path = dataset_path.joinpath('patterns_and_keywords')
    with open(f'{patterns_path}/javascript_built_in_keywords.json', 'r') as file:
        javascript_built_in_keywords = json.load(file)

    with open(f'{patterns_path}/node_keywords.json', 'r') as file:
        node_keywords = json.load(file)

    for keywords in javascript_built_in_keywords['Built_in_Function']:
        for keyword in keywords:
            if keyword in js_code:
                return True
            
    for keywords in node_keywords['Built_in_Classes']:
        for keyword in keywords:
            if keyword in js_code:
                return True

    else:
        return False

def get_file_from_commit(
    org: str,
    repo: str,
    target_file_path: str,
    removed_dependency_name: str,
    commit_sha: str,
    dataset_path: Path,
    github_token: str,
    spare_api: Union[bool, None] = None,
    detail: bool = False
) -> tuple[str, bool]:
    save_path = dataset_path.joinpath(f'04_pairs_of_commit/{org}:{repo}/{removed_dependency_name}')
    if not save_path.exists():
        save_path.mkdir(parents=True)

    # Saved file scheme: {commit sha}_{parent commit sha}.json
    saved_files = [file.stem.rsplit('.')[-1] for file in save_path.glob('*_*.json')]

    for saved_file in saved_files:
        current_commit_sha, parent_commit_sha = saved_file.split('_')

        if current_commit_sha == commit_sha:
            with open(f'{save_path}/{saved_file}.json', 'r') as file:
                data = json.load(file)
                return data['replaced_code'], True
            
        elif parent_commit_sha == commit_sha:
            with open(f'{save_path}/{saved_file}.json', 'r') as file:
                data = json.load(file)
                return data['deleted_code'], True
            
    headers = {"Authorization": f"Bearer {github_token}"}

    if detail:
        print(f'Getting parent commit: {parent_commit_sha} from {org}/{repo} \n by using spare api: {spare_api}')

    url = f'https://api.github.com/repos/{org}/{repo}/contents/{target_file_path}?ref={commit_sha}'

    res, request_left = request_api(
        api=url,
        package_name=f'{org}/{repo}',
        headers=headers,
        spare_api=spare_api
    )

    if detail:
        print(f'Request left: {request_left}')

    if res is None or res is False or res == []:
        if detail:
            print('{}No parent commit found{}, this is already an initial commit'.format(
                logging_code.ERROR, logging_code.ENDC))
        return None, False
    
    target_file_url = res['download_url']
    target_file, request_left = request_api(
        api=target_file_url,
        package_name=f'{org}/{repo}',
        headers=headers,
        spare_api=spare_api
    )

    if detail:
        print(f'Request left: {request_left}')

    if target_file is None or target_file is False or target_file == []:
        if detail:
            print('{}No parent commit found{}, this is already an initial commit'.format(
                logging_code.ERROR, logging_code.ENDC))
        return None, False
    
    return target_file, False

# def save_pair_of_code(
#     org: str,
#     repo: str,
#     file_name: str,
#     removed_dependency_name: str,
#     current_commit_sha: str,
#     parent_commit_sha: str,
#     dataset_path: str,
#     replaced_code: dict,
#     deleted_code: dict
# ) -> None:
#     save_path = dataset_path.joinpath(
#         f'04_pairs_of_commit/{org}:{repo}/{removed_dependency_name}')
#     if not save_path.exists():
#         save_path.mkdir(parents=True)

#     # Saved file scheme: {commit sha}_{parent commit sha}.json
#     # saved_files = [file.stem.rsplit('.')[-1] for file in save_path.glob('*_*.json')]
#     saved_file_name = f'{current_commit_sha}_{parent_commit_sha}'
#     res = {
#         'file_name': file_name,
#         'deleted_code': deleted_code,
#         'replaced_code': replaced_code
#     }

#     with open(f'{save_path}/{saved_file_name}.json', 'w') as file:
#         json.dump(res, file)

#     return

def get_package_json_at_commit_date(
    dataset_path: Path,
    org: str,
    repo: str,
    commit_date: str,
    commit_sha: str
) -> tuple[Union[dict, None], Union[dict, None]]:
    package_json_path = dataset_path.joinpath(f'01_package_json_history/{org}:{repo}')
    package_json_files = package_json_path.glob('*_*.json')
    commit_date = datetime.strptime(commit_date, '%Y-%m-%dT%H:%M:%SZ')

    candidate_files = []
    found_target_package_json = False
    target_package_json = list(package_json_path.glob(f'*_{commit_sha}.json'))
    
    if len(target_package_json) > 0:
        target_package_json_date = datetime.strptime(target_package_json[0].stem.split('_')[0], '%Y-%m-%dT%H:%M:%SZ')
        with open(target_package_json[0], 'r') as file:
            package_json = json.load(file)
        
        found_target_package_json = True

    for package_json_file in package_json_files:
        package_json_date = datetime.strptime(package_json_file.stem.split('_')[0], '%Y-%m-%dT%H:%M:%SZ')

        target_date = target_package_json_date if found_target_package_json else commit_date
        if package_json_date <= target_date:
            candidate_files.append(package_json_file)

    candidate_files = sorted(candidate_files, key=lambda x: x.stem.split('_')[0], reverse=True)

    if candidate_files == []:
        return None, None
    
    if not found_target_package_json:
        with open(candidate_files[0], 'r') as file:
            package_json = json.load(file)

    if len(candidate_files) == 1:
        return package_json, None
    else:
        with open(candidate_files[1], 'r') as file:
            parent_package_json = json.load(file)

        return package_json, parent_package_json


def removal_scenario_classification(
    # dependent_org_name: str,
    # dependent_repo_name: str,
    dependency_removal_scenarios: dict,
    dataset_path: Path,
    keywords_path: Path,
    github_token: str,
    update: bool = False,
    detail: bool = False,
    level_of_logging: int = 0
) -> list[dict[str, list]]:
    """
        This is the forth function.
        Purpose: Classify the dependency removal scenarios.
                 After classify each commit, the commit will be saved in each dataset folder.
        Result: Classified dependency removal scenarios.
        detail: Show the detail of the process.
        level_of_logging:  The level of detail of the classification.
                Default level is 0, which is general classification.
                Level 1 provide detail classification.
                Level 2 provide full detail classification.
    """
    
    classified_res = dict()
    found_dependency_usage_on_removed_code: bool = False
    for project_name, scenarios in dependency_removal_scenarios.items():
        dependent_org_name, dependent_repo_name = project_name.split(':')
        commit_description_path = dataset_path.joinpath(f'03_commits_description_since_install_until_remove/{dependent_org_name}:{dependent_repo_name}')
        # dependency_removal_scenarios = dependency_removal_scenarios[f'{dependent_org_name}:{dependent_repo_name}']

        dependency_name = scenarios['user_input']
        dependency_removal_scenario = scenarios['usage_interval_scenarios']
        removed_dependency_version = dependency_removal_scenario['version']
        classified_res = {
            'project_name': project_name,
            'dependency_name': dependency_name,
            'version': removed_dependency_version,
            'scenarios': dict(),
            'move_dep_to_other_fields': [],
        }
        # event_type = dependency_removal_scenario['event_type'] # ? moved or removed

        scenario_report = [
            f'{logging_code.INFO}Project\'s name{logging_code.ENDC} : {dependent_org_name}:{dependent_repo_name}',
            f'{logging_code.INFO}Dependency name{logging_code.ENDC}: {dependency_name}',
            f'{logging_code.INFO}Removed Version{logging_code.ENDC}: {removed_dependency_version}',
            f'{logging_code.INFO}Installed date{logging_code.ENDC} : {dependency_removal_scenario["installed_date"]}',
            f'{logging_code.INFO}Removed date{logging_code.ENDC}   : {dependency_removal_scenario["removed_date"]}',
            f'{logging_code.INFO}Usage period{logging_code.ENDC}   : {dependency_removal_scenario["usage_period"]} day(s)',
        ]

        print('\n'.join(scenario_report))
        print()

        since_date = dependency_removal_scenario['installed_date']
        since_date = datetime.strptime(since_date, '%Y-%m-%dT%H:%M:%SZ')
        since_date = since_date.replace(hour=0, minute=0, second=0)
        until_date = dependency_removal_scenario['removed_date']
        until_date = datetime.strptime(until_date, '%Y-%m-%dT%H:%M:%SZ')
        until_date = until_date.replace(hour=23, minute=59, second=59)

        commits_description = list()
        for file in commit_description_path.glob('*_*.json'):
            file_date = datetime.strptime(file.stem.split('_')[0], '%Y-%m-%dT%H:%M:%SZ')
            if since_date <= file_date <= until_date:
                commits_description.append(file)
        
        move_dep_to_other_fields = []
        remove_bloat_dependency = []
        shrink_library = []
        replace_dep_with_builtins = []
        replace_dep_with_another_dep = []
        unknown = []

        # pairs_of_replaced_and_removal_code = []
        for commit_description_path in commits_description:
            # print('commit_description_path:', commit_description_path)
            with open(commit_description_path, 'r') as f:
                commit_description = json.load(f)
            
            # * commit information
            commit_sha = commit_description['sha']
            commit_date = commit_description['commit']['committer']['date']
            # print('commit_sha before function:', commit_sha)

            package_json_at_commit_date, package_json_before_commit_date = get_package_json_at_commit_date(
                dataset_path=dataset_path,
                org=dependent_org_name,
                repo=dependent_repo_name,
                commit_date=commit_date,
                commit_sha=commit_sha
            )

            commit_parents = commit_description['parents']
            parent_commit_sha = commit_parents[0]['sha'] if commit_parents != [] else None
            commit_url = commit_description['html_url']
            commit_message = commit_description['commit']['message']
            preprocess_commit_message = commit_message.replace('\n\n', '\n').split('\n')
            preprocess_commit_message = [line.strip() for line in preprocess_commit_message if line.strip() != '']
            commit_message_pattern = classify_commit_message(preprocess_commit_message)
            patch_files = commit_description['files']

            if detail:
                print('\nCommit url: {}{}{}'.format(logging_code.INFO, commit_url, logging_code.ENDC))

            if 'Merge' in commit_message:
                continue

            found_package_json = False
            got_result = False
            for patch_file in patch_files:
                if 'patch' not in patch_file.keys():
                    continue

                file_name = patch_file['filename']
                change_status = patch_file['status']

                if change_status == 'renamed':
                    file_name = patch_file['previous_filename']

                if detail:
                    print('File name: {}{}{}'.format(logging_code.INFO, file_name, logging_code.ENDC))
                
                if file_name == 'package.json':
                    found_package_json = True

                if not file_name.endswith('.js'):
                    continue

                if 'test' in file_name or 'example' in file_name:
                    continue

                patch = patch_file['patch']

                if patch == []:
                    continue

                # * current commit information
                replaced_raw, is_replaced_saved = get_file_from_commit(
                    org=dependent_org_name,
                    repo=dependent_repo_name,
                    target_file_path=file_name,
                    removed_dependency_name=dependency_name,
                    commit_sha=commit_sha,
                    github_token=github_token,
                    dataset_path=dataset_path
                )

                # * parent commit information
                # ? Case no parent commit -> Initial commit
                if parent_commit_sha is None:
                    continue
                deleted_raw, is_deleted_saved = get_file_from_commit(
                    org=dependent_org_name,
                    repo=dependent_repo_name,
                    target_file_path=file_name,
                    removed_dependency_name=dependency_name,
                    commit_sha=parent_commit_sha,
                    github_token=github_token,
                    dataset_path=dataset_path
                )

                if deleted_raw is None:
                    continue
                if replaced_raw is None:
                    replaced_raw = ''

                replaced_raw_snippet, deleted_raw_snippet = extracttion_of_repalcement_and_removal_code(patch)
                replaced_import_classified = classify_python_code_with_grouping(replaced_raw_snippet)
                deleted_import_classified = classify_python_code_with_grouping(deleted_raw_snippet)
                replaced_classified = classify_python_code(replaced_raw_snippet)
                deleted_classified = classify_python_code(deleted_raw_snippet)

                replaced_classified_lines = replaced_classified['classified_lines']
                # replaced_comment = replaced_classified['comment']
                # replaced_code = replaced_classified['code_without_comment']
                deleted_classified_lines = deleted_classified['classified_lines']
                # deleted_comment = deleted_classified['comment']
                # deleted_code = deleted_classified['code_without_comment']

                # ? Detect removing dependency from commit message
                all_removed_commit_message = []
                for val in commit_message_pattern.values():
                    all_removed_commit_message += val

                commit_messsage_declare_as_removed = True if len(all_removed_commit_message) > 0 else False

                # ? Case find the deleted code which is contain the dependency import
                all_replaced_import = [] # ? simple_import + import_from + es5_import
                for val in replaced_import_classified.values():
                    all_replaced_import += val

                dependency_import_in_replaced_names = [replaced['module_name'] for replaced in all_replaced_import]
                dependency_import_in_replaced_names = set(dependency_import_in_replaced_names)
                found_dependency_import_in_replaced = dependency_name in dependency_import_in_replaced_names

                all_deleted_import = []  # ? simple_import + import_from + es5_import
                for val in deleted_import_classified.values():
                    all_deleted_import += val

                dependency_import_in_deleted_names = [deleted['module_name'] for deleted in all_deleted_import]
                dependency_import_in_deleted_names = set(dependency_import_in_deleted_names)
                found_dependency_import_in_deleted = dependency_name in dependency_import_in_deleted_names
                
                found_dependency_usage_in_deleted = False
                found_dependency_usage_in_deleted = any(dependency_name in line for line in deleted_raw)

                found_dependency_usage_in_replaced = False
                found_dependency_usage_in_replaced = any(dependency_name in line for line in replaced_raw)

                res = {
                    # 'removed_dependency_name': dependency_name,
                    'file_name': file_name,
                    'url': commit_url,
                    'commit_sha': commit_sha,
                    'commit_message': {
                        'raw': commit_message,
                        'preprocess': preprocess_commit_message,
                        'pattern': commit_message_pattern,
                    },
                    'replacement_code': {
                        'raw': replaced_raw_snippet,
                        'import_classified': replaced_import_classified,
                        # 'all_classified': replaced_classified_lines,
                    },
                    'deleted_code': {
                        'raw': deleted_raw_snippet,
                        'import_classified': deleted_import_classified,
                        # 'all_classified': deleted_classified_lines,
                    },
                }

                found_dependency_in_removed_code = found_dependency_import_in_deleted or found_dependency_usage_in_deleted
                found_dependency_in_replaced_code = found_dependency_import_in_replaced or found_dependency_usage_in_replaced
                
                deleted_dependencies = dependency_import_in_deleted_names - dependency_import_in_replaced_names
                replaced_dependencies = dependency_import_in_replaced_names - dependency_import_in_deleted_names

                if detail and level_of_logging > 0:
                    print(json.dumps(res, indent=4))
                    print()

                if detail and level_of_logging > 1:
                    print('{}found_dependency_import_in_replaced:{} {}'.format(logging_code.INFO, logging_code.ENDC, found_dependency_import_in_replaced))
                    print('{}found_dependency_import_in_deleted:{} {}'.format(logging_code.INFO, logging_code.ENDC, found_dependency_import_in_deleted))
                    print('{}found_dependency_in_removed_code:{} {}'.format(logging_code.INFO, logging_code.ENDC, found_dependency_in_removed_code))
                    print('{}found_dependency_in_replaced_code:{} {}'.format(logging_code.INFO, logging_code.ENDC, found_dependency_in_replaced_code))
                    print('{}dependency_import_in_deleted_names:{} {}'.format(logging_code.INFO, logging_code.ENDC, dependency_import_in_deleted_names))
                    print('{}dependency_import_in_replaced_names:{} {}'.format(logging_code.INFO, logging_code.ENDC, dependency_import_in_replaced_names))
                    print('{}deleted_dependencies:{} {}'.format(logging_code.INFO, logging_code.ENDC, deleted_dependencies))
                    print('{}replaced_dependencies:{} {}'.format(logging_code.INFO, logging_code.ENDC, replaced_dependencies))
                    if 'dependencies' in package_json_at_commit_date.keys():
                        print('{}dependencies in package_json_at_commit_date:{} {}'.format(logging_code.INFO, logging_code.ENDC, json.dumps(list(package_json_at_commit_date['dependencies'].keys()), indent=4)))
                    else:
                        print('{}package_json_at_commit_date:{} {}'.format(logging_code.INFO, logging_code.ENDC, json.dumps(package_json_at_commit_date, indent=4)))
                    print()

                # ? Case the target detendency is imported in replaced code
                if found_dependency_import_in_replaced:
                    found_dependency_usage_on_removed_code = True
                    if commit_messsage_declare_as_removed:
                        unknown.append(res)
                    continue

                # ? Case no import line in deleted code
                if not found_dependency_import_in_deleted:
                    if commit_messsage_declare_as_removed:
                        unknown.append(res)
                    continue
                else:
                    found_dependency_usage_on_removed_code = True

                # ? Case have import target dependency both in replaced and deleted code -> No dependency removal
                if found_dependency_in_removed_code and found_dependency_in_replaced_code:
                    found_dependency_usage_on_removed_code = True
                    if commit_messsage_declare_as_removed:
                        unknown.append(res)
                    continue

                # ? Catch the usage of dependency
                if found_dependency_usage_in_deleted:
                    found_dependency_usage_on_removed_code = True

                # ? Case no dependency changes in the package.json
                # ? Some case there are dependency removal in a source code but not remove in package.json
                # ? So, this case I note the dependency usage for determine between shrink library or remove bloat dependency
                if 'dependencies' not in package_json_at_commit_date.keys() and 'dependencies' not in package_json_before_commit_date.keys():
                    if commit_messsage_declare_as_removed:
                        unknown.append(res)
                    continue

                dependency_list_at_commit_date = list(package_json_at_commit_date.get('dependencies', {}).keys())

                if dependency_name in dependency_list_at_commit_date:
                    if commit_messsage_declare_as_removed:
                        unknown.append(res)
                    continue

                # ? Case move the dependency to other fields
                other_fields_dependency_in_package_json = []
                for key in package_json_at_commit_date.keys():
                    if 'Dependencies' in key:
                        if dependency_name in package_json_at_commit_date[key]:
                            other_fields_dependency_in_package_json += package_json_at_commit_date[key]
                            break
                if other_fields_dependency_in_package_json != []:
                    continue

                if dependency_name in dependency_list_at_commit_date and dependency_name in other_fields_dependency_in_package_json:
                    move_dep_to_other_fields.append(res)
                    continue

                # ? Case replace the removed dependency
                contain_keyword_in_replaced_code = compare_with_keyword(keywords_path, replaced_raw_snippet)

                got_result = True
                if replaced_dependencies:
                    replace_dep_with_another_dep.append(res)
                    continue

                else:
                    # ? Case only remove the dependency
                    if not found_dependency_usage_on_removed_code:
                        remove_bloat_dependency.append(res)
                        continue

                    elif contain_keyword_in_replaced_code:
                        replace_dep_with_builtins.append(res)
                        continue

                    elif not contain_keyword_in_replaced_code:
                        # print(commit_url)
                        # print(file_name)
                        if change_status == 'removed':
                            shrink_library.append(res)
                            continue

                        similarity = compare_replaced_code_with_dependency(
                            dataset_path=dataset_path,
                            dependency_name=dependency_name,
                            version=removed_dependency_version,
                            deleted_code_snippet=deleted_raw_snippet,
                            deleted_source_code=deleted_raw,
                            replaced_code_snippet=replaced_raw_snippet,
                            replaced_source_code=replaced_raw,
                            update=update,
                            detail=detail
                        )

                        if similarity:
                            replace_dep_with_builtins.append(res)
                        else:
                            shrink_library.append(res)
                        continue

                    else:
                        unknown.append(res)
                        continue

            else:
                package_json_at_commit_date, package_json_before_commit_date = get_package_json_at_commit_date(
                    dataset_path=dataset_path,
                    org=dependent_org_name,
                    repo=dependent_repo_name,
                    commit_date=commit_date,
                    commit_sha=commit_sha
                )

                if found_package_json and not got_result:
                    res = {
                        # 'removed_dependency_name': dependency_name,
                        'file_name': 'package.json',
                        'url': commit_url,
                        'commit_sha': commit_sha,
                        'commit_message': {
                            'raw': commit_message,
                            'preprocess': preprocess_commit_message,
                            'pattern': commit_message_pattern,
                        },
                    }

                    if package_json_at_commit_date is None:
                        unknown.append(res)
                        continue

                    # print('commit_sha before function:', commit_sha)

                    if detail and level_of_logging > 0:
                        print('package_json_at_commit_date:', json.dumps(package_json_at_commit_date, indent=4))
                        print('package_json_before_commit_date:', json.dumps(package_json_before_commit_date, indent=4))

                    if package_json_at_commit_date is None:
                        unknown.append(res)
                        continue

                    # ? Case not a dependnecy removal
                    if package_json_at_commit_date is not None and package_json_before_commit_date is None:
                        continue

                    # ? Case no dependency changes in the package.json
                    if 'dependencies' not in package_json_at_commit_date.keys() and 'dependencies' not in package_json_before_commit_date.keys():
                        continue

                    if dependency_name in package_json_at_commit_date.get('dependencies', {}):
                        continue

                    # ? Case move the dependency to other fields
                    other_fields_deps = []
                    for key in package_json_at_commit_date:
                        if 'ependencies' in key:
                            other_fields_deps.extend(package_json_at_commit_date[key])

                    if dependency_name in package_json_before_commit_date.get('dependencies', {}) and dependency_name in other_fields_deps:
                        move_dep_to_other_fields.append(res)
                        continue

                    package_json_patch = next((p for p in commit_description['files'] if p['filename'] == 'package.json'), None)
                    if package_json_patch:
                        replaced, deleted = extracttion_of_repalcement_and_removal_code(package_json_patch['patch'])
                        if dependency_name in ''.join(deleted) and dependency_name not in ''.join(replaced):
                            remove_bloat_dependency.append(res)

        # ? prevent detect as unknown if found other removed categories in a same dependency usage.
        if any([move_dep_to_other_fields, remove_bloat_dependency, shrink_library, 
            replace_dep_with_builtins, replace_dep_with_another_dep]):
            unknown = []

        classified_res['scenarios'] = {
            # 'move_dep_to_other_fields': move_dep_to_other_fields,
            'shrink_library': shrink_library,
            'remove_bloat_dependency': remove_bloat_dependency,
            'replace_dep_with_builtins': replace_dep_with_builtins,
            'replace_dep_with_another_dep': replace_dep_with_another_dep,
            'unknown': unknown
        }

        classified_res['move_dep_to_other_fields'] = move_dep_to_other_fields

    # print(json.dumps(classified_res, indent=4))

    return classified_res