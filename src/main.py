#/usr/bin/env python3.12
import json
import argparse

from urllib.parse import urlparse
from pathlib import Path

from src.components.logging_code import logging_code
from src.components.first_function import history_of_package_json
from src.components.second_function import ask_user_to_choose_dependency
from src.components.third_function import get_interval_of_usage_period
from src.components.forth_function import removal_scenario_classification
from src.components.fifth_function import result_and_another_input


def analyze_project(
    link_to_project_repository: str,
    update: bool = False,
    detail: bool = False,
    level_of_logging: int = 0,
    config_file: str = None,
) -> None:
    if config_file:
        try:
            config_file_path = Path(config_file)
        except Exception as e:
            print('{}The config file is not found at {}{}.'.format(logging_code.ERROR, logging_code.ENDC, config_file))
            exit(-1)

        with open(config_file_path, 'r') as file:
            try:
                config = json.load(file)    
            except Exception as e:
                print('{}The config file is not in JSON format.{}'.format(logging_code.ERROR, logging_code.ENDC))
                exit(-1)

    github_token = config['github_token'] if 'github_token' in config.keys() else None

    if 'dataset_path' in config.keys():
        root_dataset_path = config['dataset_path']
    else:
        # Prepare the application
        current_path = Path.cwd()

        if 'src' not in str(current_path):
            root_dataset_path = current_path.parent.joinpath('dataset')
            keywords_path = current_path.joinpath('patterns_and_keywords')
        else:
            root_dataset_path = current_path.parent.parent.joinpath('dataset')
            keywords_path = current_path.parent.joinpath('patterns_and_keywords')

    parsed_url = urlparse(link_to_project_repository)

    if '/repos' in parsed_url.path:
        org, repo = parsed_url.path.split('/')[2:4]
    else:
        org, repo = parsed_url.path.split('/')[1:3]

    # 1st function
    # Get history of package.json project.
    # Sort the version of package.json.
    # Extract the dependency which is moved to other fields.
    # Return the list of dependency which is moved to other fields
    # and the rest that is not moved

    print('{}Retrieve the information from the project repository{}: {}'.format(
        logging_code.INFO, logging_code.ENDC, link_to_project_repository
    ))

    moved, removed, installed, updated = history_of_package_json(
        org=org,
        repo=repo,
        dataset_path=root_dataset_path,
        github_token=github_token,
        update=update,
        detail=detail,
        level_of_logging=level_of_logging
    )

    if not moved and not removed:
        if not updated:
            print('{}The link is unusable.{} Please check the link and try again.'.format(
                logging_code.ERROR, logging_code.ENDC
            ))
            exit(0)

        else:
            print('{}The project has no dependency removal.{}'.format(
                logging_code.SUCCESS, logging_code.ENDC
            ))
            exit(0)

    # 2nd function
    # Show the list of dependency that has been removed to users.
    # Users can choose the dependency that they want to analyse.
    # Retuen the list of dependency that has been removed.

    users_input = ask_user_to_choose_dependency(
        moved_dependencies=moved,
        removed_dependencies=removed,
    )

    if not users_input:
        exit(0)

    # 3rd function
    # Get the list of commit within usage period that has been removed.
    # Download all commits and then select only .js filts.

    # Users will assign the value into Continue_analyze after the analysis is finished.
    # If users want to continue the analysis with other dependency, the value will be True.
    # If users want to stop the analysis, the value will be False.
    # The initial value is True for start the loop.
    continue_analyze = True

    while continue_analyze:
        # ! Now support only a single dependency query.
        res = get_interval_of_usage_period(
            dependent_org_name=org,
            dependent_repo_name=repo,
            moved_dependencies=moved,
            removed_dependencies=removed,
            installed_dependencies=installed,
            updated_dependencies=updated,
            dataset_path=root_dataset_path,
            github_token=github_token,
            users_input=users_input,
            update=update,
            detail=detail,
            level_of_logging=level_of_logging
        )

        # 4th funciton
        # Classify the dependency removal scenarios.
        # After classify each commit, the commit will be saved in each dataset folder.

        classified_scenarios = []
        for dependency in res:
            dependency_res = removal_scenario_classification(
                # dependent_org_name=org,
                # dependent_repo_name=repo,
                dependency_removal_scenarios=dependency,
                dataset_path=root_dataset_path,
                keywords_path=keywords_path,
                github_token=github_token,
                update=update,
                detail=detail,
                level_of_logging=level_of_logging
            )

            filtered_moved = [scenario for scenario in moved if scenario['name'] == dependency_res['dependency_name']]

            dependency_res['move_dep_to_other_fields'].extend(
                filtered_moved)
            classified_scenarios.append(dependency_res)

        # 5th function (last function)
        # Report the result of classification to users.
        # Show the path to the dataset folder.
        # If users want to continue the analysis with other dependency
        # they can choose the dependency name and then the analysis will be continued.
        # The dependency name are provided from 2nd fucntion.

        continue_analyze, users_input = result_and_another_input(
            proj_org=org,
            proj_repo=repo,
            dataset_path=root_dataset_path,
            result_path=root_dataset_path,
            results=classified_scenarios,
            moved_dependencies=moved,
            removed_dependencies=removed,
            previous_input=users_input
        )

    exit(0)

def main() -> None:
    # Parse the arguments
    parser = argparse.ArgumentParser(
        description='''
        An CLI application for classifying dependency removal scenarios.
        Current version only supports the JavScript project.
        '''
    )

    # Main argument
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--analyze', '-a',
        action='store_true',
        help='Analyze the project.'
    )

    parser.add_argument(
        'link_to_project_repository',
        type=str,
        help='The link to the project repository to analyze.'
    )

    # Argument for update
    parser.add_argument(
        '--update', '-u',
        action='store_true',
        help='Update the dataset.'
    )

    # Argument for detail and level of logging
    parser.add_argument(
        '--detail', '-d',
        type=int,
        choices=[0, 1, 2],
        help='Debug mode and set level of logging.'
    )

    # Argument for config file
    parser.add_argument(
        '--config', '-c',
        nargs='?',
        type=str,
        help='The path to the config file.'
    )

    args = parser.parse_args()

    if args.analyze:
        analyze_project(
            args.link_to_project_repository,
            update=True if args.update else False,
            detail=True if args.detail else False,
            level_of_logging=args.detail if args.detail else 0,
            config_file=args.config
        )


if __name__ == '__main__':
    main()
