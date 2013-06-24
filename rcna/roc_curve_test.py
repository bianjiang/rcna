#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Social Network Analysis of the UAMS's CTSA grant
grant_data_statistics.py

'''

__appname__ = 'Research Collaboration Social Network Analysis'
__author__  = 'Jiang Bian'
__version__ = '0.0.1'
__license__ = 'MIT'


import logging
import numpy as np
from misc.utils import root_folder
import network_analysis.prediction.rocarea as roc
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def plot_auc(startBudgetYear,endBudgetYear):
	

	filename = '%s/result/%s-%s.per_network.roc.samples.npy'%(root_folder(),startBudgetYear, endBudgetYear)

	roc_samples = np.load(filename)

	logger.info(len(roc_samples))

	labels = []
	scores = []
	for k, label, score in roc_samples:
		labels.append(np.float(label))
		scores.append(np.float(score))

	logger.info(scores)

	quit()

	area, [ax, lines] = roc.roc_curve(labels=np.array(labels),scores=np.array(scores))

	return area, [ax, lines]

def test():
	plot_auc(2006, 2009)
	plot_auc(2010, 2012)

	#logger.info(area)

	plt.show()


if __name__ == '__main__':
	test()


