'''
	Preprocess .json file
	Create 2 files: 1 consists of natural language questions 
					other consists of SQL queries
'''

import json, re
import nltk

def preprocess_sql(input_sql):
	line = re.sub(r'(from|FROM|From) \"([^\"]+)\"', r'\1 \2', input_sql)
	line = re.sub(r'\"(ASC|DESC)\"', r'\1', line)
	line = re.sub(r'\"((COUNT)\((.*)\))\"', r'\1', line)
	line = re.sub(r'\"((MAX)\((.*)\))\"', r'\1', line)
	line = re.sub(r'\"((AVG)\((.*)\))\"', r'\1', line)
	line = re.sub(r'\"((MIN)\((.*)\))\"', r'\1', line)
	line = re.sub(r'\"((AVERAGE)\((.*)\))\"', r'\1', line)
	line = re.sub(r'SELECT AVERAGE', r'SELECT AVG', line)
	column_search = re.search(r'(SELECT|Select|select)( )*(\"[^\"]+\") (FROM|from|From)', line, re.IGNORECASE)
	column = ""
	if column_search:
		column = column_search.group(3)
		print(column)
	line = line.replace('ORDER BY  ASC', 'ORDER BY '+column+' ASC')
	line = line.replace('ORDER BY  DESC', 'ORDER BY '+column+' DESC')
	line = line.replace(', ASC', ' ASC')
	line = line.replace('" is "', '" = "')
	return line

def read_and_write_dataset(input_path, nl_output_file, sql_output_file, table_file, init_id_file, do_print=False, remove_duplicate=True, preprocess=False):
	with open(input_path) as input_file:
		data = json.load(input_file)

	nl_writer = open(nl_output_file, 'w')
	sql_writer = open(sql_output_file, 'w')
	table_writer = open(table_file, 'w')
	init_id_writer = open(init_id_file, 'w')
	nl_dict = {}
	nl_counter = {}
	sql_dict = {}
	sql_counter = {}
	counter = 0
	for index in data:
		instance = data[index]
		nl_question = instance['question'].strip()
		is_executable = instance['query_execution']['preprocessed_query']
		print(is_executable)
		if is_executable == True:
			print(instance['for_QA_parser'])
			sql_query = instance['for_QA_parser']['query'].strip()
			table_name = instance['for_QA_parser']['table_name'].strip()
		
			if sql_query[len(sql_query)-1] != ";":
				sql_query += ";"
		
			if not (nl_question in nl_dict and sql_query in sql_dict): #and nl_question not in nl_dict and sql_query not in sql_dict
				nlNotInDict = True
				sqlNotInDict = True
				if nl_question in nl_dict and sql_query not in sql_dict:
					#print("================")
					#print("NL question in dict: " + nl_question)
					#print("SQL question not in dict: " + sql_query)
					#print("The SQL which is in dict: " + nl_dict[nl_question])
					#print("===============")
					nlNotInDict = False
					nl_counter[nl_question] += 1
					nl_key = nl_question+"_"+str(nl_counter[nl_question])
					nl_dict[nl_key] = sql_query
					sql_dict[sql_query] = nl_question
				if nl_question not in nl_dict and sql_query in sql_dict:
					#print("------------------------")
					#print("SQL query: " + sql_query)
					#print("NL question not in dict: " + nl_question)
					#print("Old NL in dict: " + sql_dict[sql_query])
					#print("------------------------")
					sqlNotInDict = False
					sql_counter[sql_query] += 1
					sql_key = sql_query+"_"+str(sql_counter[sql_query])
					sql_dict[sql_key] = nl_question
					nl_dict[nl_question] = sql_query

				nl_writer.write(nl_question+"\n")
				sql_writer.write(sql_query+"\n")
				table_writer.write(table_name+"\n")
				init_id_writer.write(str(index) + "\n")
				if nlNotInDict and sqlNotInDict:
					nl_dict[nl_question] = sql_query
					nl_counter[nl_question] = 1
					sql_dict[sql_query] = nl_question
					sql_counter[sql_query] = 1
			elif nl_question in nl_dict and sql_query in sql_dict:
				if do_print:
					print("--- Duplicated #{}---".format(counter))
					print(nl_question)
					print(sql_query)
					print("----FINISH DUPLICATED----")
				counter += 1
				if not remove_duplicate and is_executable:
					nl_writer.write(nl_question+"\n")
					sql_writer.write(sql_query+"\n")
	print("#Duplicated instances: {}".format(counter))
	print("#Instances: {}".format(len(nl_dict)))

if __name__ == '__main__':
	input_path = "/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/questions_queries.json"
	nl_path = "/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/new_nl_question.txt"
	sql_path = "/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/new_sql_query.txt"
	table_path = "/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/new_table.txt"
	id_path = "/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/new_initial_id.txt"
	read_and_write_dataset(input_path, nl_path, sql_path, table_path, id_path, do_print=True, preprocess=True)

	'''
	sql = 'SELECT  "hehe" FROM X WHERE  "Property"  LIKE "%%people%HIV%" ORDER BY  "ASC";'
	result = preprocess_sql(sql)
	print(result)
	'''

	'''
	query = 'it is just a "query" abc.efg "second string"'
	code = """a = "hihi" """
	q, c, str_map = process_query(query, code)
	print(q)
	print(c)
	print(str_map)
	'''
	
	