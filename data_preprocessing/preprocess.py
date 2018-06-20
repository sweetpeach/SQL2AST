'''
	Preprocess .json file
	Create 2 files: 1 consists of natural language questions 
					other consists of SQL queries
'''

import json
def process_dataset(input_path, nl_output_file, sql_output_file):
	with open(input_path) as input_file:
		data = json.load(input_file)

	nl_writer = open(nl_output_file, 'w')
	sql_writer = open(sql_output_file, 'w')
	nl_dict = {}
	sql_dict = {}
	for index in data:
		instance = data[index]
		nl_question = instance['question'].strip()
		sql_query = instance['preprocessed_query'].strip()
		
		if sql_query[len(sql_query)-1] != ";":
			sql_query += ";"
		is_executable = instance['query_execution']['preprocessed_query']
		if is_executable == True and nl_question not in nl_dict and sql_query not in sql_dict:
			nl_writer.write(nl_question+"\n")
			nl_dict[nl_question] = True
			sql_writer.write(sql_query+"\n")
			sql_dict[sql_query] = True

if __name__ == '__main__':
	input_path = "/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/questions_queries.json"
	nl_path = "/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/nl_question.txt"
	sql_path = "/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/sql_query.txt"
	process_dataset(input_path, nl_path, sql_path)
	
	