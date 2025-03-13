import json

from pathlib import Path
from typing import Union
from datetime import datetime
from collections import defaultdict

from .requests_git_api import request_api
from .logging_code import logging_code
from ..interfaces import User_Input


def get_commit_history(
    # dependent_name: str,
    org: str,
    repo: str,
	github_token: str,
	save_path: Path,
    since: str,
    until: str,
	update: bool = False,
	spare_api: Union[str, None] = None,
    detail: bool = False,
    level_of_logging: int = 0,
) -> int:
    headers = {"Authorization": f"Bearer {github_token}"}

    page = 1

    save_path = save_path.joinpath(f'{org}:{repo}')
    saved_files = None
    if save_path.exists():
        saved_files = save_path.glob('*.json')
        saved_files = [str(file.name) for file in saved_files]

    request_left = None
    while True:
        if isinstance(since, str):
            # try:
            #     since = datetime.strptime(since, '%Y-%m-%dT%H:%M:%SZ')
            # except ValueError:
                since = datetime.strptime(since, '%Y-%m-%dT%H:%M:%SZ')
                
        if isinstance(until, str):
            # try:
            #     until = datetime.strptime(until, '%Y-%m-%dT%H:%M:%SZ')
            # except ValueError:
                until = datetime.strptime(until, '%Y-%m-%dT%H:%M:%SZ')

        if since > until:
            since, until = until, since

        # since = since.strftime('%Y-%m-%dT%H:%M:%SZ')
        # until = until.strftime('%Y-%m-%dT%H:%M:%SZ')

        since_str = since.replace(hour=0, minute=0, second=0).strftime(
            '%Y-%m-%dT%H:%M:%SZ')
        until_str = until.replace(hour=23, minute=59, second=59).strftime(
            '%Y-%m-%dT%H:%M:%SZ')

        commit_api = f'https://api.github.com/repos/{org}/{repo}/commits?since={since_str}&until={until_str}&per_page=100&page={page}'
        # print(commit_api)
        # break

        file_name = f'{since_str}_to_{until_str}_commits_page_{page}.json'
        need_to_delete_old_file = {'delete': False, 'file': None}
        if saved_files is not None:
            if file_name in saved_files:
                if not update:
                    if detail:
                        print(f'        {logging_code.WARNING}Found{logging_code.ENDC} {logging_code.WARNING}{file_name}{logging_code.ENDC} the folder {
                            logging_code.WARNING}{org}:{repo}{logging_code.ENDC}, skip to the next commit', end='\n')
                    return None
                else:
                    for saved_file in saved_files:
                        current_file_element = saved_file.split('_')
                        current_since = datetime.strptime(current_file_element[0], '%Y-%m-%dT%H:%M:%SZ')
                        current_until = datetime.strptime(current_file_element[2], '%Y-%m-%dT%H:%M:%SZ')

                        older = since < current_since
                        same_old = since == current_since
                        newer = until > current_until
                        same_new = until == current_until
                        if (older and newer) or (same_old and newer) or (older and same_new):
                            need_to_delete_old_file['delete'] = True
                            need_to_delete_old_file['file'] = saved_file
                            break
                            
                        else:
                            if detail:
                                print(f'        {logging_code.WARNING}Found{logging_code.ENDC} {logging_code.WARNING}{saved_file}{logging_code.ENDC} the folder {
                                    logging_code.WARNING}{org}:{repo}{logging_code.ENDC}, skip to the next commit', end='\n')
                            break

        res, request_left = request_api(commit_api, f'{org}:{repo}', headers, spare_api)
        if res is None or res == [] or len(res) == 0:
            # print(f'        {logging_code.CYAN}No commit{logging_code.ENDC} between {logging_code.WARNING}{since}{logging_code.ENDC} and {
            #       logging_code.WARNING}{until}{logging_code.ENDC} in the GitHub. Skip to the next dependency')
            break

        if not save_path.exists():
            save_path.mkdir(parents=True)
            if detail:
                print(f'        {logging_code.INFO}Create{logging_code.ENDC} folder at {
                    logging_code.WARNING}{save_path}{logging_code.ENDC}')
            saved_files = []

        with open(f'{save_path}/{file_name}', 'w+') as file:
            json.dump(res, file, indent=4)
            
        if need_to_delete_old_file['delete']:
            old_file = save_path.joinpath(need_to_delete_old_file['file'])
            old_file.unlink()
            if detail:
                print(f'        {logging_code.SUCCESS}Update{logging_code.ENDC} from {logging_code.WARNING}{need_to_delete_old_file["file"]}{logging_code.ENDC} to {logging_code.WARNING}{file_name}{
                    logging_code.ENDC} in the folder {logging_code.WARNING}{org}:{repo}{logging_code.ENDC}')
        else:
            if detail:
                print(f'        {logging_code.SUCCESS}Saved{logging_code.ENDC} {logging_code.WARNING}{file_name}{
                  logging_code.ENDC} in the folder {logging_code.WARNING}{save_path}{logging_code.ENDC}')


        if detail and level_of_logging > 0:
            print(f'        {logging_code.WARNING}Request left{logging_code.ENDC}: {request_left}')
        page += 1

    return request_left

