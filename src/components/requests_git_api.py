import re
import json
import requests

from typing import Union, Any
from time import time, sleep
from datetime import timedelta, datetime

from .logging_code import logging_code


def detect_json_and_clean_and_fix_json(
    broken_json: Union[str, dict]
) -> tuple[Union[dict, None], Union[bool, None]]:
    
    # Check if input is already a dictionary
    if isinstance(broken_json, dict):
        for key, value in broken_json.items():
            if isinstance(value, str):
                broken_json[key] = re.sub(r'//.*?(\n|$)', '', value)
            elif isinstance(value, dict):
                detect_json_and_clean_and_fix_json(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        detect_json_and_clean_and_fix_json(item)
        return broken_json, None

    # First check if the string is valid JSON
    try:
        return json.loads(broken_json)
    except json.JSONDecodeError:
        # If not valid JSON, try to fix it
        # Check if string looks like JSON (starts with { or [ and ends with } or ])
        if not (broken_json.strip().startswith('{') or broken_json.strip().startswith('[')) or \
           not (broken_json.strip().endswith('}') or broken_json.strip().endswith(']')):
            # print('Input string does not appear to be JSON')
            return broken_json, False

        # Remove trailing commas
        broken_json = re.sub(r',\s*([\]}])', r'\1', broken_json)

        # Remove any leading unexpected characters before the JSON starts
        broken_json = re.sub(r'^[^\{]*', '', broken_json)

        # Remove any trailing unexpected characters after the JSON ends
        broken_json = re.sub(r'[^\}]*$', '', broken_json)

        # Remove comments
        broken_json = re.sub(r'//.*?(\n|$)', '\n', broken_json)  # Single-line comments
        broken_json = re.sub(r'/\*.*?\*/', '', broken_json, flags=re.DOTALL)  # Multi-line comments

        # Attempt to add missing commas
        broken_json = re.sub(r'([}\]"\'\w])\s*([\[{])', r'\1,\2', broken_json)

        # Ensure keys are quoted
        broken_json = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', broken_json)

        # Final attempt to parse the JSON
        try:
            return json.loads(broken_json), True
        except json.JSONDecodeError as e:
            print(f'Failed to parse JSON: {e}')
            return None, None

def log_error_limit_reached(
    package_name: str,
    api: str, status_code: int,
    wait_time: timedelta
) -> None:
    print(f'{logging_code.ERROR}ERROR{logging_code.ENDC}, with {logging_code.WARNING}{status_code}{logging_code.ENDC} when getting {
          logging_code.WARNING}{package_name}{logging_code.ENDC} from {logging_code.WARNING}{api}{logging_code.ENDC}')
    while wait_time > 0:
        if wait_time != 1:
            print(f"out of x-ratelimit: wait {logging_code.WARNING}%02d:%02d:%02d{logging_code.ENDC} to get the data again\r" %
                  (wait_time // 3600, wait_time // 60, wait_time % 60), end="")
            wait_time -= 1
            sleep(1)

        else:
            print(f"out of x-ratelimit: wait {logging_code.WARNING}%02d:%02d:%02d{logging_code.ENDC} to get the data again\n" %
                  (wait_time // 3600, wait_time // 60, wait_time % 60))
            sleep(3)


def request_api(
    api: str,
    package_name: str,  # * For logging purpose
    headers: Union[dict, None] = None,
    spare_api: Union[str, None] = None,
    debug: bool = False,
) -> tuple[Union[dict[str, str], bool], int]:
    session = requests.Session()
    session.headers.update(headers)

    try:
        res = session.get(api)
    except requests.exceptions.RequestException as e:
        session.close()
        session = requests.Session()
        session.headers.update(headers)

        res = session.get(api)

    if 'x-ratelimit-remaining' in res.headers.keys():
        requests_left = res.headers['x-ratelimit-remaining']
    else:
        requests_left = None

    time_stamp = datetime.fromtimestamp(time())
    if 'x-ratelimit-reset' in res.headers.keys():
        reset_time = datetime.fromtimestamp(
            int(res.headers['x-ratelimit-reset']))

    else:
        rate_limit = session.get('https://api.github.com/rate_limit')
        rate_limit = rate_limit.json()
        reset_time = rate_limit['rate']['reset']
        reset_time = datetime.fromtimestamp(reset_time)

        if requests_left is None:
            requests_left = rate_limit['rate']['remaining']
    
    duration = reset_time - time_stamp

    match res.status_code:
        case 401:
            print(f'{logging_code.ERROR}ERROR{
                  logging_code.ENDC}, Unauthorized. Please check your GitHub token.')
            return None, requests_left

        case 404:
            print(f'{logging_code.ERROR}ERROR{logging_code.ENDC}, not found when getting {logging_code.WARNING}{
                  package_name}{logging_code.ENDC} from {logging_code.WARNING}{api}{logging_code.ENDC}')
            if spare_api is not None:
                print(f'{logging_code.WARNING}Try{logging_code.ENDC} with {logging_code.WARNING}{spare_api}{logging_code.ENDC}')
            else:
                print(f'{logging_code.ERROR}No spare api{logging_code.ENDC} for {
                      logging_code.WARNING}{package_name}{logging_code.ENDC}')
                return None, requests_left

            try:
                res = session.get(api)
            except requests.exceptions.RequestException as e:
                session.close()
                session = requests.Session()
                session.headers.update(headers)

                res = session.get(api)

            match res.status_code:
                case 403 | 429:
                    max_retries = 3
                    for try_count in range(max_retries):
                        wait_time = duration.total_seconds()
                        log_error_limit_reached(
                            package_name, api, res.status_code, wait_time)

                        try:
                            res = session.get(api)
                            res = res.json()
                            return res, requests_left
                        except requests.exceptions.RequestException as e:
                            print(f'{logging_code.ERROR}ERROR{logging_code.ENDC}, with {
                                  logging_code.WARNING}{e}{logging_code.ENDC}')
                            return None, requests_left
                case _:
                    if res.status_code != 200:
                        print(f'{logging_code.ERROR}ERROR{logging_code.ENDC}, with {logging_code.WARNING}{res.status_code}{
                              logging_code.ENDC} when getting {logging_code.WARNING}{package_name}{logging_code.ENDC} from {logging_code.WARNING}{api}{logging_code.ENDC}')
                        return None, requests_left

                    res = res.json()
                    print(f'{logging_code.SUCCESS}Success{logging_code.ENDC}, with {logging_code.WARNING}{res.status_code}{
                          logging_code.ENDC} when getting {logging_code.WARNING}{package_name}{logging_code.ENDC} from {logging_code.WARNING}{api}{logging_code.ENDC}')
                    return res, requests_left

        case 403 | 429:
            wait_time = duration.total_seconds()
            log_error_limit_reached(
                package_name, api, res.status_code, wait_time)

            try:
                try:
                    res = session.get(api)
                except requests.exceptions.RequestException as e:
                    session.close()
                    session = requests.Session()
                    session.headers.update(headers)

                    res = session.get(api)
                res = res.json()
                return res, requests_left
            except requests.exceptions.RequestException as e:
                print(f'{logging_code.ERROR}ERROR{logging_code.ENDC}, with {logging_code.WARNING}{e}{logging_code.ENDC}')
                return None, requests_left

        case 422:
            print(f'{logging_code.ERROR}ERROR{logging_code.ENDC}, exceed limit requests with {logging_code.WARNING}{res.status_code}{
                  logging_code.ENDC} when getting {logging_code.WARNING}{package_name}{logging_code.ENDC} from {logging_code.WARNING}{api}{logging_code.ENDC}')
            return None, requests_left

        case _:
            if res.status_code != 200:
                print(f'{logging_code.ERROR}ERROR{logging_code.ENDC}, with {logging_code.WARNING}{res.status_code}{
                      logging_code.ENDC} when getting {logging_code.WARNING}{package_name}{logging_code.ENDC} from {logging_code.WARNING}{api}{logging_code.ENDC}')
                return None, requests_left

            try:
                res = res.json()
                return res, requests_left
            except json.decoder.JSONDecodeError as e:
                if debug:
                    print(f'{logging_code.WARNING}Debugging step{logging_code.ENDC}')
                    print(api)
                    print(res.text)

                res = res.text

                result, is_json = detect_json_and_clean_and_fix_json(res)
                if not is_json:
                    return res, requests_left
                
                if result is None:
                    print(res.text)
                    return None, requests_left

                return result, requests_left
