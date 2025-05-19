import json

from pathlib import Path
from typing import Union

from time import time
from datetime import datetime
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from .logging_code import logging_code


def result_and_another_input(
    proj_org: str,
    proj_repo: str,
    dataset_path: Path,
    result_path: Path,
    results: list[dict],
    moved_dependencies: list[dict],
    removed_dependencies: list[dict],
    previous_input: list[dict[str]],
) -> tuple[bool, Union[list[str], None]]:
    """
        This is the fifth function.
        Purpose: Report the result of classification to users.
                 Show the path to the dataset folder.
                 If users want to continue the analysis with other dependency
                 they can choose the dependency name and then the analysis will be continued.
                 The dependency name are provided from 2nd fucntion.
    """

    # * Save procedure
    save_path = dataset_path.joinpath('06_results_of_classification')
    number_of_saved_folders = list(save_path.glob('*'))
    amount_of_each_project = {}
    for folder in number_of_saved_folders:
        if proj_org in folder.stem and proj_repo in folder.stem:
            if f'{proj_org}:{proj_repo}' not in amount_of_each_project:
                amount_of_each_project[f'{proj_org}:{proj_repo}'] = 1
            else:
                amount_of_each_project[f'{proj_org}:{proj_repo}'] += 1

    current_time = time()
    current_date = datetime.fromtimestamp(current_time).strftime('%Y-%m-%dT%H:%M:%SZ')

    reports = dict()
    number_of_saved_dependency_folders = 0
    for each_folder_name in amount_of_each_project.keys():
        number_of_saved_dependency_folders = amount_of_each_project[f'{each_folder_name}']
        
    folder_name = f'{proj_org}:{proj_repo}_{number_of_saved_dependency_folders + 1}_{current_date}'

    current_save_path = save_path.joinpath(f'{folder_name}')
    if not current_save_path.exists():
        current_save_path.mkdir(parents=True)

    # print(json.dumps(results, indent=4))

    for result in results:
        all_scenarios = 0
        dependency_name = result['dependency_name']
        removed_version = result['version']
        # print(json.dumps(result, indent=4))

        # filtered_scenarios = []
        # for scenario in result['move_dep_to_other_fields']:
        #     if 'name' in scenario.keys():
        #         if scenario['name'] != dependency_name:
        #             continue
        #         else:
        #             filtered_scenarios.append(scenario)

        # result['scenarios']['move_dep_to_other_fields'] = filtered_scenarios

        # for scenario in result['scenarios']:
        scenario = result['scenarios']
        if len(scenario) == 0:
            continue
        for group, each_scenario in scenario.items():
            all_scenarios += len(each_scenario)

            current_dependency_save_path = current_save_path.joinpath(f'{dependency_name}/version_{removed_version}')
            # print(current_dependency_save_path)
            if not current_dependency_save_path.exists():
                current_dependency_save_path.mkdir(parents=True)
            if each_scenario == [] or len(each_scenario) == 0:
                continue

            readable_group = ''
            if group == 'removal_affected_code':
                readable_group = 'Dependency Removals with Direct Code Impact'
            elif group == 'removal_not_affected_code':
                readable_group = 'Dependency Removals without Direct Code Impact'
            elif group == 'not_related':
                readable_group = 'Not related to dependency removal'
            # if group == 'move_dep_to_other_fields':
            #     readable_group = 'Move dependency to other fields'
            # elif group == 'shrink_library':
            #     readable_group = 'Shrink library'
            # elif group == 'remove_bloat_dependency':
            #     readable_group = 'Remove bloat dependency'
            # elif group == 'replace_dep_with_builtins':
            #     readable_group = 'Replace dependency with built-ins or custom functions'
            # elif group == 'replace_dep_with_another_dep':
            #     readable_group = 'Replace dependency with another dependency'
            elif group == 'unknown':
                readable_group = 'Unknown'
            with open(f'{current_dependency_save_path}/{readable_group}.json', 'w') as file:
                json.dump(each_scenario, file, indent=4)

            each_scenario_sha = [each_scenario_['commit_sha'] for each_scenario_ in each_scenario]
            each_scenario_sha = list(set(each_scenario_sha))

            print(readable_group)

            if len(each_scenario) > 0:
                if dependency_name not in reports.keys():
                    reports[dependency_name] = {
                        removed_version: {
                            'all_removed': len(each_scenario),
                            'scenarios': {
                                readable_group: len(each_scenario)
                            },
                            'commit_sha': each_scenario_sha
                        }
                    }
                else:
                    if removed_version not in reports[dependency_name].keys():
                        reports[dependency_name][removed_version] = {
                            'all_removed': len(each_scenario),
                            'scenarios': {
                                readable_group: len(each_scenario)
                            },
                            'commit_sha': each_scenario_sha
                        }
                    else:
                        reports[dependency_name][removed_version]['all_removed'] += len(each_scenario)
                        if readable_group not in reports[dependency_name][removed_version]['scenarios'].keys():
                            reports[dependency_name][removed_version]['scenarios'][readable_group] = len(each_scenario)
                        else:
                            reports[dependency_name][removed_version]['scenarios'][readable_group] += len(each_scenario)

    previous_dependency = [previous_input] if isinstance(previous_input, str) else previous_input

    with open(f'{current_save_path}/report.txt', 'w') as file:
        report_full = []
        report_full.append('Results of the analysis')

        print(json.dumps(reports, indent=4))
        for dependency_name_in_report, report in reports.items():
            report_full.append(dependency_name_in_report)
            for version, report_description in report.items():
                report_full.append(f'  - Version {version}: Found {report_description['all_removed']} removed scenarios.')
                for group, amount in report_description['scenarios'].items():
                    report_full.append(f'    - {group}: found {amount} times. {report_description['commit_sha']}')
                report_full.append('')
            # report_full.append('#' * 50)

        report_full.append('')
        report_full.append(f'The full report and classified commits are saved at')
        report_full.append('{}{}{}'.format(logging_code.INFO, current_save_path, logging_code.ENDC))
        report_full.append('')
        report_string = '\n'.join(report_full)
        file.write(report_string)

    # print(json.dumps(report_string, indent=4))

    # print('-' * 50)
    print()
    print(report_string)

    print()
    print('If you want to continue the analysis with other dependency, please enter the dependency name.')
    print('If you prefer to stop the analysis, please enter \"end\" or \"ctrl + c\".')
    print()

    # ! For testing will skip the input receive part
    # first_res = []
    # for group in [moved_dependencies, removed_dependencies]:
    #     for dependency in group:
    #         if dependency['name'] not in first_res:
    #             first_res.append(dependency['name'])

    # first_res = sorted(first_res)
    # dependency_completer = WordCompleter(first_res, ignore_case=True, sentence=True)

    # for index, dependency in enumerate(first_res, 1):
    #     status = ' << {}Analyzed{}'.format(logging_code.SUCCESS, logging_code.ENDC) if dependency in previous_dependency else ''
    #     print('  {}. \"{}{}{}\"{}'.format(
    #         index,
    #         logging_code.WARNING,
    #         dependency,
    #         logging_code.ENDC,
    #         status
    #     ))

    # try:
    #     print('Please enter the dependency name: ')
    #     users_input = prompt('> ', completer=dependency_completer)
    # except KeyboardInterrupt:
    #     return False, None

    # users_input = users_input.strip().split(',')
    # users_input = set(users_input)
    # first_res = set(first_res)

    # overlap = users_input & first_res

    # while not overlap:
    #     if 'end' in users_input:
    #         return False, None
    #     if 'all' in users_input:
    #         return True, first_res
    #     print('The dependency that you entered is not in the list of dependencies.')
    #     print('Please enter the correct dependency.')
    #     try:
    #         print()
    #         print('Please enter the dependency name: ')
    #         users_input = prompt('> ', completer=dependency_completer)
    #         # print(first_res)
    #     except KeyboardInterrupt:
    #         return False, None

    # return True, users_input

    # ! If not testing, please remove this line to enable the input receive part
    return False, None