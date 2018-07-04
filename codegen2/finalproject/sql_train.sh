output="../../files/runs"
device="cpu"

# sql dataset
echo "training sql dataset"
dataset="sql_dataset.bin"
commandline="-batch_size 10 -max_epoch 200 -valid_per_batch 280 -save_per_batch 280 -decode_max_time_step 750 -optimizer adadelta -rule_embed_dim 128 -node_embed_dim 64 -valid_metric bleu"
datatype="sql"

# train the model
THEANO_FLAGS="mode=FAST_RUN,device=${device},floatX=float32" python2 -u code_gen.py \
	-data_type ${datatype} \
	-data ../../files/${dataset} \
	-output_dir ${output} \
	${commandline} \
	train

# decode testing set, and evaluate the model which achieves the best bleu and accuracy, resp.
for model in "model.best_bleu.npz" "model.best_acc.npz"; do
	THEANO_FLAGS="mode=FAST_RUN,device=${device},floatX=float32" python2 code_gen.py \
	-data_type ${datatype} \
	-data ../../files/${dataset} \
	-output_dir ${output} \
	-model ${output}/${model} \
	${commandline} \
	decode \
	-saveto ${output}/${model}.decode_results.test.bin

	python2 code_gen.py \
		-data_type ${datatype} \
		-data ../../files/${dataset} \
		-output_dir ${output} \
		evaluate \
		-input ${output}/${model}.decode_results.test.bin
done
