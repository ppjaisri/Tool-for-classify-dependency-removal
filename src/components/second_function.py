from typing import Union
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import print_formatted_text

from .logging_code import logging_code


def ask_user_to_choose_dependency(
    moved_dependencies: list[dict],
    removed_dependencies: list[dict],
) -> Union[set, bool]:
    print('These are name of dependencies which {}have been removed{} from list of dependencies.'.format(
        logging_code.INFO, logging_code.ENDC
    ))

    first_res = []
    for group in [moved_dependencies, removed_dependencies]:
        for dependency in group:
            if dependency['name'] not in first_res:
                first_res.append(dependency['name'])

    first_res = sorted(first_res)

    for index, dependency in enumerate(first_res, 1):
        print('  {}. \"{}{}{}\"'.format(
            index,
            logging_code.WARNING,
            dependency,
            logging_code.ENDC
        ))

    print('Which dependency that you {}prefer to analyze{}'.format(
        logging_code.INFO, logging_code.ENDC
    ))

    print('Please enter the name of dependency that you want to analyze.')
    # print('Enter multiple dependencies by separating them with a comma.')
    # print('If you prefer to analyze all dependencies, please enter \"all\".')
    print()
    print('Latest update is 24-01-2025')

    dependency_completer = WordCompleter(first_res, ignore_case=True, sentence=True)
    try:
        formatted_text = ANSI('{}Please enter prefer dependency{}: '.format(
            logging_code.CYAN, logging_code.ENDC
        ))
        print_formatted_text(formatted_text)
        users_input = prompt('> ', completer=dependency_completer)
    except KeyboardInterrupt:
        return False
    print()

    if users_input == 'end':
        return False

    users_input = users_input.strip().split(',')
    users_input = set(users_input)
    first_res = set(first_res)

    overlap = users_input & first_res

    while not overlap:
        if 'all' in users_input:
            break
        elif'end' in users_input:
            return False
        print('The dependency that you entered is not in the list of dependencies.')
        print('Please enter the correct dependency.')
        print(first_res)
        try:
            print('Please enter prefer dependency:')
            users_input = prompt('> ', completer=dependency_completer)
            users_input = set(users_input.strip().split(','))

            overlap = users_input & first_res
            # print(first_res)
        except KeyboardInterrupt:
            return False

    if users_input == {'all'}:
        return first_res

    return users_input
