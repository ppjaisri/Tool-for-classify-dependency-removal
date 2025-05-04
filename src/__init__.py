# Functional files
from .components import detect_change_of_dependency_field, detect_moving_dep_to_other_fields

# Classification
from .components.element_classification import classify_commit_message, classify_python_code, classify_python_code_with_grouping
# from .components.compare_code_change_by_ast import compare_replaced_code_with_dependency

# Interface files
from .interfaces import result

# logging
from .components.logging_code import logging_code

# API
from .components.requests_git_api import request_api, detect_json_and_clean_and_fix_json
from .components.first_function import history_of_package_json
from .components.second_function import ask_user_to_choose_dependency
from .components.third_function import get_interval_of_usage_period
from .components.forth_function import removal_scenario_classification

# Code clone detection
# from .components.code_clone_detector import CodeCloneDetector

__version__ = '0.5.0'
__all__ = [
    'detect_change_of_dependency_field',
    'detect_moving_dep_to_other_fields',
    'classify_commit_message',
    'classify_python_code',
    'classify_python_code_with_grouping',
    # 'compare_replaced_code_with_dependency',
    'result',
    'logging_code',
    'request_api',
    'detect_json_and_clean_and_fix_json',
    'history_of_package_json',
    'ask_user_to_choose_dependency',
    'get_interval_of_usage_period',
    'removal_scenario_classification',
    # 'CodeCloneDetector',
]
