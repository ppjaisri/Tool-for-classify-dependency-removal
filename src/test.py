import json
import pty
import os
import time

import pandas as pd
import numpy as np
from pathlib import Path
import subprocess

def run_script(
    command_line_script: str,
    target_dependency: str
) -> None:
    command_line_script = command_line_script.split(' ')

    try:
        # Create a pseudo-terminal
        master_fd, slave_fd = pty.openpty()

        process = subprocess.Popen(
            ["stdbuf", "-oL"] + command_line_script,
            stdin=slave_fd,  # Use PTY for input
            stdout=slave_fd,  # Use PTY for output
            stderr=slave_fd,  # Redirect stderr to PTY
            text=True
        )

        # Close the slave end (we use master_fd for interaction)
        os.close(slave_fd)

        captured_output = []  # Store output for later use
        usage_period = 0

        input_send = False
        stop_watch = 0
        while True:
            # **Check if process has exited with `exit(0)`**
            exit_code = process.poll()
            if exit_code == 0:  # Process has finished
                print(f"\n✅ Process exited with code {exit_code}")
                break  # Stop loop on exit(0)
            elif exit_code is not None:  # Process has finished with an error
                print(f"\n❌ Process exited with code {exit_code}")
                break

            # Check if process has been running for more than 90 minutes
            stop_watch += 1
            if stop_watch >= 5400:  # 90 minutes * 60 seconds
                print("\n❌ Error: Process timed out after 90 minutes")
                process.terminate()
                return {"exit_code": 1, "output": [], "error": "Process timed out", "usage_period": None}

            try:
                # Read output from PTY
                output = os.read(master_fd, 1024).decode()
                found_result_indicator = False
                if output:
                    print(output, end='')  # Print real-time output
                    for line in output.split('\n'):
                        line = line.strip() 
                        if line != "":
                            if line == 'Results of the analysis':
                                found_result_indicator = True
                            if line == 'The full report and classified commits are saved at':
                                found_result_indicator = False
                            if found_result_indicator:
                                captured_output.append(line)
                            if 'Usage period   :' in line:
                                usage_period = line.split(':')[-1].strip().split()[0]

                # **Write input only ONCE**
                if not input_send:
                    time.sleep(0.5)  # Ensure process is ready
                    os.write(master_fd, (target_dependency + '\n').encode())
                    input_send = True  # Prevent further writes

            except OSError:
                pass  # No output yet, but process might still be running

        os.close(master_fd)  # Close master PTY after reading
        process.wait()

        if process.returncode != 0:
            print('❌ Error: Process exited with code', process.returncode)

        return {
            "exit_code": process.returncode,
            "output": captured_output,
            "usage_period": usage_period
        }

    except (subprocess.SubprocessError, OSError) as e:
        print('❌ Error:', e)
        return {"exit_code": 1, "output": [], "error": str(e), "usage_period": None}

    except KeyboardInterrupt:
        print('\n⏹️ Process interrupted.')
        process.terminate()
        return {"exit_code": 1, "output": [], "error": "Process interrupted", "usage_period": None}


def main():
    current_path = Path.cwd()

    if 'src' in str(current_path):
        root_path = current_path.parent
        dataset_file_path = current_path.parent.joinpath('test - Dependency Removal Scenario Classification - Tool - Dataset dep_removal_commit.csv')
    else:
        root_path = current_path
        dataset_file_path = current_path.joinpath('test - Dependency Removal Scenario Classification - Tool - Dataset dep_removal_commit.csv')

    # data = pd.read_csv(dataset_file_path)
    data = pd.read_csv(f'{root_path}/update_test.csv')

    progress = 600
    # try:
    #     with open(f'{root_path}/temp_progress.json', 'r') as file:
    #         progress = json.load(file)
    #         progress = progress['index']
    # except:
    #     pass

    not_classified_data = data[data['Category'].isnull()]

    # ? Example prompt
    # ? python3 -m src.main -a "https://github.com/ant-design/react-slick" -d 0 --config src/config.json
    for index, row in not_classified_data.iterrows():
        print('Index:', index)
        if index < progress:
            continue
        target_dependency = row['removed_dependency']
        link_to_project_repository = row['commit_url'].split('/commit')[0]
        commit_sha = row['commit_url'].split('/commit/')[1]
        # if 'angular' in link_to_project_repository:
        #     continue
        # if 'emotion' in link_to_project_repository:
        #     continue
        prompt = 'python3 -m {} -a -u {} --config {} {}'.format(
            'src.main',
            link_to_project_repository,
            'src/config.json',
            '-d 1'
        )
        print(prompt)
        
        res_output = run_script(prompt, target_dependency)
        print('Exit code from run_script:', res_output['exit_code'])
        if res_output['exit_code'] != 0:
            # print('Error:', res_output['error'])
            continue
        usage_period = res_output['usage_period']
        each_output = res_output['output'][1:]
        each_output = [line for line in each_output if not line.startswith('#')]

        each_output_dict = {}
        current_dependency = None
        for line in each_output:

            if not line.startswith('-'):
                current_dependency = line.strip()

                # Ensure the structure is a list of dicts
                if current_dependency not in each_output_dict:
                    each_output_dict[current_dependency] = []

                each_output_dict[current_dependency].append({
                    "version": None,
                    "reason": []
                })
            else:
                line = line.replace('-', '').strip()

                if 'Version' in line:
                    # Update latest entry
                    each_output_dict[current_dependency][-1]['version'] = line
                else:
                    # Append to the list
                    each_output_dict[current_dependency][-1]['reason'].append(line)

        print('Output:', json.dumps(each_output_dict, indent=4))
        # output.append(each_output_dict)
        for dependency_name, scenarios in each_output_dict.items():
            for scenario in scenarios:
                reasons = scenario['reason']
                
                for reason in reasons:
                    list_of_commit_sha = reason.split('[')[1].strip(']')
                    list_of_commit_sha = [i.strip().strip("'") for i in list_of_commit_sha.split(',')]
                    main_reason = reason.split(':')[0].strip()

                    print(list_of_commit_sha)
                    print(main_reason)
                    if not commit_sha in list_of_commit_sha:
                        continue

                    if main_reason == 'Move dependency to other fields':
                        readable_group = '1 Move dependency to other field'
                    elif main_reason == 'Shrink library':
                        readable_group = '2 Remove bloat dependency'
                    elif main_reason == 'Remove bloat dependency':
                        readable_group = '3 Shrink library'
                    elif main_reason == 'Replace dependency with built-ins or custom functions':
                        readable_group = '4 Repalce dependency with built-ins or custom function'
                    elif main_reason == 'Replace dependency with another dependency':
                        readable_group = '5 Replace dependency with another dependency'
                    elif main_reason == 'Unknown':
                        readable_group = 'Unknown'

                    # row['dependency_usage_period'] = usage_period
                    # row['Category'] = readable_group

                    not_classified_data.loc[not_classified_data['removed_dependency'] == target_dependency, 'Category'] = readable_group
                    not_classified_data.loc[not_classified_data['removed_dependency'] == target_dependency, 'dependency_usage_period'] = usage_period

        data.update(not_classified_data)
        data.to_csv(f'{root_path}/update_test.csv', index=False)

if __name__ == '__main__':
    main()