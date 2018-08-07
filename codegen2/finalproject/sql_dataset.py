# -*- coding: UTF-8 -*-
from __future__ import division
import ast
import astor
import logging
from itertools import chain
import nltk
import re
from sql_parse import parse_sql, sql_to_parse_tree, source_from_parse_tree, get_sql_grammar
from nn.utils.io_utils import serialize_to_file, deserialize_from_file
from nn.utils.generic_utils import init_logging
import time
from lang.sqlp.parser import SQLParser
from lang.sqlp.sqlpyacc import _lr_productions
from lang.sqlp.sqlplex import _lextokens
from tqdm import tqdm

from dataset import gen_vocab, DataSet, DataEntry, Action, APPLY_RULE, GEN_TOKEN, COPY_TOKEN, GEN_COPY_TOKEN, Vocab
from lang.py.parse import parse, parse_tree_to_python_ast, canonicalize_code, parse_raw, \
    de_canonicalize_code, tokenize_code, tokenize_code_adv, de_canonicalize_code_for_seq2seq
from lang.py.unaryclosure import get_top_unary_closures, apply_unary_closures

QUOTED_STRING_RE = re.compile(r"(?P<quote>['\"])(?P<string>.*?)(?<!\\)(?P=quote)")

def standardize_example(nl_input, sql_query):
    #from lang.sqlp.parser import SQLParser
    
    import re

    nl_tokens = nltk.word_tokenize(nl_input)

    '''
        Replace quoted string in SQL Query with STR
    '''
    str_count = 0
    str_map = dict()

    match_count = 1
    preprocessed_sql_query = sql_query

    #sanity check
    tree = parse_sql(preprocessed_sql_query)
    output_sql = source_from_parse_tree(tree)
    gold_sql = re.sub(' +',' ',sql_query)

    #print("---------------------")
    # preprocessed_sql = output_sql
    # for element in str_map:
    #     output_sql = output_sql.replace(element, str_map[element])
    
    #print(preprocessed_sql)
    #----- WITHOUR STR REPLACEMENT FOR COLUMN NAMES -----
    #temp = gold_sql.split("FROM")
    #gold_sql = temp[0].replace('"','') + "FROM" + temp[1]
    #temp = output_sql.split("FROM")
    #output_sql = temp[0].replace('"','') + "FROM" + temp[1]


    #print(output_sql)
    #print(gold_sql)

    #assert nltk.word_tokenize(gold_sql) == nltk.word_tokenize(output_sql), 'sanity check fails: gold=[%s], actual=[%s]' % (gold_sql, output_sql)

    return nl_tokens, gold_sql, output_sql, str_map


def preprocess_sql_dataset(annot_file, code_file, table_name_file, wikisql):
    examples = []
    err_num = 0
    if wikisql:
        file_writer = open('wikisql_dataset.examples.txt', 'w')
        for idx, (annot, code) in enumerate(zip(open(annot_file), open(code_file))):
            if idx % 10000 == 0:
                print(idx)
            annot = annot.strip()
            code = code.strip()
            nl_tokens = nltk.word_tokenize(annot)
            #nl_tokens, sql_query, preprocessed_sql, str_map = standardize_example(annot, code)
            sql_query = code
            example = {'id': idx, 'query_tokens': nl_tokens, 'code': sql_query}#, 'str_map': str_map}
            examples.append(example)

            file_writer.write('-' * 50 + '\n')
            file_writer.write('example# %d\n' % idx)
            file_writer.write(' '.join(nl_tokens) + '\n')
            file_writer.write('\n')
            file_writer.write(sql_query + '\n')
            file_writer.write('-' * 50 + '\n')

            idx += 1
            #if idx == 2001:
            #    break
    else:
        file_writer = open('sql_dataset.examples.txt', 'w')
        for idx, (annot, code, table_name) in enumerate(zip(open(annot_file), open(code_file), open(table_name_file))):
            annot = annot.strip()
            code = code.strip()
            table_name = table_name.strip()

            nl_tokens, sql_query, preprocessed_sql, str_map = standardize_example(annot, code)
            raw_code = sql_query.replace("Table_1", table_name)
            example = {'id': idx, 'query_tokens': nl_tokens, 'code': preprocessed_sql,
                       'table_name': table_name, 'raw_code': raw_code}#, 'str_map': str_map}
            examples.append(example)

            file_writer.write('-' * 50 + '\n')
            file_writer.write('example# %d\n' % idx)
            file_writer.write(' '.join(nl_tokens) + '\n')
            file_writer.write('\n')
            file_writer.write(sql_query + '\n')
            file_writer.write(preprocessed_sql + '\n')
            file_writer.write(table_name + '\n')
            file_writer.write(raw_code + '\n')
            file_writer.write('-' * 50 + '\n')

            idx += 1

        file_writer.close()

    return examples

