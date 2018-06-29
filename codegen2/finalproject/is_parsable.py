from lang.sqlp.parser import SQLParser
import re

prohibited_chars = set('-,?:;()')

def fix_table_name(query):
	orig_table_name = "TABLE_1"
	search = re.search(r'(FROM|from|From) (.*)(;)',query, re.IGNORECASE)
	if search:
		table_name = search.group(2)
		#print(table_name)
		if any((c in prohibited_chars) for c in table_name) or table_name[0].isdigit():
			#print("tetot")
			orig_table_name = table_name
			query = query.replace(table_name, "TABLE_1")
			#print("new query: " + query)
	else:
		split_it = query.split("WHERE")
		query = split_it[0].strip() + " FROM TABLE_1 WHERE " + split_it[1].strip()
	return query, orig_table_name

def read_sql_dataset(sql_input_file, nl_input_file, table_in, sql_out, nl_out, table_out):
	failure = 0
	nl_writer = open(nl_out, 'w')
	sql_writer = open(sql_out, 'w')
	table_writer = open(table_out, 'w')
	with open(sql_input_file, "r") as sql_file, open(nl_input_file, "r") as nl_file, open(table_in, "r") as table_file:
		counter = 1
		for sql_line, nl_line, table_line in zip(sql_file, nl_file, table_file):
			sql_parser = SQLParser()
			query = sql_line.strip()
			try:
				#new_query, orig_table_name = fix_table_name(query)
				parse_tree, rule_list = sql_parser.parse(query, get_rules=True)
				nl_writer.write(nl_line)
				table_writer.write(table_line)
				sql_writer.write(str(query)+"\n")
				#print("----- SUCCESS{} -----".format(counter))
			except:
				print("===== FAILURE in QUERY {} =====".format(counter))
				print(query)
				print("=======================")
				failure += 1
			counter += 1
	print("Num of non-parsable queries: {}".format(failure))

if __name__ == '__main__':
	path = "/Users/shayati/Documents/summer_2018/sql_to_ast/sql_data/"
	sql_path = path + "new_sql_query.txt"
	nl_path = path + "new_nl_question.txt"
	table_path = path + "new_table.txt"
	new_nl = path + "new_sql_generation.in"
	new_sql = path + "new_sql_generation.out"
	new_table = path + "sql.table"
	read_sql_dataset(sql_path, nl_path, table_path, new_sql, new_nl, new_table)

#parse_tree, rule_list = sql_parser.parse('SELECT  AVG("price_1", "+", 0.01*"price_2") FROM air_fryers;', get_rules=True)
#sql = 'SELECT bla2bla2 WHERE hihi = "1";'
#fix_table_name(sql)