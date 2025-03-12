import re
import json
import tarfile
import esprima
# import tree_sitter_javascript

from pathlib import Path
from typing import Union, Any
from packaging.version import Version
# from tree_sitter import Language, Parser, Node

from .requests_git_api import request_api
from .element_classification import classify_python_code
from .code_clone_detector import CodeCloneDetector


def get_dependency_source_code(
    dataset_path: Path,
    dependency_name: str,
    version: str,
    update: bool = False,
    detail: bool = False,
) -> Union[str, None]:
    saved_path = dataset_path.joinpath(f'05_source_code_of_removed_dependencies/{dependency_name}')

    if not saved_path.joinpath(f'{dependency_name}-{version}.tgz').exists() or update:

        # print(version)
        # Get the source code of the dependency
        version = re.sub(r"^[~^<>=!]*", "", version)
        find_unstable_version_patterns = {
            "0.x": r"^0\.x$",
            "0.0.x": r"^0\.0\.x$",
            "0.x.y": r"^0\.x\.y$"
        }
        unstable_version = False
        # print(version)
        for pattern in find_unstable_version_patterns.values():
            # print(re.match(pattern=pattern, string=version))
            if re.match(pattern=pattern, string=version):
                unstable_version = True

        dependency_metadata_api = f'https://registry.npmjs.org/{dependency_name}'
        # print(unstable_version)
        if unstable_version:
            print(dependency_metadata_api)
            dependency_metadata, requests_left = request_api(dependency_metadata_api, f'{dependency_name}:metadata')

            matching_versions = list()
            versions = list(dependency_metadata['versions'].keys())
            # print(json.dumps(versions, indent=4))
            for ver in versions:
                parsed_ver = Version(ver)
                # print(parsed_ver)

                for pattern_name, pattern in find_unstable_version_patterns.items():
                    if re.match(pattern=pattern, string=version):
                        if pattern_name == "0.0.x" and parsed_ver.major == 0:
                            matching_versions.append(ver)
                        elif (pattern_name == "0.x.y" or pattern_name == "0.x"):
                            matching_versions.append(ver)

            matching_versions = sorted(matching_versions, key=Version)
            # print(json.dumps(matching_versions, indent=4))
            version = matching_versions[-1]

        # npm_api = f'https://registry.npmjs.org/{dependency_name}/-/{dependency_name}-{version}.tgz'
        dependency_metadata, requests_left = request_api(dependency_metadata_api, f'{dependency_name}:metadata')

        npm_api = dependency_metadata['versions'][version]['dist']['tarball']

        res, requests_left = request_api(npm_api, f'{dependency_name}:{version}')
        if not saved_path.exists():
            saved_path.mkdir(parents=True)

        # Save the downloaded file
        with open(f'{saved_path}/{dependency_name}-{version}.tgz', 'wb') as file:
            for chunk in res.iter_content(chunk_size=1024):
                file.write(chunk)

        # Read and extract the downloaded file
        with open(f'{saved_path}/{dependency_name}-{version}.tgz', 'rb') as file:
            tar = tarfile.open(fileobj=file)
            tar.extractall(path=saved_path)

    main_file = 'index.js'
    with open(f'{saved_path}/package/package.json', 'r') as file:
        package_json = json.load(file)
        if 'main' in package_json.keys():
            # print(json.dumps(package_json, indent=4))
            main_file = package_json['main']
            if not main_file.endswith('.js'):
                main_file += '.js'

    source_code = None
    with open(f'{saved_path}/package/{main_file}', 'r') as file:
        source_code = file.read()

    return source_code

