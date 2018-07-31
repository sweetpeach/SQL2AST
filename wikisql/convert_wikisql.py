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

def read_and_write_query(query_question_path, tables, question_output_path, sql_output_path):
	sql_parser = SQLParser()
	sql_writer = open(sql_output_path, 'w')
	question_writer = open(question_output_path, 'w')
	with open(query_question_path) as qq_file:
		queries = []
		questions = []
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
			print(question)
			#print(sql)
			sql_query = query.__repr__()
			print("query: " + query.__repr__())
			try:
				#new_query, orig_table_name = fix_table_name(query)
				parse_tree, rule_list = sql_parser.parse(sql_query, get_rules=True)
				sql_writer.write(sql_query + "\n")
				question_writer.write(question +"\n")
			except:
				print("ERROR: " + str(sql_query))

			#print("hehe")
#table_path = "WikiSQL/data/dev.tables.jsonl"
#train file
table_path = "test.json"
tables = read_table(table_path)
read_and_write_query("questions.json", tables, "question_result.txt", "sql_result.txt")

#valid file

#test file