def get_commit_description(
    org: str,
    repo: str,
    github_token: str,
    save_path: Path,
    commit_sha: str,
    update: bool = False,
    spare_api: Union[str, None] = None,
    detail: bool = False,
    level_of_logging: int = 0,
) -> None:
    downloaded_folder = save_path.joinpath(f'{org}:{repo}')
    downloaded_files = downloaded_folder.glob('*.json')
    downloaded_files = [file.name.rsplit('_', 1)[-1].rsplit('.', 1)[0] for file in downloaded_files]

    if commit_sha in downloaded_files:
        if not update:
            if detail:
                print(f'{logging_code.CYAN}Found{logging_code.ENDC} {logging_code.WARNING}{commit_sha}{logging_code.ENDC} the folder {logging_code.WARNING}{org}:{repo}{logging_code.ENDC}, skip to the next commit')
        return

    headers = {"Authorization": f"Bearer {github_token}"}

    commit_api = f'https://api.github.com/repos/{org}/{repo}/commits/{commit_sha}'
    
    if detail:
        print(f'    {logging_code.INFO}Getting{logging_code.ENDC} commit description from {logging_code.WARNING}{org}:{repo}{logging_code.ENDC}')

    res, request_left = request_api(commit_api, f'{org}:{repo}', headers, spare_api)
    if res is None:
        return request_left

    commit_date = res['commit']['committer']['date']

    save_path = save_path.joinpath(f'{org}:{repo}')
    if not save_path.exists():
        save_path.mkdir(parents=True)

    save_file_name = f'{commit_date}_{commit_sha}.json'
    with open(f'{save_path}/{save_file_name}', 'w+') as file:
        json.dump(res, file, indent=4)

    if detail:
        print(f'    {logging_code.SUCCESS}Saved{logging_code.ENDC} {logging_code.WARNING}{save_file_name}{logging_code.ENDC} in the folder {logging_code.WARNING}{org}:{repo}{logging_code.ENDC}')

    return request_left

def commit_description(
    org: str,
    repo: str,
    commits_history_path: Path,
    save_path: Path,
    github_token: str,
    # since: str,
    # until: str,
    update: bool = False,
    detail: bool = False,
    level_of_logging: int = 0,
) -> User_Input:
    commits_history_path = commits_history_path.joinpath(f'{org}:{repo}')
    commits_folders = commits_history_path.glob('*')

    for file in commits_folders:
        file_name = file.name
        since = datetime.strptime(file_name.split('_')[0], '%Y-%m-%dT%H:%M:%SZ')
        until = datetime.strptime(file_name.split('_')[2], '%Y-%m-%dT%H:%M:%SZ')
        with open(file, 'r') as f:
            commits = json.load(f)

        for commit in commits:
            commit_sha = commit['sha']
            
            if detail:
                print(f'    {logging_code.INFO}Getting{logging_code.ENDC} commits description from commits history of {logging_code.WARNING}{org}:{repo}{logging_code.ENDC}')

            request_left = get_commit_description(
                org=org,
                repo=repo,
                github_token=github_token,
                save_path=save_path,
                commit_sha=commit_sha,
                update=update,
                detail=detail,
                level_of_logging=level_of_logging,
            )

            if detail:
                print(f'    {logging_code.WARNING}Request left{logging_code.ENDC}: {request_left}')

        print(f'{logging_code.SUCCESS}Done{logging_code.ENDC} getting commits description history of {
            logging_code.WARNING}{org}:{repo}{logging_code.ENDC} between {logging_code.CYAN}{since}{logging_code.ENDC} and {logging_code.CYAN}{until}{logging_code.ENDC}\n')

    return

def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ") if date_str else None

