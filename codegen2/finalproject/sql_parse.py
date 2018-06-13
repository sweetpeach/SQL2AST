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
from lang.sqlp.sqlplex import _lextokens
import pprint
import json
import yaml

def sql_rules_to_tree(query, rule_file_path):
    with open(rule_file_path, 'r') as input_file:
        rule_list = yaml.safe_load(input_file)

    rule_list = list(reversed(rule_list))
    print("rule list : " + str(rule_list))
    tree = sql_ast_to_parse_tree(rule_list, rule_list[0], 0, -1)
    #print(tree)
    return tree

def sql_ast_to_parse_tree(rule_list, current_list, current_rule_idx, prev_line_no):
    tree = ASTNode(current_list[0])
    if len(current_list) == 1:
        print(" ----- empty tree -----")
        empty_child = ASTNode('empty')
        tree.add_child(empty_child)
        print(tree)
        print("current_rule_idx: " + str(current_rule_idx))
        print(" ----- end of empty tree -----")
        return tree
    
    length = len(current_list)
    print("----------------------------------")
    print("current list length: " + str(length))
    print("current_rule_idx: " + str(current_rule_idx))
    print "current list: " + str(current_list)
    hasLexToken = False
    for i in range(1, length):
        index = length - i
        child_node = current_list[index]
        if child_node[0:8] == "LexToken":
            temp = child_node[9:len(child_node)-1].split(",")
            first_child_node = ASTNode(temp[0])
            node_type = type(temp[1])
            node_value = temp[1]
            second_child_node = ASTNode(node_type=node_type, value=node_value)
            first_child_node.add_child(second_child_node)
            tree.add_child(first_child_node)
            hasLexToken = True
        else:
            print "not lex: " + child_node
            print "i: " + str(i)
            print "index: " + str(index)
            if hasLexToken:
                addition = i-1
            else:
                addition = i
            print "addition: " + str(addition)
            print("next rule: " + str(current_rule_idx+addition))
            tree.add_child(sql_ast_to_parse_tree(rule_list, rule_list[current_rule_idx+addition], current_rule_idx+addition, current_rule_idx))
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
    sql_parser = SQLParser()
    result_file="/Users/shayati/Documents/summer_2018/sql_to_ast/SQL2AST/codegen2/finalproject/sql_rules.json"
    parse_tree = sql_parser.parse(query, do_write=True, outfile=result_file)
    pprint.pprint([parse_tree])
    
    tree = sql_rules_to_tree(query, result_file)

    #tree = add_root(tree)
    #return tree

if __name__ == '__main__':
    '''
    sql_parser = SQLParser()
    query = "SELECT my_column FROM That_Table;"
    parse_sql(query)

    '''
    fake_query = ""
    result_file="/Users/shayati/Documents/summer_2018/sql_to_ast/SQL2AST/codegen2/finalproject/test_file_shorter.json"
    final_tree = sql_rules_to_tree(fake_query, result_file)
    print("****** FINAL TREE *******")
    print(final_tree)