def extract_functions_from_ast(
    ast_tree: Any
):
    """
    Extracts function names, parameters, variable names, and various expressions from a JavaScript AST.
    """
    elements = {}

    # Traverse AST nodes
    def traverse(node):
        if node.type == "function_declaration":
            func_name = node.child_by_field_name("name").text.decode("utf-8")
            parameters = [
                param.text.decode("utf-8") for param in node.child_by_field_name("parameters").children
            ]
            # elements.append({"type": "function", "name": func_name, "parameters": parameters})
            if 'function' not in elements:
                elements['function'] = [{'name': func_name, 'parameters': parameters}]
            else:
                elements['function'].append({'name': func_name, 'parameters': parameters})

        elif node.type == "variable_declaration":
            for child in node.children:
                if child.type == "variable_declarator":
                    var_name = child.child_by_field_name("name").text.decode("utf-8")
                    # elements.append({"type": "variable", "name": var_name})
                    if 'variable' not in elements:
                        elements['variable'] = [var_name]
                    else:
                        elements['variable'].append(var_name)

        elif node.type == "expression_statement":
            expression = node.text.decode("utf-8")
            # elements.append({"type": "expression", "expression": expression})
            if 'expression' not in elements:
                elements['expression'] = [expression]
            else:
                elements['expression'].append(expression)

        elif node.type == "call_expression":
            call_expression = node.text.decode("utf-8")
            # if call_expression.startswith("require("):
                # elements.append({"type": "call_expression", "expression": call_expression})
            if 'call_expression' not in elements:
                elements['call_expression'] = [call_expression]
            else:
                elements['call_expression'].append(call_expression)

        elif node.type == "class_declaration":
            class_name = node.child_by_field_name("name").text.decode("utf-8")
            # elements.append({"type": "class", "name": class_name})
            if 'class' not in elements:
                elements['class'] = [class_name]
            else:
                elements['class'].append(class_name)

        elif node.type == "method_definition":
            method_name = node.child_by_field_name("name").text.decode("utf-8")
            # elements.append({"type": "method", "name": method_name})
            if 'method' not in elements:
                elements['method'] = [method_name]
            else:
                elements['method'].append(method_name)

        elif node.type == "arrow_function":
            # elements.append({"type": "arrow_function", "expression": node.text.decode("utf-8")})
            if 'arrow_function' not in elements:
                elements['arrow_function'] = [node.text.decode("utf-8")]
            else:
                elements['arrow_function'].append(node.text.decode("utf-8"))

        # Recurse through children
        for child in node.children:
            traverse(child)

    traverse(ast_tree)
    return elements

def node_sequences_from_AST(
    ast_tree: Any,
) -> list:
    """
    Traverse an Esprima AST using an iterative Depth-First Search (DFS).
    
    :param node: The root AST node (Esprima node object).
    :return: A list of node types in DFS order.
    """
    sequence = []
    stack = [ast_tree]  # Use a stack instead of recursion

    while stack:
        current = stack.pop()  # Get the last node (LIFO order)

        if hasattr(current, 'type'):  # Process the node if it has a type
            sequence.append(current.type)

        for attr in dir(current):  # Loop through attributes
            # Skip private and "type" itself
            if attr.startswith('_') or attr == 'type':
                continue

            child = getattr(current, attr)

            if isinstance(child, list):  # If it's a list, push all valid children
                for item in reversed(child):  # Reverse to maintain correct DFS order
                    if hasattr(item, 'type'):
                        stack.append(item)

            elif hasattr(child, 'type'):  # If it's a single node, push to stack
                stack.append(child)

    sequence = [i for i in sequence if i is not None]
    return sequence

def generate_n_grams_from_sequence(
    sequence: list,
    n: int
) -> list:
    """
    Generates n-grams from a given sequence.
    
    Args:
        sequence (list): The input sequence from which n-grams are to be generated.
        n (int): The number of elements in each n-gram.
    
    Returns:
        list: A list of n-grams.
    """
    n_grams = [sequence[i:i + n] for i in range(len(sequence) - n + 1)]
    return n_grams

def invert_index_of_n_gram(
    n_grams: list[list]
) -> dict:
    """
    Inverts the index of n-grams to map each unique n-gram to its positions in the sequence.
    
    Args:
        n_grams (list): A list of n-grams.
    
    Returns:
        dict: A dictionary where keys are unique n-grams and values are lists of positions.
    """
    inverted_index = {}
    for index, n_gram in enumerate(n_grams):
        n_gram_key = ','.join(n_gram)
        if n_gram_key not in inverted_index:
            inverted_index[n_gram_key] = [index]
        else:
            inverted_index[n_gram_key].append(index)
    return inverted_index

# def _save_as_a_file(
#     file_name: str,
#     file_type: str,
#     content: str
# ) -> None:
#     with open(f'_{file_name}.{file_type}', 'w') as file:
#         if file_type == 'json':
#             json.dump(content, file, indent=4)
#         else:
#             file.write(str(content))

# def naive_clean_js_code(
#     js_code: str
# ) -> str:
#     """
#     A very naive approach:
#       - Inserts a semicolon if there's a `var` or return statement 
#         at the end of the line with no semicolon.
#       - Balances curly braces if there's an obvious mismatch.
    
#     This is NOT robust, just a demonstration.
#     """
#     is_valid = False

#     def check_valid_code(code: str) -> bool:
#         try:
#             esprima.parseScript(code)
#             return True
#         except Exception as e:
#             return False

#     is_valid = check_valid_code(js_code)

#     if not is_valid:
#         lines = js_code.split('\n')
#         cleaned_lines = []

