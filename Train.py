import tensorflow as tf
import tensorflow_hub as hub
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import os

def load_data_set(file):
	df = pd.read_csv(file)
	msk = np.random.rand(len(df)) < 0.8
	return df[msk], df[~msk]

def one_hot(dataset, match):
	dataset['y'] = 0
	dataset.loc[dataset[match] == 'FAKE', 'y'] = 1
	return dataset

def get_predictions(estimator, input_fn):

  	return [x["class_ids"][0] for x in estimator.predict(input_fn=input_fn)]

if __name__ == "__main__":

	tf.logging.set_verbosity(tf.logging.INFO)

	################################# Data Loading #######################################
	train, test = load_data_set("./data/fake_or_real_news.csv")

	train = one_hot(train, 'label')
	test = one_hot(test, 'label')

	print(train.shape)
	print(test.shape)
	print(train.head())

	print('Fake news percentage is {}.'.format(len(train[train['y'] ==1])/len(train)))
	
	################################## Modeling ##########################################

	BASE_EXPORT_DIR = os.getcwd() + '/tmp/'

	embedded_text_feature_column = hub.text_embedding_column(
	    key="text", 
	    module_spec="https://tfhub.dev/google/nnlm-en-dim128/1")

	# Transform Data to TF data type

	train_input_fn = tf.estimator.inputs.pandas_input_fn(
		train, train['y'], num_epochs=None, shuffle=True)

	predict_train_input_fn = tf.estimator.inputs.pandas_input_fn(
	    train, train['y'], shuffle=False)

	predict_test_input_fn = tf.estimator.inputs.pandas_input_fn(
	    test, test['y'], shuffle=False)


	estimator = tf.estimator.DNNClassifier(
	    hidden_units=[500, 100],
	    feature_columns=[embedded_text_feature_column],
	    n_classes=2,
	    optimizer=tf.train.AdagradOptimizer(learning_rate=0.003),
	    model_dir=BASE_EXPORT_DIR)

	# Train model

	estimator.train(input_fn=train_input_fn, steps=1000)

	# Evalute model and get accuracy

	train_eval_result = estimator.evaluate(input_fn=predict_train_input_fn)
	test_eval_result = estimator.evaluate(input_fn=predict_test_input_fn)

	print("Training set accuracy: {accuracy}".format(**train_eval_result))
	print("Test set accuracy: {accuracy}".format(**test_eval_result))

	print(estimator.evaluate(input_fn=predict_test_input_fn)["accuracy_baseline"])
	
	################################confusion matrix######################################

	LABELS = [
	    "FAKE", "REAL"
	]

	# Create a confusion matrix on training data.

	with tf.Graph().as_default():
	  cm = tf.confusion_matrix(train["y"], 
	                           get_predictions(estimator, predict_train_input_fn))
	  with tf.Session() as session:
	    cm_out = session.run(cm)

	# Normalize the confusion matrix so that each row sums to 1.
	
	cm_out = cm_out.astype(float) / cm_out.sum(axis=1)[:, np.newaxis]

	sns.heatmap(cm_out, annot=True, xticklabels=LABELS, yticklabels=LABELS)
	plt.xlabel("Predicted")
	plt.ylabel("True")
	plt.show()