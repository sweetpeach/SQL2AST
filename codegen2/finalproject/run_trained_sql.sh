output="../../files/runs"
models="../../files/runs"
device="cpu"

if [ "$1" == "col" ]; then
	echo "run trained model for sql with columns"
	dataset="../../files/col_sql_dataset.bin"
	model="col_noretrieval_best_model.iter3640.npz"
	commandline="-decode_max_time_step 750 -rule_embed_dim 128 -node_embed_dim 64 -enable_retrieval -retrieval_factor 3 -max_retrieved_sentences 3"
	datatype="sql"
else
	# without column
	echo "run trained model for sql without columns"
	dataset="../../files/sql_dataset.bin"
	model="model_best_sql.npz"
	commandline="-decode_max_time_step 750 -rule_embed_dim 128 -node_embed_dim 64 -enable_retrieval -retrieval_factor 3 -max_retrieved_sentences 3"
	datatype="sql"
fi

# decode the test set and save the nbest decoding results
THEANO_FLAGS="mode=FAST_RUN,device=${device},floatX=float32" python2 code_gen.py \
-data_type ${datatype} \
-data ${dataset} \
-output_dir ${output} \
-model ${models}/${model} \
${commandline} \
decode \
-saveto ${output}/${model}.decode_results.test.bin

# evaluate the decoding result
python2 code_gen.py \
-data_type ${datatype} \
-data ${dataset} \
-output_dir ${output} \
evaluate \
-input ${output}/${model}.decode_results.test.bin | tee ${output}/${model}.decode_results.test.log
