#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Social Network Analysis of the UAMS's CTSA grant"""
'''
	utils.py for network_analysis
	utility functions:
		k-fold cross validation from http://code.activestate.com/recipes/521906-k-fold-cross-validation-partition/
''' 
__appname__ = "Research Collaboration Social Network Analysis"
__author__  = "Jiang Bian"
__version__ = "0.0.1"
__license__ = "MIT"

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

import numpy as np

from random import shuffle

def k_fold_cross_validation(items, k, randomize=True):
	"""
	Generates K (training, validation) pairs from the items in X.

	Each pair is a partition of X, where validation is an iterable
	of length len(X)/K. So each training iterable is of length (K-1)*len(X)/K.

	If randomise is true, a copy of X is shuffled before partitioning,
	otherwise its order is preserved in training and validation.
	"""
	if randomize:
		items = list(items)
		shuffle(items)

	slices = [items[i::k] for i in xrange(k)]

	for i in xrange(k):
		validation = slices[i]
		training = [item
					for s in slices if s is not validation
					for item in s]
		yield training, validation

if __name__ == '__main__':
	items = range(97)
	for training, validation in k_fold_cross_validation(items, 7):
		for item in items:
			logger.info ((item in training) ^ (item in validation))



