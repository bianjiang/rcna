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
import network_analysis.link_prediction.benchmark.rocarea as roc
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def plot_auc(startBudgetYear,endBudgetYear, task, ax, color):
	

	filename = '%s/data/%s-%s.%s.roc.samples.npy'%(root_folder(),startBudgetYear, endBudgetYear, task)

	roc_samples = np.load(filename)

	labels = []
	scores = []
	for k, label, score in roc_samples:
		labels.append(np.float(label))
		scores.append(np.float(score))

	area, [ax, lines] = roc.roc_curve(labels=np.array(labels),scores=np.array(scores), ax=ax, linewidth=1.5, color=color)

	return area, [ax, lines]

def test():
	from matplotlib import rc
	rc('text', usetex=False)
	rc('font', family='serif')

	fig = plt.figure(figsize=(8,16))
	ax = fig.add_subplot(1,2,1)

	task = 'per_user'
	roc.roc_curve_init(ax)

	area, [ax, b] = plot_auc(2006, 2009, task, ax, 'b')
	area, [ax, g] = plot_auc(2010, 2012, task, ax, 'g')
	area, [ax, r] = plot_auc(2006, 2012, task, ax, 'r')

	ax.set_title('Per-user Model')
	
	

	#f.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=.3, hspace=.2)
	#plt.legend(loc=4)
	
	#plt.savefig('%s/figures/%s-roc-curve.eps'%(root_folder(), task),bbox_inches='tight', dpi=600)

	#plt.close()
	task = 'per_network'
	ax = fig.add_subplot(1,2,2)
	roc.roc_curve_init(ax)

	area, [ax, b] = plot_auc(2006, 2009, task, ax, 'b')
	area, [ax, g] = plot_auc(2010, 2012, task, ax, 'g')
	area, [ax, r] = plot_auc(2006, 2012, task, ax, 'r')

	ax.set_title('Per-network Model')	
	
	fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=.3, hspace=.2)
	#plt.figlegend((b, g, r), ('RCN (2006 - 2009)',  'RCN (2010 - 2012)',  'RCN (2006 - 2012)'), 'center')
	#plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.05), ncol=5, fancybox=True)
	plt.legend((b, g, r), ('RCN (2006 - 2009)',  'RCN (2010 - 2012)',  'RCN (2006 - 2012)'), bbox_to_anchor=(-0.15,-0.4),loc='center', prop={'size':12}) 

	plt.savefig('%s/figures/roc-curve.eps'%(root_folder()),bbox_inches='tight', dpi=600)

if __name__ == '__main__':
	test()


