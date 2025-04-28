from typing import Union
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import print_formatted_text

from .logging_code import logging_code


def ask_user_to_choose_dependency(
    removed_dependencies: list[dict],
) -> Union[set, bool]:
    print('These are name of dependencies which {}have been removed{} from list of dependencies.'.format(
        logging_code.INFO, logging_code.ENDC
    ))

    first_res = []
    for dependency in removed_dependencies:
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

    print('Please enter the name or index of dependency that you want to analyze.')
    print()
    print('Latest update is 24-01-2025')

    dependency_completer = WordCompleter(first_res, ignore_case=True, sentence=True)
    while True:
        try:
            formatted_text = ANSI('{}Please enter prefer dependency name or index{}: '.format(
                logging_code.CYAN, logging_code.ENDC
            ))
            print_formatted_text(formatted_text)
            user_input = prompt('> ', completer=dependency_completer)

            if user_input == 'end':
                return False
            
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
            return False
    print()

    if type(user_input) == int:
        target_dependency = first_res[user_input - 1]
    else:
        target_dependency = user_input
    print('You have selected \"{}{}{}\"'.format(
        logging_code.WARNING,
        target_dependency,
        logging_code.ENDC
    ))

    return target_dependency
