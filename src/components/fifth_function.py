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
    results: list[dict],
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

    for result in results:
        dependency_name = result['dependency_name']
        removed_version = result['version']
        
        scenario = result['scenarios']
        if len(scenario) == 0:
            continue
        for group, each_scenario in scenario.items():

            current_dependency_save_path = current_save_path.joinpath(f'{dependency_name}/version_{removed_version}')
            if not current_dependency_save_path.exists():
                current_dependency_save_path.mkdir(parents=True)
            with open(f'{current_dependency_save_path}/{group}.json', 'w') as file:
                json.dump(each_scenario, file, indent=4)

            readable_group = ''
            if group == 'removal_affected_code':
                readable_group = 'Dependency Removals with Direct Code Impact'
            elif group == 'removal_not_affected_code':
                readable_group = 'Dependency Removals without Direct Code Impact'
            elif group == 'unknown':
                readable_group = 'Unknown'

            each_scenario_sha = [each_scenario_['commit_sha'] for each_scenario_ in each_scenario]
            each_scenario_sha = list(set(each_scenario_sha))

            if len(each_scenario) > 0:
                if dependency_name not in reports.keys():
                    reports[dependency_name] = {
                        removed_version: {
                            'all_removed': len(each_scenario),
                            'scenarios': {
                                readable_group: len(each_scenario)
                            }
                        }
                    }
                else:
                    if removed_version not in reports[dependency_name].keys():
                        reports[dependency_name][removed_version] = {
                            'all_removed': len(each_scenario),
                            'scenarios': {
                                readable_group: len(each_scenario)
                            }
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

        for dependency_name_in_report, report in reports.items():
            report_full.append(dependency_name_in_report)
            for version, report_description in report.items():
                report_full.append(f'  - Version {version}: Found {report_description['all_removed']} removed scenarios.')
                for group, amount in report_description['scenarios'].items():
                    report_full.append(f'    - {group}: found {amount} times.')
                report_full.append('')
            report_full.append('#' * 50)

        report_full.append('')
        report_full.append(f'The full report and classified commits are saved at')
        report_full.append('{}{}{}'.format(logging_code.INFO, current_save_path, logging_code.ENDC))
        report_full.append('')
        report_string = '\n'.join(report_full)
        file.write(report_string)

    print()
    print(report_string)

    print()
    print('If you want to continue the analysis with other dependency, please enter the dependency name.')
    print('If you prefer to stop the analysis, please enter \"end\" or \"ctrl + c\".')
    print()

    first_res = []
    for dependency in removed_dependencies:
        if dependency['name'] not in first_res:
            first_res.append(dependency['name'])

    first_res = sorted(first_res)
    dependency_completer = WordCompleter(first_res, ignore_case=True, sentence=True)

    for index, dependency in enumerate(first_res, 1):
        status = ' << {}Analyzed{}'.format(logging_code.SUCCESS, logging_code.ENDC) if dependency in previous_dependency else ''
        print('  {}. \"{}{}{}\"{}'.format(
            index,
            logging_code.WARNING,
            dependency,
            logging_code.ENDC,
            status
        ))

    while True:
        try:
            print('Please enter the dependency name: ')
            user_input = prompt('> ', completer=dependency_completer)

            if user_input == 'end':
                return False, None
            try:
                user_input = int(user_input)
                if user_input > 0 and user_input <= len(first_res):
                    break
                else:
                    print('The index that you entered is not in the list of dependencies.')
                    print('Please enter the correct index.')
                    print('Please enter a number between 1 and {}.'.format(len(first_res)))
            except ValueError:
                if user_input in first_res:
                    break
                else:
                    print('The dependency that you entered is not in the list of dependencies.')
                    print('Please enter the correct dependency.')
        except KeyboardInterrupt:
            return False, None
        
    target_dependency = first_res[user_input - 1]
    print('You have selected \"{}{}{}\"'.format(
        logging_code.WARNING,
        target_dependency,
        logging_code.ENDC
    ))

    return True, target_dependency