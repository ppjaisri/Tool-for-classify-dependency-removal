from typing import Protocol

# Type 1: Move devDependency to other fileds
class Move_Dep_Scenario(Protocol):
    """
    Move_Dep_Scenario is a protocol that defines the structure for scenarios involving 
    the movement or removal of dependencies.
    Attributes:
        name (str): The name of the scenario.
        verison_of_package_json (str): The version of the package.json file associated with the scenario.
        date_of_change (str): The date when the change was made.
    """

    name: str
    verison_of_package_json: str
    date_of_change: str

class Move_Dep_Result(Protocol):
    """
    Move_Dep_Result is a protocol that defines the structure for the result of a dependency removal operation.
    Attributes:
        type_of_scenario (str): The type of scenario being described.
        number_of_scenarios (int): The total number of scenarios.
        scenarios (list): A list of scenarios, each represented by an instance of Move_Dep_Scenario.
        scenarios_group_by_dependent (list): A list of scenarios grouped by their dependencies.
    """

    type_of_scenario: str
    number_of_scenarios: int
    # scenarios: list[Move_Dep_Scenario]
    scenarios: list
    scenarios_group_by_dependent: list

# Type 2: Remove bloat dependency
remove_bloat_dependency = {
    'type': 'Remove bloat dependency',
    'number_of_scenarios': int,
    'scenarios': [
        {
            'name': str,
            'verison_of_package_json': str,
            'date_of_change': str,
        }
    ]
}

# Users input
class Removal_Scenario(Protocol):
    """
    Removal_Scenario is a protocol that defines the structure for scenarios involving the removal of dependencies.
    Attributes:
        name (str): The name of the scenario.
        version (str): The version of the dependency.
        removed_date (str): The date when the dependency was removed.
        installed_date (str): The date when the dependency was installed.
    """

    name: str
    version: str
    removed_date: str
    installed_date: str

class User_Input(Protocol):
    """
    User_Input is a protocol that defines the structure for user input.
    Attributes:
        user_input (str): The input provided by the user.
        usage_interval_scenarios (Removal_Scenario): The scenario involving the removal of dependencies.
    """

    user_input: str
    usage_interval_scenarios: Removal_Scenario
