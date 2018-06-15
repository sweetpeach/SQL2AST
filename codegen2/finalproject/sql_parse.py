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

    #rule_list = list(reversed(rule_list))
    #print("rule list : " + str(rule_list))
    tree = sql_ast_to_parse_tree(rule_list)
    
    return tree

def sql_ast_to_parse_tree(rule_list):
    print("----------------------------------")

    queue = []
    for rule_idx in range(len(rule_list)):
    #while rule_list:
        current_level = rule_list.pop()
        parent = current_level[0]
        #print("parent: " + str(parent))
        length = len(current_level)
        
        list_of_children = []
        for node_idx in range(1, length):
            child = current_level[node_idx]

            if child[0:8] == "LexToken":
                temp = child[9:len(child)-1].split(",")
                first_child_node = ASTNode(temp[0])

                node_type = type(temp[1])
                node_value = temp[1]
                second_child_node = ASTNode(node_type=node_type, value=node_value)
                first_child_node.add_child(second_child_node)
                list_of_children.append(first_child_node)
            else:
                #print "not lex: " + child
                child_node = create_node_with_empty_leaf(child)
                list_of_children.append(child_node)
        #print("list of children: " + str(list_of_children))
        if queue:
            front = queue.pop(0)
        else:
            root = ASTNode(parent)
            front = root
        #print "queue: " + str(queue)
        while front.type != parent and queue:
            front = queue.pop(0)
            #print("inside while")

        #print("old front: " + str(front))# + "rule_idx: " + str(rule_idx))
        if rule_idx > 0:
            #print "here"
            front.__delitem__("empty")

        for child in list_of_children:
            front.add_child(child)

        #print("new front: " + str(front))
        queue.extend(reversed(list_of_children))
        #print("root: " + str(root))
        #pointer
    #print root
    tree = add_root(root)
    return tree

def create_node_with_empty_leaf(node_name):
    tree = ASTNode(node_name)
    empty_child = ASTNode("empty")
    tree.add_child(empty_child)
    return tree

def add_root(tree):
    root_node = ASTNode("root")
    root_node.add_child(tree)

    return root_node

def parse_sql(query):
    """
    parse an SQL code into a tree structure
    code -> AST tree -> AST tree to internal tree structure
    """
    sql_parser = SQLParser()
    result_file="/Users/shayati/Documents/summer_2018/sql_to_ast/SQL2AST/codegen2/finalproject/sql_rules.json"
    parse_tree, rule_list = sql_parser.parse(query, do_write=True, outfile=result_file)
    pprint.pprint([parse_tree])
    
    #tree = sql_rules_to_tree(query, result_file)
    tree = sql_ast_to_parse_tree(rule_list)
    return tree

if __name__ == '__main__':
    
    sql_parser = SQLParser()
    query = "SELECT my_column FROM That_Table;"
    tree = parse_sql(query)
    print("=> TREE <=")
    print(tree)

    '''

    fake_query = ""
    result_file="/Users/shayati/Documents/summer_2018/sql_to_ast/SQL2AST/codegen2/finalproject/test_file_shorter.json"
    final_tree = sql_rules_to_tree(fake_query, result_file)
    print("****** FINAL TREE *******")
    print(final_tree)
    '''
    '''
    root = ASTNode("root")
    child_a = ASTNode("child_a")
    child_b = ASTNode("child_b")
    child_c = ASTNode("child_a")
    root.add_child(child_a)
    root.add_child(child_b)
    root.add_child(child_c)
    child_a.add_child(ASTNode("hehe"))
    print root
    child_a.__delitem__("hehe")
    print root
    '''