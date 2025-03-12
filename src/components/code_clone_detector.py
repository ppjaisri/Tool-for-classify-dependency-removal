import hashlib
import esprima

from collections import defaultdict
from difflib import SequenceMatcher


class CodeCloneDetector:
    def __init__(self, n_gram_size=15, verification_threshold=0.65):
        self.n_gram_size = n_gram_size  # N-gram size
        self.inverted_index = defaultdict(set)  # HashMap for N-grams
        self.verification_threshold = verification_threshold  # Threshold for final clone confirmation

    def extract_ast_nodes(self, js_code):
        """
        Parses JavaScript code into an AST and extracts a sequence of node types.
        """
        try:
            ast = esprima.parse(js_code, tolerant=True)
            node_sequence = []
            self._dfs_traverse(ast, node_sequence)
            return ast, node_sequence
        except Exception as e:
            print(f"Error parsing JavaScript code: {e}")
            return [], []

    def _dfs_traverse(self, node, sequence):
        """
        Performs a depth-first traversal on the AST and records node types.
        """
        stack = [node]

        while stack:
            current = stack.pop()
            if hasattr(current, 'type'):
                sequence.append(current.type)

            # Get all attributes that could be child nodes
            children = []
            for attr in dir(current):
                if not attr.startswith('_') and attr != 'type':
                    child = getattr(current, attr)
                    if isinstance(child, list):
                        children.extend(item for item in child if hasattr(item, 'type'))
                    elif hasattr(child, 'type'):
                        children.append(child)
            
            # Add children to stack in reverse order for DFS
            stack.extend(reversed(children))

    def generate_n_grams(self, node_sequence: list[str]) -> list[tuple]:
        """
        Generates N-grams from an AST node sequence.
        """
        n = self.n_gram_size
        return [tuple(node_sequence[i:i + n]) for i in range(len(node_sequence) - n + 1)]

    def hash_n_gram(self, n_gram) -> str:
        """
        Hash function to convert N-gram into a unique key.
        """
        return hashlib.md5(str(n_gram).encode()).hexdigest()

    def build_inverted_index(self, code_blocks):
        """
        Constructs an inverted index from a list of JavaScript code blocks.
        """
        for block_id, js_code in enumerate(code_blocks):
            ast_nodes, node_sequences = self.extract_ast_nodes(js_code)
            n_grams = self.generate_n_grams(node_sequences)
            for n_gram in n_grams:
                hash_key = self.hash_n_gram(n_gram)
                self.inverted_index[hash_key].add(block_id)

    def compute_lcs_similarity(self, seq1: list[str], seq2: list[str]) -> float:
        """
        Computes the Longest Common Subsequence (LCS) similarity between two AST node sequences.
        Uses difflib.SequenceMatcher to find LCS ratio.

        :return: Similarity score (0.0 to 1.0).
        """
        matcher = SequenceMatcher(None, seq1, seq2)
        return matcher.ratio()  # Returns a similarity score between 0 and 1

    def verify_similarity(self, js_code_1: str, js_code_2: str) -> bool:
        """
        Verification step: Uses LCS to determine if two AST node sequences represent true clones.

        :return: True if the similarity score meets the threshold, otherwise False.
        """
        try:
            # Parse both code blocks into AST
            ast_1 = esprima.parse(js_code_1, tolerant=True)
            ast_2 = esprima.parse(js_code_2, tolerant=True)

            # Extract node sequences using DFS
            seq_1 = self.node_sequences_from_AST(ast_1)
            seq_2 = self.node_sequences_from_AST(ast_2)

            # Compute LCS similarity
            similarity_score = self.compute_lcs_similarity(seq_1, seq_2)

            # Return True if above threshold, otherwise False
            return similarity_score >= self.verification_threshold

        except Exception as e:
            print(f"Error parsing JavaScript code: {e}")
            return False 
