from lang.sqlp.parser import SQLParser

def read_sql_dataset(input_file):
	with open(input_file, "r") as f:
		counter = 0
		for line in f:
			sql_parser = SQLParser()
			query = line.strip()
			try:
				parse_tree, rule_list = sql_parser.parse(query, get_rules=True)
				#print("----- SUCCESS{} -----".format(counter))
			except:
				print("===== FAIL{} =====".format(counter))
				print(query)
				print("=======================")
			counter += 1

sql_path = "/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/sql_generation.out"
read_sql_dataset(sql_path)