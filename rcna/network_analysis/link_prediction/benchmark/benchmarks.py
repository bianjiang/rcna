#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Social Network Analysis of the UAMS's CTSA grant"""
'''
	benchmarks.py for network_analysis
	benchmark functions - AUC and Precision (copied from https://github.com/benhamner/Metrics/blob/master/Python/ml_metrics/auc.py)
''' 
__appname__ = "Research Collaboration Social Network Analysis"
__author__  = "Jiang Bian"
__version__ = "0.0.1"
__license__ = "MIT"

import logging
import numpy as np

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def tied_rank(x):
	"""
	Computes the tied rank of elements in x.

	This function computes the tied rank of elements in x.

	Parameters
	----------
	x : list of numbers, numpy array

	Returns
	-------
	score : list of numbers
			The tied rank f each element in x

	"""
	sorted_x = sorted(zip(x,range(len(x))))
	r = [0 for k in x]
	cur_val = sorted_x[0][0]
	last_rank = 0
	for i in range(len(sorted_x)):
		if cur_val != sorted_x[i][0]:
			cur_val = sorted_x[i][0]
			for j in range(last_rank, i): 
				r[sorted_x[j][1]] = float(last_rank+1+i)/2.0
			last_rank = i
		if i==len(sorted_x)-1:
			for j in range(last_rank, i+1): 
				r[sorted_x[j][1]] = float(last_rank+i+2)/2.0
	return r

def auc(actual, posterior):
	"""
	Computes the area under the receiver-operater characteristic (AUC)

	This function computes the AUC error metric for binary classification.

	Parameters
	----------
	actual : list of binary numbers, numpy array
			 The ground truth value
	posterior : same type as actual
				Defines a ranking on the binary numbers, from most likely to
				be positive to least likely to be positive.

	Returns
	-------
	score : double
			The mean squared error between actual and posterior

	"""
	r = tied_rank(posterior)
	num_positive = len([0 for x in actual if x==1])
	num_negative = len(actual)-num_positive
	sum_positive = sum([r[i] for i in range(len(r)) if actual[i]==1])
	auc = ((sum_positive - num_positive*(num_positive+1)/2.0) /
		   (num_negative*num_positive))
	return auc

def apk(actual, predicted, k=10):
	"""
	Computes the average precision at k.

	This function computes the average prescision at k between two lists of
	items.

	Parameters
	----------
	actual : list
			 A list of elements that are to be predicted (order doesn't matter)
	predicted : list
				A list of predicted elements (order does matter)
	k : int, optional
		The maximum number of predicted elements

	Returns
	-------
	score : double
			The average precision at k over the input lists

	"""
	if len(predicted)>k:
		predicted = predicted[:k]

	score = 0.0
	num_hits = 0.0

	for i,p in enumerate(predicted):
		if p in actual and p not in predicted[:i]:
			num_hits += 1.0
			score += num_hits / (i+1.0)

	if not actual:
		return 1.0

	return score / min(len(actual), k)

def mapk(actual, predicted, k=10):
	"""
	Computes the mean average precision at k.

	This function computes the mean average prescision at k between two lists
	of lists of items.

	Parameters
	----------
	actual : list
			 A list of lists of elements that are to be predicted 
			 (order doesn't matter in the lists)
	predicted : list
				A list of lists of predicted elements
				(order matters in the lists)
	k : int, optional
		The maximum number of predicted elements

	Returns
	-------
	score : double
			The mean average precision at k over the input lists

	"""
	return np.mean([apk(a,p,k) for a,p in zip(actual, predicted)])