def extract_usage_periods(
    project_name: str,
    installed: list[dict],
    removed: list[dict],
    moved: list[dict],
    updated: list[dict],
) -> list[dict]:
    """Extracts the usage period of dependencies, including removal, moves, and updates."""
    usage_periods = defaultdict(list)

    updated_dict = defaultdict(list)
    for upd in updated:
        updated_dict[upd["name"].lower()].append(upd)

    # Process removed dependencies
    for entry in removed:
        name = entry["name"].lower()
        removed_version = entry["version"]
        removed_date = parse_date(entry["removed_date"])
        installed_date = parse_date(entry["installed_date"]) if entry["installed_date"] else None
        
        # Try to find an update scenario where the removed version is an updated version of an installed version
        if installed_date is None and name in updated_dict:
            for upd in updated_dict[name]:
                if upd["new_version"] == removed_version:
                    installed_date = parse_date(upd["updated_date"])
                    break  # Take the first matching update scenario
        
        if installed_date is None:
            continue  # Skip if no valid installed date is found
        
        # Check if this removal is part of an update process (false positive removal case)
        false_positive = any(
            parse_date(upd["updated_date"]) == removed_date and
            upd["old_version"] == entry["version"] and
            upd["new_version"] == entry["version"]
            for upd in updated_dict[name]
        )
        if false_positive:
            continue

        usage_periods[name].append({
            "version": removed_version, 
            "installed": installed_date, 
            "removed": removed_date
        })

    # Merge overlapping periods with the same version
    for name, periods in usage_periods.items():
        periods.sort(key=lambda x: x["installed"])
        merged_periods = []
        for period in periods:
            if not merged_periods or merged_periods[-1]["removed"] < period["installed"] or merged_periods[-1]["version"] != period["version"]:
                merged_periods.append(period)
            else:
                merged_periods[-1]["removed"] = max(merged_periods[-1]["removed"], period["removed"])
        usage_periods[name] = merged_periods

    # Convert to dictionary format
    usage_periods_result = {}
    for name, periods in usage_periods.items():
        usage_periods_result[name] = [
            {
                "project_name": project_name,
                "version": period["version"],
                "installed_date": period["installed"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                "removed_date": period["removed"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                "usage_period": (period["removed"] - period["installed"]).days
            }
            for period in periods
        ]

    return usage_periods_result

def get_interval_of_usage_period(
    dependent_org_name: str,
    dependent_repo_name: str,
    moved_dependencies: dict,
    removed_dependencies: dict,
    installed_dependencies: dict,
    updated_dependencies: dict,
    dataset_path: Path,
    github_token: str,
    users_input: Union[set, list],
    update: bool = False,
    detail: bool = False,
    level_of_logging: int = 0,
) -> list[dict]:
    """
        This is the third function.
        Purpose: Get the list of commit within usage period that has been removed.
                 Download all commits and then select only .js filts.

        Result: No return value.
    """

    result = list()
    if type(users_input) == str:
        users_input = [users_input]

    elif type(users_input) == set:
        users_input = list(users_input)

    usage_periods = extract_usage_periods(
        project_name=f"{dependent_org_name}:{dependent_repo_name}",
        installed=installed_dependencies,
        removed=removed_dependencies,
        moved=moved_dependencies,
        updated=updated_dependencies
    )

    if detail and level_of_logging > 0:
        print(json.dumps(usage_periods, indent=4))

    if detail and level_of_logging > 1:
        print(f'Moved dependencies: {json.dumps(moved_dependencies, indent=4)}')
        print(f'Removed dependencies: {json.dumps(removed_dependencies, indent=4)}')
        print(f'Installed dependencies: {json.dumps(installed_dependencies, indent=4)}')
        print(f'Updated dependencies: {json.dumps(updated_dependencies, indent=4)}')

    for user_input in users_input:
        if user_input not in usage_periods:
            if detail:
                print(f"Skipping {user_input}, as no complete usage period found.")
            continue

        for usage_interval in usage_periods[user_input]:
            commits_history_path = dataset_path.joinpath("02_commits_since_install_until_remove")
            commits_description_history_path = dataset_path.joinpath("03_commits_description_since_install_until_remove")


            get_commit_history(
                org=dependent_org_name,
                repo=dependent_repo_name,
                github_token=github_token,
                save_path=commits_history_path,
                since=usage_interval['installed_date'],
                until=usage_interval['removed_date'] if 'removed_date' in usage_interval else usage_interval['moved_date'],
                update=update,
                detail=detail,
                level_of_logging=level_of_logging
            )

            commit_description(
                org=dependent_org_name,
                repo=dependent_repo_name,
                commits_history_path=commits_history_path,
                save_path=commits_description_history_path,
                github_token=github_token,
                update=update,
                detail=detail,
                level_of_logging=level_of_logging
            )

            res = {
                f'{dependent_org_name}:{dependent_repo_name}': {
                    'user_input': user_input,
                    'usage_interval_scenarios': usage_interval,
                }
            }

            result.append(res)

    return result
