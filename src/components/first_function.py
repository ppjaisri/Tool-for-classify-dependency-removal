import json

from typing import Union
from pathlib import Path
from datetime import datetime

from .logging_code import logging_code
from .requests_git_api import request_api, detect_json_and_clean_and_fix_json
from .detect_moving_dep_to_other_fields import detect_moving_dependency_to_other_fields


def get_package_json_history(
        org: str,
        repo: str,
        github_token: str,
        save_path: Path,
        update: bool = False,
        spare_api: Union[str, None] = None,
        detail: bool = False
) -> Union[bool, int]:
    saved_files = save_path.glob('*.json')
    saved_files = [str(file) for file in saved_files]

    headers = {"Authorization": f"Bearer {github_token}"}

    page = 1
    no_download = True
    api_not_working: bool = False
    first_attemp = True
    while True:
        api = f'https://api.github.com/repos/{org}/{repo}/commits?path=package.json&per_page=100&page={page}'

        res, request_left = request_api(api, f'{org}:{repo}', headers, spare_api)
        if res is None or res == []:
            if first_attemp:
                print()
                print('{}Error{}, The repository {}:{} does not have package.json in the root of the repository.'.format(logging_code.ERROR, logging_code.ENDC, org, repo))
                api_not_working = True
                break
        if len(res) == 0:
            break

        for commit in res:
            try:
                commit_date = commit['commit']['committer']['date']
                # commit_date = datetime.strptime(commit_date, '%Y-%m-%dT%H:%M:%SZ')
                # commit_date = commit_date.strftime('%Y-%m-%d')
            except:
                try:
                    print('Cannot get date from commit[\'commit\'][\'committer\']')
                    print(json.dumps(commit['commit']['committer']))
                except:
                    try:
                        print('Cannot get committer from commit[\'commit\']')
                        print(json.dumps(commit['commit']))
                    except:
                        print('Cannot get commit from commit')
                        print(json.dumps(commit))
                        # raise Exception('Error at date')
            try:
                commit_sha = commit['sha']
            except:
                print('Cannot get sha from commit')
                print(json.dumps(commit))
                continue
                # raise Exception('Error at sha')
                
            if not save_path.exists():
                save_path.mkdir(parents=True)
            save_file_name = f'{save_path}/{commit_date}_{commit_sha}.json'

            # print(save_file_name)
            if save_file_name in saved_files and not update:
                if detail:
                    print(f'    {logging_code.WARNING}Found{logging_code.ENDC} {logging_code.WARNING}{save_file_name}{logging_code.ENDC} the folder {
                        logging_code.WARNING}{org}:{repo}{logging_code.ENDC}, skip to the next commit')
                continue

            description_api = f'https://api.github.com/repos/{
                org}/{repo}/contents/package.json?ref={commit_sha}'

            description_res, request_left = request_api(description_api, f'{org}:{
                                          repo}', headers, spare_api)
            if description_res is None:
                break

            if 'download_url' not in description_res.keys():
                # print(json.dumps(description_res, indent=4))
                continue
            content_api = description_res['download_url']

            content_res, request_left = request_api(content_api, f'{org}:{
                                      repo}', headers, spare_api)
            if content_res is None:
                break

            content_res, is_broken_json = detect_json_and_clean_and_fix_json(content_res, api)

            if not is_broken_json:
                with open(save_file_name, 'w') as file:
                    file.write(json.dumps(content_res, indent=4))

            no_download = False

        # print(f'        {logging_code.WARNING}Request left{logging_code.ENDC}: {request_left}')
        page += 1
        first_attemp = False

    if no_download and detail:
        print(f'        {logging_code.WARNING}Already download{logging_code.ENDC} all version of package.json of {
              logging_code.WARNING}{org}:{repo}{logging_code.ENDC}, skip to the next dependent')
        
    if api_not_working:
        return None

    return request_left


def history_of_package_json(
    org: str,
    repo: str,
    dataset_path: Path,
    github_token: str,
    update: bool = False,
    detail: bool = False,
    level_of_logging: int = 0,
) -> tuple[dict, dict, dict, dict]:
    """
        This is the first function.
        Purpose: Get history of package.json project.
                 Sort the version of package.json.
                 Extract the dependency which is moved to other fields.

        Result: Return the list of dependency which is moved to other
                fields and the rest that is not moved.
            - Dependencies which are moved to other fields.
            - Dependencies which are not moved to other fields.
                - Dependencies which are removed.
                - Dependencies which are installed.
                - Dependencies which are updated.
    """

    package_json_history_path = dataset_path.joinpath(f'01_package_json_history/{org}:{repo}')

    need_to_download: bool = False
    if not package_json_history_path.exists():
        need_to_download = True

    if update or need_to_download:
        if detail:
            print(f'    {logging_code.INFO}Getting{logging_code.ENDC} history of package.json of {
                logging_code.WARNING}{org}{repo}{logging_code.ENDC}')
        result = get_package_json_history(
            org=org,
            repo=repo,
            github_token=github_token,
            save_path=package_json_history_path,
            update=update,
            detail=detail
        )

        if result is None:
            return None, None, None, None

        print(f'    {logging_code.WARNING}Request left{logging_code.ENDC}: {result}')
        print(f'{logging_code.SUCCESS}Done{logging_code.ENDC} getting history of package.json of {
            logging_code.WARNING}{org}:{repo}{logging_code.ENDC}\n')
    
    try:
        res = detect_moving_dependency_to_other_fields(package_json_history_path)
    except Exception as e:
        print(f'{logging_code.ERROR}Error{logging_code.ENDC} when getting history of package.json of {org}:{repo}')
        print(f'{logging_code.ERROR}Error{logging_code.ENDC}: {e}')
        return None, None, None, None

    if level_of_logging > 1:
        print(json.dumps(res, indent=4))
    
    return res['moved'], res['removed'], res['installed'], res['updated']