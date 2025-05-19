import re
import json

from typing import Union


def classify_commit_message(
    lines: Union[str, list],
    # patterns: dict[str, str],
) -> dict[str, str]:
    """
    Classifies lines of Python code as 'import', 'function', or 'variable'.
    
    Args:
        lines (list): List of lines from a .py file.
    
    Returns:
        dict: Dictionary with classification of lines.
    """
    patterns = {
        "shrink_library": r"(?i)^.*?(?P<action>remove|drop|deprecate|stop supporting|end support|trim|strip|disable|discontinue|reduce|shrink)\s+"
                          r"(?P<target>support|feature|legacy|deprecated|unused|unnecessary|polyfill|code|module|API|function|method|dependency|dependencies)\b"
                          r"(?!.*?(with|to|instead of|, use))",

        "replace_action": r"(?i)^.*?(?P<action>replace|switch from|substitute|migrate from|use|drop)\s+"
                          r"(?P<removed_dep>[\w.-]+),?\s+(with|to|instead of|, use|use)\s+"
                          r"(?P<replacement>[\w.-]+)",

        "remove_unused_dependency": r"(?i)^.*?(?P<action>remove|eliminate|prune|clean up|cleanup|drop|drops)\s+"
                                    r"(?P<removed_dep>[\w.-]+)\b",
    }

    # Classification results
    classified_lines = {key: [] for key in patterns.keys()}

    if '\n' in lines:
        lines = lines.split('\n')

    for line in lines:
        for name, pattern in patterns.items():
            match = re.match(pattern, line, re.IGNORECASE)
            # print(match)
            if match:
                # print(match.groupdict())
                res = {
                    "line": line,
                    "type": name,
                    "removed_dep": match.group("removed_dep") if "removed_dep" in match.groupdict() else None,
                    "replacement": match.group("replacement") if "replacement" in match.groupdict() else None
                }
                classified_lines[name].append(res)
                break
        # raise Exception("Not implemented yet")
        return classified_lines

def classify_python_code(
    lines: str,
    # patterns: dict[str, str],
    custom_log: bool = False
) -> dict[str, str]:
    """
    Classifies lines of Python code as 'import', 'function', or 'variable'.
    
    Args:
        lines (list): List of lines from a .py file.
    
    Returns:
        dict: Dictionary with classification of lines.
    """

    patterns = {
        "comment": r"(\/\*\*[\s\S]*?\*\/|^\s*\*.*$|^\s*\/\*$|^\s*\*\/$|\/\/.*|^\s*#.*$|<!--[\s\S]*?-->|\/\*![\s\S]*?\*\/)",
        # "simple_import": r"^(\/\*.*?\*\/\s*)?import\s+[a-zA-Z0-9_-]+(\s+as\s+\w+)?(\s*\/\/.*)?$",
        # "import_from": r"^(\/\*.*?\*\/\s*)?import\s+[a-zA-Z0-9_-]+\s+from\s+[a-zA-Z0-9_-]+(\s+as\s+\w+)?(\s*\/\/.*)?$",
        # "es5_import": r"^\s*.*require\s*\(['\"][^'\")]+['\"]\)",
        "conditional": r"^\s*(if|else\s*if|else)\b.*|.*\?.*:",
        "function_declaration": r"^\s*(function\s+\w+\s*\(|(var|let|const)\s+\w+\s*=\s*\(?\w*\)?\s*=>)",
        "function_usage": r"^\s*[\w]+\.\w+\s*\(.*\)|^\s*[\w]+\s*\(.*\)$",
        "loop": r"^\s*(for|while|do)\b.*\{?",
        "variable": r"^\s*(var|let|const)\s+\w+\s*=\s*[^=><!]+\s*[^>](?<!\s=>).*$",
        "class_declaration": r"^\s*class\s+\w+\s*\{?",
        "class_variable": r"^\s*[\w]+\.[\w]+\s*=\s*.*"
    }

    # Classification results
    classified_lines = {key: [] for key in patterns.keys()}
    comment_blocks = []
    code_without_comment = []
    current_comment_block = []
    inside_comment_block = False

    if '\n' in lines:
        lines = lines.split('\n')

    for line in lines:
        stripped_line = line.strip()
        if stripped_line == "":
            continue  # Ignore empty lines

        classified = False

        # Detect start of multi-line comment
        if stripped_line.startswith("/**") or stripped_line.startswith("/*") or stripped_line.startswith("<!--"):
            inside_comment_block = True
            current_comment_block.append(line)
            continue

        # Detect end of multi-line comment
        if inside_comment_block and stripped_line.endswith("*/") or stripped_line.endswith("-->"):
            current_comment_block.append(line)
            # comment_blocks.append("\n".join(current_comment_block))
            comment_blocks.extend(current_comment_block)
            current_comment_block = []
            inside_comment_block = False
            continue

        # Inside multi-line comment block
        if inside_comment_block:
            current_comment_block.append(line)
            continue

        # Single-line comments
        if re.match(patterns["comment"], stripped_line):
            comment_blocks.append(line)
            continue

        # Classify non-comment lines
        for category, pattern in patterns.items():
            if category == "comment":
                continue  # Skip comment classification
            if re.match(pattern=pattern, string=stripped_line):
                classified_lines[category].append(stripped_line)
                classified = True
                break  # Stop after the first match

        # Unclassified code lines
        if not classified:
            if "unclassified" not in classified_lines:
                classified_lines["unclassified"] = [stripped_line]
            else:
                classified_lines["unclassified"].append(stripped_line)

        # Add code to the code_without_comment list
        code_without_comment.append(stripped_line)

    res = {
        'classified_lines': classified_lines,
        'comment': comment_blocks,
        'code_without_comment': code_without_comment
    }

    return res

def classify_python_code_with_grouping(
    lines: Union[str, list],
    # patterns: dict[str, str],
) -> dict:
    """
    Classifies lines of Python code as 'import', 'function', or 'variable'.
    
    Args:
        lines (list): List of lines from a .py file.
    
    Returns:
        dict: Dictionary with classification of lines.
    """
    patterns = {
        "simple_import": r"^(\/\*.*?\*\/\s*)?import\s+(?P<module>[a-zA-Z0-9_-]+)(\s+as\s+\w+)?(\s*\/\/.*)?$",
        "import_from": r"^\s*import\s+(?P<items>[\w\{\}\*,\s]*)\s+from\s+['\"](?P<module>[^'\"]+)['\"]",
        "es5_import": r"require\s*\(['\"](?P<module>[^'\")]+)['\"]\)"
    }
    # Classification results
    classified_lines = {key: [] for key in patterns.keys()}

    splitted_lines = []
    if '\n' in lines:
        for line in lines.strip().split('\n'):
            if line.strip() == "":
                continue
            splitted_lines.append(line.strip())

        lines = splitted_lines
    else:
        splitted_lines = lines

    for line in splitted_lines:
        for name, pattern in patterns.items():
            # match = re.match(pattern, line)
            match = re.search(pattern, line)
            if match:
                module_name = match.group("module") if "module" in match.groupdict() else None
                res = {
                    "line": line,
                    "module_name": module_name
                }
                classified_lines[name].append(res)
                # print({
                #     "line": line,
                #     "type": name,
                #     "module_name": module_name
                # })
                break
 
    return classified_lines

