output="../../files/runs"
data="../../files"
device="cpu"

# sql dataset
echo "test SQL"
dataset="sql_dataset.bin"
commandline="-batch_size 10 -max_epoch 200 -valid_per_batch 280 -save_per_batch 280 -decode_max_time_step 750 -optimizer adadelta -rule_embed_dim 128 -node_embed_dim 64 -valid_metric bleu -no_retrieval"
datatype="sql"

for model in "model.npz"; do
	THEANO_FLAGS="mode=FAST_RUN,device=${device},floatX=float32" python2 code_gen.py \
	-data_type ${datatype} \
	-data ${data}/${dataset} \
	-output_dir ${output} \
	-model ${output}/${model} \
	${commandline} \
	decode \
	-saveto ${output}/${model}.decode_results_sql.test.bin

	python2 code_gen.py \
		-data_type ${datatype} \
		-data ${data}/${dataset} \
		-output_dir ${output} \
		evaluate \
		-input ${output}/${model}.decode_results_sql.test.bin
done