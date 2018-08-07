import ast
import logging
import re
import token as tk
from cStringIO import StringIO
from tokenize import generate_tokens

from astnode import ASTNode
from lang.py.grammar import is_compositional_leaf, PY_AST_NODE_FIELDS, NODE_FIELD_BLACK_LIST, SQLGrammar
from lang.util import escape
from lang.util import typename
from lang.sqlp.parser import SQLParser
from lang.sqlp.sqlpyacc import _lr_productions
from lang.sqlp.sqlplex import _lextokens
from lang.grammar import Grammar
import pprint
import json
import yaml
from tqdm import tqdm

def sql_rules_to_tree(query, rule_file_path): #don't need this function anymore
    with open(rule_file_path, 'r') as input_file:
        rule_list = yaml.safe_load(input_file)

    #rule_list = list(reversed(rule_list))
    #print("rule list : " + str(rule_list))
    tree = sql_ast_to_parse_tree(rule_list)
    
    return tree

def sql_to_parse_tree(rule_list, doPrint, debug=False):
    queue = []
    level = 0
    if doPrint:
        print("sql to parse tree")
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
    queue = []
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
    terminal_list = tree.get_leaves()
    '''
    print("-=-=-=-=-=-=-=-=-=-=-=-=-=")
    print(tree)
    print "terminal: " + str(terminal_list)
    '''
    position = 0
    #for terminal in terminal_list:
    for i in range(0, len(terminal_list)):
        terminal = terminal_list[i]
        '''
        print("i: " + str(i))
        print(terminal.value)
        print(terminal.type)
        print " length: " + str(len(terminal_list))
        '''
        if str(terminal.type) != "empty":
            #print("here: " + terminal.value)
            token = terminal.value.replace("'","").replace("<eos>","")
            if terminal.type == "STRING":
                sql += '"' + token + '" '
            elif terminal.type == "DELIM":
                sql = sql.strip() + token
            elif str(terminal.type) == "IDENT" and str(token) != "Table_1":
                #print(token)
                sql += '"' + token + '" '
            else:
                sql += token + " "
            position += 1
    sql = sql.replace("  ", ", ")
    #print(sql)
    return sql

def get_sql_grammar(parse_trees):
    rules = set()
    # rule_num_dist = defaultdict(int)
    for parse_tree in tqdm(parse_trees, total=len(parse_trees)):
    #for parse_tree in parse_trees:
        #print("parse tree")
        parse_tree_rules, rule_parents = parse_tree.get_productions()
        for rule in parse_tree_rules:
            rules.add(rule)

    rules = list(sorted(rules, key=lambda x: x.__repr__()))
    #print "rules: " + str(rules)
    grammar = SQLGrammar(rules)

    logging.info('num. rules: %d', len(rules))
    print "get sql grammar"
    return grammar


def parse_sql(query, doPrint):
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
    tree = sql_to_parse_tree(rule_list, doPrint)
    return tree

def count_lines(fname):
    with open(fname) as f:
        return sum(1 for line in f)

def read_dataset_and_parse(input_path):
    sql_parser = SQLParser()
    counter = 0
    with open(input_path) as input_file:
        for query in tqdm(input_file, total=count_lines(input_path)):
            #tree = parse_sql(query, False)
            parse_tree, rule_list = sql_parser.parse(query, get_rules=True)
            sql_to_parse_tree(rule_list, False)
            counter += 1

    '''
    for i in tqdm(range(1000000)):
        j = 10
        while j < 100000000:
            j = j * 2
    '''


if __name__ == '__main__':
    sql_dataset_file = "/Users/shayati/Documents/summer_2018/sql_to_ast/wikisql_data/wikisql_dev.query"
    read_dataset_and_parse(sql_dataset_file)
    '''
    from nn.utils.generic_utils import init_logging
    init_logging('misc.log')
    
    #sql_parser = SQLParser()
    #query = 'SELECT my_column FROM That_Table limit 3;'
    #query = 'SELECT * FROM That_Table as ALIAS_TABLE where x LIKE "%hihi%";'
    #query = 'SELECT  "State/District/Territory" from Obesity_in_the_US  ORDER BY  "Obesity_Rank", "ASC" LIMIT 1;'
    #query = 'SELECT "2018" FROM Customers_0 WHERE ((Country="Argentina") OR (City="Campinas"));'
    query ='SELECT  "Value", "COL FROM", "haha" FROM Power_Transmitter  WHERE  "Property"  LIKE "%%Description%" AND "huhu" LIKE "HIHI";'
    #query = 'SELECT "Battle", "Unlock_Requirements" FROM Table_1;'
    #query = 'SELECT  "Date" FROM Table_1  WHERE  (("Fighter_1"  LIKE "%%Brock_Lesnar%" )  OR  ("Fighter_2"  LIKE "%%Brock_Lesnar%" ) )  AND  "Event_Name_1"  LIKE "%%UFC%" LIMIT 1;'
    print(query)
    tree = parse_sql(query)
    grammar = get_sql_grammar([tree])
    print("---------- => TREE <= ----------")
    #print(tree)
    sql_query = source_from_parse_tree(tree)
    print("---------- => QUERY <= ----------")
    print(sql_query)
    '''


    '''
    rule_list, rule_parents = tree.get_productions(include_value_node=True)
    for rule_count, rule in enumerate(rule_list):
        #if not grammar.is_value_node(rule.parent):
        if not grammar.is_sql_lextoken(rule.parent):
            print("-------")
            print("rule value: " + str(rule.value))
            print(rule)
            print(rule.parent)
            assert rule.value is None
    '''
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