#         # 1) Insert semicolon if lines end with common statements
#         for line in lines:
#             stripped = line.rstrip()
#             # If line ends with something like "return x" or "var x = 4"
#             if (stripped.startswith("var ") or stripped.startswith("let ") or
#                 stripped.startswith("const ") or stripped.startswith("return ") or
#                     stripped.startswith("function ")):
#                 # Doesn’t necessarily mean we MUST append semicolon
#                 # but let's do a naive check if it ends with a brace, semicolon, or colon
#                 if (stripped.endswith(',')):
#                     stripped = stripped[:-1]
#                     stripped += ';'
#                 if not (stripped.endswith(';') or stripped.endswith('{') or stripped.endswith('}')):
#                     stripped += ';'
#             cleaned_lines.append(stripped)

#         temp_code = "\n".join(cleaned_lines)

#         # 2) Balance curly braces
#         open_braces = temp_code.count('{')
#         close_braces = temp_code.count('}')
#         diff = open_braces - close_braces
#         if diff > 0:
#             # Add missing closing braces at the end
#             temp_code += '\n' + '}' * diff
#         elif diff < 0:
#             # This is unusual (more closes than opens). We can't guess where to add, so skip
#             pass

#         return temp_code
#     else:
#         return js_code

def validated_code_snippet(
    code_snippet: Union[str, list],
    full_code: str
) -> str:
    is_valid = False
    def check_valid_code(code: str) -> bool:
        try:
            esprima.parseScript(code)
            return True
        except Exception as e:
            return False
        
    is_valid = check_valid_code(code_snippet)

    valid_code = ''
    if not is_valid:
        full_code_lines = full_code.split('\n')
        snippet_lines = code_snippet.split('\n') if isinstance(code_snippet, str) else code_snippet
        start_index = -1
        last_index = -1

        for index, line in enumerate(full_code_lines):
            if snippet_lines[0] in line:
                start_index = index

            if snippet_lines[-1] in line:
                last_index = index
                break

        if start_index != -1 and last_index != -1:
            valid_start = max(0, start_index - 5)
            valid_end = min(len(full_code_lines), last_index + 5)
            valid_code = '\n'.join(full_code_lines[valid_start:valid_end])

    if valid_code == '':
        valid_code = code_snippet

    is_valid = check_valid_code(valid_code)
    if not is_valid:
        # valid_code = valid_code.replace(';', ';\n')
        valid_code = valid_code.replace(r"(if|for|while|else|try|catch|function)\s*\((.*?)\)\s*\n", r"\1 (\2) {\n")

        open_params = valid_code.count('(')
        close_params = valid_code.count(')')
        diff_params = open_params - close_params
        valid_code += ')' * diff_params if open_params > close_params else ''

        open_braces = valid_code.count('{')
        close_braces = valid_code.count('}')
        diff_braces = open_braces - close_braces
        valid_code += '}' * diff_braces if open_braces > close_braces else ''

    return valid_code

def compare_replaced_code_with_dependency(
    dataset_path: Path,
    dependency_name: str,
    version: str,
    deleted_code_snippet: str,
    deleted_source_code: Union[str, list],
    replaced_code_snippet: str,
    replaced_source_code: Union[str, list],
    update: bool = False,
    detail: bool = False,
) -> bool:
    if isinstance(replaced_source_code, list):
        replaced_source_code = '\n'.join(replaced_source_code)
    if isinstance(deleted_source_code, list):
        deleted_source_code = '\n'.join(deleted_source_code)

    deleted_code_snippet = '\n'.join(deleted_code_snippet)
    replaced_code_snippet = '\n'.join(replaced_code_snippet)

    validated_deleted_code = validated_code_snippet(deleted_code_snippet, deleted_source_code)
    validated_replaced_code = validated_code_snippet(replaced_code_snippet, replaced_source_code)

    detector = CodeCloneDetector(n_gram_size=15)

    # ? AST & Node sequences
    replaced_ast_parsed, replaced_node_sequence = detector.extract_ast_nodes(validated_replaced_code)
    deleted_ast_parsed, deleted_node_sequence = detector.extract_ast_nodes(validated_deleted_code)

    # ? n-grams
    replaced_n_grams = detector.generate_n_grams(replaced_node_sequence)
    deleted_n_grams = detector.generate_n_grams(deleted_node_sequence)

    common_ngrams_replaced_deleted = len(set(replaced_n_grams) & set(deleted_n_grams))
    union_ngrams_replaced_deleted = len(set(replaced_n_grams) | set(deleted_n_grams))

    if union_ngrams_replaced_deleted == 0:
        print('Not a code clone')

    similarity_score = detector.compute_lcs_similarity(
        seq1=replaced_node_sequence,
        seq2=deleted_node_sequence
    )

    if similarity_score >= 0.65:
        return True
    else:
        return False