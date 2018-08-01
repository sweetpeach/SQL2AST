import ujson as json
from tqdm import tqdm
from common import count_lines, detokenize
from query import Query
from sqlp.parser import SQLParser

agg_ops = ['', 'MAX', 'MIN', 'COUNT', 'SUM', 'AVG']
cond_ops = ['=', '>', '<', 'OP']
syms = ['SELECT', 'WHERE', 'AND', 'COL', 'TABLE', 'CAPTION', 'PAGE', 'SECTION', 'OP', 'COND', 'QUESTION', 'AGG', 'AGGOPS', 'CONDOPS']

def read_table(json_table_path):
	with open(json_table_path) as table_file:
		tables = {}
		for line in tqdm(table_file, total=count_lines(json_table_path)):
			d = json.loads(line)
			tables[d['id']] = d

	return tables

def read_and_write_query(query_question_path, tables, question_output_path, sql_output_path, table_path, valid_file_counter, debug=False, do_append=False):
	sql_parser = SQLParser()
	if do_append: 
		sql_writer = open(sql_output_path, 'a')
		question_writer = open(question_output_path, 'a')
		table_writer = open(table_path, 'a')
	else:
		sql_writer = open(sql_output_path, 'w')
		question_writer = open(question_output_path, 'w')
		table_writer = open(table_path, 'w')
	num_of_unicode_error = 0
	num_of_non_parsable_error = 0
	with open(query_question_path) as qq_file:
		queries = []
		questions = []
		counter = 0
		for line in tqdm(qq_file, total=count_lines(query_question_path)):
			data = json.loads(line)
			question = data['question']
			table_id = data['table_id']
			table = tables[table_id]
			column_names = table["header"]
			#print(column_names)
			sql = data['sql']
			select_col = table["header"][int(sql["sel"])]
			agg = agg_ops[int(sql["agg"])]
			conditions = sql["conds"]
			use_column_name = True
			query = Query(int(sql["sel"]), int(sql["agg"]), column_names, use_column_name, conditions)
			#print("select col: " + select_col)
			#print("agg: " + agg)
			#print(question)
			#print(sql)
			
			#print(col_names)
			hasError = False
			try:
				sql_query = query.__repr__()
				col_names = " COL_END COL_START ".join(str(x) for x in column_names)
			except:
				if debug:
					print("ERROR in line unicode" + str(counter))
				hasError = True
				num_of_unicode_error += 1
			if not hasError:
				try:
					#new_query, orig_table_name = fix_table_name(query)
					parse_tree, rule_list = sql_parser.parse(sql_query, get_rules=True)
					sql_writer.write(sql_query + "\n")
					question_writer.write(question  + " COL_START " + col_names + " COL_END\n")
					valid_file_counter += 1
				except:
					if debug:
						print("ERROR in line " + str(counter) + " :" + str(sql_query))
					num_of_non_parsable_error += 1
				counter += 1
			#if counter == 10:
			#	break
		print("Unicode error: " + str(num_of_unicode_error))
		print("Nonparsable error: " + str(num_of_non_parsable_error))
		return valid_file_counter


#table_path = "WikiSQL/data/dev.tables.jsonl"
#train file
train_table_path = "../../../../wikisql/WikiSQL/data/train.tables.jsonl"
train_question_path = "../../../../wikisql/WikiSQL/data/train.jsonl"
train_tables = read_table(train_table_path)
train_questions = "../../../wikisql_data/nl_question"
train_queries = "../../../wikisql_data/sql_query"
#counter = 0
counter = read_and_write_query(train_question_path, train_tables, train_questions, train_queries, train_table_path, 0, do_append=True)
print(counter)
#dev file
dev_table_path = "../../../../wikisql/WikiSQL/data/dev.tables.jsonl"
dev_question_path = "../../../../wikisql/WikiSQL/data/dev.jsonl"
dev_tables = read_table(dev_table_path)
dev_questions = "../../../wikisql_data/nl_question"
dev_queries = "../../../wikisql_data/sql_query"
counter = read_and_write_query(dev_question_path, dev_tables, dev_questions, dev_queries, dev_table_path, counter, do_append=True)
print(counter)
#test file
test_table_path = "../../../../wikisql/WikiSQL/data/test.tables.jsonl"
test_question_path = "../../../../wikisql/WikiSQL/data/test.jsonl"
test_tables = read_table(test_table_path)
test_questions = "../../../wikisql_data/nl_question"
test_queries = "../../../wikisql_data/sql_query"
counter = read_and_write_query(test_question_path, test_tables, test_questions, test_queries, test_table_path, counter, do_append=True)
print(counter)

'''
old
Unicode error: 971
Nonparsable error: 4113
52242

Unicode error: 158
Nonparsable error: 631
60032

Unicode error: 264
Nonparsable error: 1125
74785
'''
'''
new
Unicode error: 1965
Nonparsable error: 3612
50778

Unicode error: 316
Nonparsable error: 548
58335

Unicode error: 475
Nonparsable error: 1004
72734

70% train 20% test 10% dev
'''