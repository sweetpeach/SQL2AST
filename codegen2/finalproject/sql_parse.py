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
from lang.grammar import Grammar
import pprint
import json
import yaml

def sql_rules_to_tree(query, rule_file_path): #don't need this function anymore
    with open(rule_file_path, 'r') as input_file:
        rule_list = yaml.safe_load(input_file)

    #rule_list = list(reversed(rule_list))
    #print("rule list : " + str(rule_list))
    tree = sql_ast_to_parse_tree(rule_list)
    
    return tree

def sql_to_parse_tree(rule_list, debug=False):
    queue = []
    level = 0
    for rule_idx in range(len(rule_list)):
    #while rule_list:
        current_level = rule_list.pop()
        parent = current_level[0]
        if debug:
            print("parent: " + str(parent))
        length = len(current_level)
        
        list_of_children = []
        for node_idx in range(1, length):
            child = current_level[node_idx]

            if child[0:8] == "LexToken":
                temp = child[9:len(child)-1].split(",")
                '''
                first_child_node = ASTNode(temp[0])

                node_type = type(temp[1])
                node_value = temp[1]
                second_child_node = ASTNode(node_type=node_type, value=node_value)
                first_child_node.add_child(second_child_node)
                list_of_children.append(first_child_node)
                '''
                child_node = ASTNode(node_type=temp[0], value=temp[1])
                list_of_children.append(child_node)
            else:
                #print "not lex: " + child
                child_node = create_node_with_empty_leaf(child)
                #child_node = ASTNode(child)
                list_of_children.append(child_node)
        if debug:
            print("list of children: " + str(list_of_children))
        if queue:
            front = queue.pop(0)
            if debug:
                print("front if" + str(front.print_with_level()))
        else:
            root = ASTNode(parent, level=1)
            front = root
        if debug:
            print("queue: " + str(queue))
        while front.type != parent and queue:
            front = queue.pop(0)
            if debug:
                print("front inside while:" + str(front.print_with_level()))

        if debug:
            print("old front: " + str(front.print_with_level()))# + "rule_idx: " + str(rule_idx))
        try:
            if rule_idx > 0:
                #print "here"
                front.__delitem__("empty")
        except:
            pass

        for child in list_of_children:
            level = front.level + 1
            child.level = level
            front.add_child(child)

        if debug:
            print("new front: " + str(front.print_with_level()))
            print("queue before extension: " + str(queue))
        #queue.extend(reversed(list_of_children))
        reversed_children = list(reversed(list_of_children))
        queue = reversed_children + queue
        
        if debug:
            print "last queue: " + str(queue)
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

def source_from_parse_tree(tree):
    sql = ''
    terminals = tree.get_leaves()
    for terminal in terminals:
        if terminal.type is not "empty":
            token = terminal.value.replace("'","")
            if terminal.type == "STRING":
                sql += '"' + token + '" '
            elif terminal.type == "DELIM":
                sql = sql.strip() + token
            else:
                sql += token + " "
    
    return sql

def get_grammar(parse_trees):
    rules = set()
    # rule_num_dist = defaultdict(int)

    for parse_tree in parse_trees:
        parse_tree_rules, rule_parents = parse_tree.get_productions()
        for rule in parse_tree_rules:
            rules.add(rule)

    rules = list(sorted(rules, key=lambda x: x.__repr__()))
    print rules
    grammar = Grammar(rules)

    logging.info('num. rules: %d', len(rules))
    print "here"
    #return grammar


def parse_sql(query):
    """
    parse an SQL code into a tree structure
    code -> AST tree -> AST tree to internal tree structure
    """
    sql_parser = SQLParser()
    #result_file="/Users/shayati/Documents/summer_2018/sql_to_ast/SQL2AST/codegen2/finalproject/sql_rules.json"
    parse_tree, rule_list = sql_parser.parse(query, get_rules=True)#, do_write=True, outfile=result_file)
    #parse_tree, rule_list = sql_parser.parse(query, get_rules=True, do_write=True, outfile=result_file)
    #pprint.pprint([parse_tree])
    
    #tree = sql_rules_to_tree(query, result_file)
    tree = sql_to_parse_tree(rule_list)
    return tree

if __name__ == '__main__':
    from nn.utils.generic_utils import init_logging
    init_logging('misc.log')
    
    #sql_parser = SQLParser()
    #query = 'SELECT my_column FROM That_Table limit 3;'
    #query = 'SELECT * FROM That_Table as ALIAS_TABLE where x LIKE "%hihi%";'
    #query = 'SELECT  "State/District/Territory" from Obesity_in_the_US  ORDER BY  "Obesity_Rank", "ASC" LIMIT 1;'
    query = 'SELECT "2018" FROM Customers_0 WHERE ((Country="Argentina") OR (City="Campinas"));'
    #query ='SELECT  "Value" FROM Power_Transmitter  WHERE  "Property"  LIKE "%%Description%";'

    tree = parse_sql(query)
    get_grammar([tree])
    print("---------- => TREE <= ----------")
    print(tree)
    sql_query = source_from_parse_tree(tree)
    print("---------- => QUERY <= ----------")
    print(sql_query)

    #parse the generated SQL query again and see if it is working
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