import ast
import logging
import re
import token as tk
from cStringIO import StringIO
from tokenize import generate_tokens

from astnode import ASTNode
from lang.py.grammar import is_compositional_leaf, PY_AST_NODE_FIELDS, NODE_FIELD_BLACK_LIST, PythonGrammar
from lang.util import escape
from lang.util import typename
from lang.sqlp.parser import SQLParser
from lang.sqlp.sqlpyacc import _lr_productions
import pprint

def sql_ast_to_parse_tree(node):
    assert isinstance(node, ast.AST)

    node_type = type(node)
    tree = ASTNode(node_type)

    # it's a leaf AST node, e.g., ADD, Break, etc.
    if len(node._fields) == 0:
        return tree

    # if it's a compositional AST node with empty fields
    if is_compositional_leaf(node):
        epsilon = ASTNode('epsilon')
        tree.add_child(epsilon)

        return tree

    fields_info = PY_AST_NODE_FIELDS[node_type.__name__]

    for field_name, field_value in ast.iter_fields(node):
        # remove ctx stuff
        if field_name in NODE_FIELD_BLACK_LIST:
            continue

        # omit empty fields, including empty lists
        if field_value is None or (isinstance(field_value, list) and len(field_value) == 0):
            continue

        # now it's not empty!
        field_type = fields_info[field_name]['type']
        is_list_field = fields_info[field_name]['is_list']

        if isinstance(field_value, ast.AST):
            child = ASTNode(field_type, field_name)
            child.add_child(python_ast_to_parse_tree(field_value))
        elif type(field_value) is str or type(field_value) is int or \
                        type(field_value) is float or type(field_value) is object or \
                        type(field_value) is bool:
            # if field_type != type(field_value):
            #     print 'expect [%s] type, got [%s]' % (field_type, type(field_value))
            child = ASTNode(type(field_value), field_name, value=field_value)
        elif is_list_field:
            list_node_type = typename(field_type) + '*'
            child = ASTNode(list_node_type, field_name)
            for n in field_value:
                if field_type in {ast.comprehension, ast.excepthandler, ast.arguments, ast.keyword, ast.alias}:
                    child.add_child(python_ast_to_parse_tree(n))
                else:
                    intermediate_node = ASTNode(field_type)
                    if field_type is str:
                        intermediate_node.value = n
                    else:
                        intermediate_node.add_child(python_ast_to_parse_tree(n))
                    child.add_child(intermediate_node)

        else:
            raise RuntimeError('unknown AST node field!')

        tree.add_child(child)

    return tree

def add_root(tree):
    root_node = ASTNode('root')
    root_node.add_child(tree)

    return root_node

def parse_sql(query):
    """
    parse an SQL code into a tree structure
    code -> AST tree -> AST tree to internal tree structure
    """
    sql_ast = sql_parser.parse(query)

    tree = sql_ast_to_parse_tree(sql_ast[0])

    tree = add_root(tree)

    return tree

if __name__ == '__main__':
    from nn.utils.generic_utils import init_logging
    init_logging('misc.log')

    sql_parser = SQLParser()
    query = "SELECT my_column FROM This_Table;"
    parse_tree = sql_parser.parse(query)
    #print(parse_tree[0][0])
    pprint.pprint([parse_tree])
    #print(_lr_productions[0])
