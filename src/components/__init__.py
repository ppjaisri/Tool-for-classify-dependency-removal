from .detect_moving_dep_to_other_fields import detect_moving_dependency_to_other_fields
# from .detect_chage_of_dependency_field import load_package_json, detect_patch_changes, display_patch_changes

# Classification
from .element_classification import classify_commit_message, classify_python_code, classify_python_code_with_grouping
from .compare_code_change_by_ast import compare_replaced_code_with_dependency

# logging
from .logging_code import logging_code

# API
from .requests_git_api import request_api, detect_json_and_clean_and_fix_json
from .first_function import history_of_package_json
from .second_function import ask_user_to_choose_dependency
from .third_function import get_interval_of_usage_period
from .forth_function import removal_scenario_classification

# Code clone detection
from .code_clone_detector import CodeCloneDetector

__all__ = [
    'detect_moving_dependency_to_other_fields',
    'classify_commit_message',
    'classify_python_code',
    'classify_python_code_with_grouping',
    'compare_replaced_code_with_dependency',
    'logging_code',
    'request_api',
    'detect_json_and_clean_and_fix_json',
    'history_of_package_json',
    'ask_user_to_choose_dependency',
    'get_interval_of_usage_period',
    'removal_scenario_classification',
    'CodeCloneDetector',
]