# An Automate Tool for classifying dependency remvoal scenaio in the NPM Ecosytem

The purpose of this tool is to classify dependency removal scenarios on the NPM ecosystem.

The dependency removal scenario is the sequence of commit in project since initially install a dependency until remove it from the project. <br>

- **Dependency Removals with Direct Code Impact**: <br>
    Dependency removal scenarios where a dependency is removed alongside with the code modification, indicating that the removal directly affects the source code (i.e. remove the dependency from the `package.json` with code changes in a commit).
- **Dependency Removals without Direct Code Impact**: <br>
    An opposite of a previous type which refers to dependency removal scenarios where a dependency is removed without the code modification, indicating that the removal is not directly affects the source code (i.e. remove the dependency from the `package.json` only).
- **Unknown**: <br>
    Cannot determine the reason for dependency removal.

## Installation & Usage
> [Note] <br>
> Currently, this tool is design to run in MacOS.
1. Install through release <br>
    Go to the release tag on the left of the page or this [link](https://github.com/ppjaisri/Tool-for-classify-dependency-removal/tags). 
    Then download the preferred version.

2. Install through git clone <br>
    - Make sure that your environment has [Git](https://git-scm.com/downloads).
    - Enter this command into the terminal or git shell. <br>
        ```sh
        git clone -b prepare_tool_for_deploy https://github.com/ppjaisri/Tool-for-classify-dependency-removal.git
        ```

3. Install the python version 3.12

4. Build the tool <br>
    Move to the root of the tool (`<install-location>/Tool-for-classify-dependency-removal/`). <br>
    Simply run this command to build the tool.
    ```sh
    python3 -m pip install .
    ```

5. Run the tool. <br>
    ```
    python3 -m src.main -a <link_to_project_repository> --config <config-path>
    ```
    Where
    ```man
    positional arguments:
        link_to_project_repository
                              The link to the project repository to analyze.

    options:
        -h, --help            show this help message and exit
        --analyze, -a         Analyze the project.
        --config [CONFIG], -c [CONFIG]
                              The path to the config file.
    ```
    This is the preset of `config.json`.
    ```json
    {
        "github_token": "<your-github-token>",
        "root_database": "<path-to-dataset>"
    }
    ```