def parse_sql_dataset(dataset, final_dataset_name, with_col=False):
    MAX_QUERY_LENGTH = 70 # FIXME: figure out the best config!
    WORD_FREQ_CUT_OFF = 2

    if dataset == "wikisql":
        print("--- CREATE WIKISQL DATASET WITH COLUMN NAMES ---")
        annot_file = '/Users/shayati/Documents/summer_2018/sql_to_ast/wikisql_data/nl_question'
        code_file = '/Users/shayati/Documents/summer_2018/sql_to_ast/wikisql_data/sql_query'
        table_name_file = ''
    else:
        if not with_col:
            annot_file = '/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/fixed_data/new_sql_generation.in'
            code_file = '/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/fixed_data/new_sql_generation.out'
            table_name_file = '/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/fixed_data/sql.table'
        else:
            print("--- CREATE SQL DATASET WITH COLUMN NAMES ---")
            annot_file = '/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/fixed_data/col_sql_generation.in'
            code_file = '/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/fixed_data/col_sql_generation.out'
            table_name_file = '/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/fixed_data/col_sql.table'

    #annot_file = '/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/just_two.in'
    #code_file = '/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/just_two.out'
    #table_name_file = '/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/just_two.table'

    if dataset == "wikisql":
        data = preprocess_sql_dataset(annot_file, code_file, table_name_file, wikisql=True)
    else:
        data = preprocess_sql_dataset(annot_file, code_file, table_name_file, wikisql=False)
    #query = 'SELECT "Battle", "huhu" FROM Table_1;'
    #print(standardize_example("Where can I buy stamps?", query))

    #from dataset import canonicalize_example
    #print(canonicalize_example('hehe hihi huhuhu "this is a string" "another string"', "a=1"))

    counter_parse = 0
    start_parse = time.time()
    sql_parser = SQLParser()
    for example in tqdm(data, total=len(data)):
        #if (counter_parse % 1000 == 0 and counter_parse <= 3000) or (counter_parse > 3000 and counter_parse %100 ==0):
        #    print("counter_parse " + str(counter_parse))
        #    doPrint = True
        #else:
        #    doPrint = False
        #example['parse_tree'] = parse_sql(str(example['code']), doPrint)
        query = str(example['code'])
        parse_tree, rule_list = sql_parser.parse(query, get_rules=True)
        example['parse_tree'] = sql_to_parse_tree(rule_list, False)
        counter_parse += 1
    end_parse = time.time()
    parse_time = end_parse - start_parse
    print("Finish making parse tree takes: " + str(parse_time) + " secs")
    parse_trees = [example['parse_tree'] for example in data]
    print("pass")
    grammar = get_sql_grammar(parse_trees)

    # write grammar
    print("write grammar")
    start_grammar = time.time()
    if dataset == "wikisql":
        grammar_file = "wikisql.grammar.txt"
    else:
        grammar_file = "sql.grammar.txt"
    with open(grammar_file, 'w') as f:
        for rule in grammar:
            #print("writing grammar")
            f.write(rule.__repr__() + '\n')
    end_grammar = time.time()
    grammar_time = end_grammar - start_grammar
    print("Finish writing grammar: " + str(grammar_time) + " secs")

    # # build grammar ...
    # from lang.py.py_dataset import extract_grammar
    # grammar, all_parse_trees = extract_grammar(code_file)

    annot_tokens = list(chain(*[e['query_tokens'] for e in data]))

    annot_vocab = gen_vocab(annot_tokens, vocab_size=5000, freq_cutoff=WORD_FREQ_CUT_OFF)

    terminal_token_seq = []
    empty_actions_count = 0

    # helper function begins
    def get_terminal_tokens(_terminal_str):
        tmp_terminal_tokens = _terminal_str.split(' ')
        _terminal_tokens = []
        for token in tmp_terminal_tokens:
            if token:
                _terminal_tokens.append(token)
            _terminal_tokens.append(' ')

        return _terminal_tokens[:-1]

    # first pass
    print("--- FIRST PASS ----")
    # for entry in data:
    for entry in tqdm(data, total=len(data)):
        idx = entry['id']
        query_tokens = entry['query_tokens']
        code = entry['code']
        parse_tree = entry['parse_tree']
        #if idx % 100 == 0:
            #print(idx)
        for node in parse_tree.get_leaves():
            #print(node)
            if grammar.is_sql_lextoken(node):
                #print("here again: " + str(node))
                terminal_val = node.value
                terminal_str = str(terminal_val)

                terminal_tokens = get_terminal_tokens(terminal_str)

                for terminal_token in terminal_tokens:
                    assert len(terminal_token) > 0
                    terminal_token_seq.append(terminal_token)

    terminal_vocab = gen_vocab(terminal_token_seq, vocab_size=5000, freq_cutoff=WORD_FREQ_CUT_OFF)
    
    train_data = DataSet(annot_vocab, terminal_vocab, grammar, 'train_data')
    dev_data = DataSet(annot_vocab, terminal_vocab, grammar, 'dev_data')
    test_data = DataSet(annot_vocab, terminal_vocab, grammar, 'test_data')

    all_examples = []

    can_fully_gen_num = 0
    
    # second pass
    #for entry in data:
    print("---- SECOND PASS ----")
    for entry in tqdm(data, total=len(data)):
        idx = entry['id']
        query_tokens = entry['query_tokens']
        code = entry['code']
        #str_map = entry['str_map']
        parse_tree = entry['parse_tree']
        rule_list, rule_parents = parse_tree.get_productions(include_value_node=True)
        
        actions = []
        can_fully_gen = True
        rule_pos_map = dict()
        for rule_count, rule in enumerate(rule_list):
            if not grammar.is_value_node(rule.parent):
            #if not grammar.is_sql_lextoken(rule.parent):
                # print("-------")
                # print("rule value: " + str(rule.value))
                # print(rule)
                # print(rule.parent)
                # print idx
                assert rule.value is None
                
                parent_rule = rule_parents[(rule_count, rule)][0]
                if parent_rule:
                    parent_t = rule_pos_map[parent_rule]
                else:
                    parent_t = 0

                rule_pos_map[rule] = len(actions)

                d = {'rule': rule, 'parent_t': parent_t, 'parent_rule': parent_rule}
                action = Action(APPLY_RULE, d)

                actions.append(action)
            else:
                assert rule.is_leaf

                parent_rule = rule_parents[(rule_count, rule)][0]
                parent_t = rule_pos_map[parent_rule]

                terminal_val = rule.value
                terminal_str = str(terminal_val)
                terminal_tokens = get_terminal_tokens(terminal_str)

                # assert len(terminal_tokens) > 0

                for terminal_token in terminal_tokens:
                    term_tok_id = terminal_vocab[terminal_token]
                    tok_src_idx = -1
                    try:
                        tok_src_idx = query_tokens.index(terminal_token)
                    except ValueError:
                        pass

                    d = {'literal': terminal_token, 'rule': rule, 'parent_rule': parent_rule, 'parent_t': parent_t}

                    # cannot copy, only generation
                    # could be unk!
                    if tok_src_idx < 0 or tok_src_idx >= MAX_QUERY_LENGTH:
                        action = Action(GEN_TOKEN, d)
                        if terminal_token not in terminal_vocab:
                            if terminal_token not in query_tokens:
                                # print terminal_token
                                can_fully_gen = False
                    else:  # copy
                        if term_tok_id != terminal_vocab.unk:
                            d['source_idx'] = tok_src_idx
                            action = Action(GEN_COPY_TOKEN, d)
                        else:
                            d['source_idx'] = tok_src_idx
                            action = Action(COPY_TOKEN, d)

                    actions.append(action)

                d = {'literal': '<eos>', 'rule': rule, 'parent_rule': parent_rule, 'parent_t': parent_t}
                actions.append(Action(GEN_TOKEN, d))

        if len(actions) == 0:
            empty_actions_count += 1
            continue

        if dataset == "wikisql":
            entry_raw_code = None
        else:
            entry_raw_code = entry['raw_code']

        example = DataEntry(idx, query_tokens, parse_tree, code, actions,
                            {'raw_code': entry_raw_code, 'str_map': None})

        if can_fully_gen:
            can_fully_gen_num += 1

        # train, valid, test
        if dataset == "wikisql":
            
            if 0 <= idx < 50900:
                train_data.add(example)
            elif 50900 <= idx < 58200:
                dev_data.add(example)
            else:
                test_data.add(example)
            
            '''
            if 0 <= idx < 1000:
                print("adding train data")
                train_data.add(example)
            elif 1000 <= idx < 1500:
                dev_data.add(example)
            elif 1500 <= idx < 2000:
                test_data.add(example)
            '''
        else:
            if 0 <= idx < 200:
                train_data.add(example)
            elif 200 <= idx < 250:
                dev_data.add(example)
            else:
                test_data.add(example)

        all_examples.append(example)

    # print statistics
    max_query_len = max(len(e.query) for e in all_examples)
    max_actions_len = max(len(e.actions) for e in all_examples)

    print("Start serializing to file...")
    serialize_to_file([len(e.query) for e in all_examples], 'query.len')
    serialize_to_file([len(e.actions) for e in all_examples], 'actions.len')

    logging.info('examples that can be fully reconstructed: %d/%d=%f',
                 can_fully_gen_num, len(all_examples),
                 can_fully_gen_num / len(all_examples))
    logging.info('empty_actions_count: %d', empty_actions_count)
    logging.info('max_query_len: %d', max_query_len)
    logging.info('max_actions_len: %d', max_actions_len)

    train_data.init_data_matrices()
    dev_data.init_data_matrices()
    test_data.init_data_matrices()

    if dataset == "wikisql":
        #bin_file_name = '/Users/shayati/Documents/summer_2018/sql_to_ast/data/wikisql_dataset.bin' #wikisql is always with column name
        bin_file_name = final_dataset_name
    else:
        if with_col:
            bin_file_name = '/Users/shayati/Documents/summer_2018/sql_to_ast/data/col_sql_dataset.bin'
        else:
            bin_file_name = '/Users/shayati/Documents/summer_2018/sql_to_ast/data/sql_dataset.bin'
    serialize_to_file((train_data, dev_data, test_data), bin_file_name)
                      # 'data/django.cleaned.dataset.freq5.par_info.refact.space_only.unary_closure.freq{UNARY_CUTOFF_FREQ}.order_by_ulink_len.bin'.format(UNARY_CUTOFF_FREQ=UNARY_CUTOFF_FREQ))

    return train_data, dev_data, test_data

if __name__ == '__main__':
    #init_logging('sql_dataset.log')
    start = time.time()
    dataset = "wikisql"
    #dataset = "sql"
    final_dataset_name = '/Users/shayati/Documents/summer_2018/sql_to_ast/data/new_full_wikisql_dataset.bin'
    parse_sql_dataset(dataset, final_dataset_name, with_col=True)
    end = time.time()
    running_time = end - start
    print("Running time is " + str(running_time) + " seconds")