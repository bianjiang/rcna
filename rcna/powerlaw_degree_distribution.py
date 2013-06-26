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
import os
import igraph
import numpy as np
from misc.utils import root_folder
from network_analysis.utils import load_network_for
from network_analysis.networks import ResearchCollaborationNetwork
import scipy.stats

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
#hdlr = logging.FileHandler('./powerlaw_degree_distribution.2.log')
#formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
#hdlr.setFormatter(formatter)
#logger.addHandler(hdlr)


import pylab
pylab.rcParams['xtick.major.pad']='8'
pylab.rcParams['ytick.major.pad']='8'
#import matplotlib.gridspec as gridspec
from matplotlib import rc
rc('text', usetex=False)
rc('font', family='serif')


def get_data(budgetYears):
	network = load_network_for(budgetYears)

	wg = network.g.copy()

	wg = ResearchCollaborationNetwork.simplify(wg)

	degree = np.array(wg.degree(), dtype=np.int)

	strength = np.array(wg.strength(loops=False,weights=wg.es['weight']), dtype=np.int)

	return wg, degree, strength


def powerlaw_fit_p_value(X):

	from network_analysis.powerlaw import plpva
	import powerlaw

	
	fit = powerlaw.Fit(X, discrete=True)
	logger.info("test X powerlaw distribution p-value; alpha: %f; xmin: %f; sigma: %f, D: %f"%(fit.power_law.alpha, fit.power_law.xmin, fit.power_law.sigma, fit.power_law.D))

	p, gof = plpva.plpva(X,fit.power_law.xmin)

	logger.info("p: %f; good-of-fitness: %f"%(p, gof))

	return p, gof
	

def plot_powerlaw(X):
	import powerlaw
	import matplotlib.pyplot as plt

	fig = plt.figure()
	ax = fig.add_subplot(111)

	powerlaw.plot_pdf(X, ax=ax, color='b', linewidth=2)

	fit = powerlaw.Fit(X, xmin=1, discrete=True)
	fit.power_law.plot_pdf(ax=ax, linestyle=':', color='g')

	fit = powerlaw.Fit(X, discrete=True)
	logger.info(fit.power_law.alpha)
	logger.info(fit.power_law.xmin)
	logger.info(fit.power_law.sigma)
	logger.info(fit.power_law.D)
	#logger.info(fit.supported_distributions)
	fit.power_law.plot_pdf(color='g', linestyle='--', ax=ax)
	fit.lognormal.plot_pdf(color='r', linestyle='--', ax=ax)

	
	
	#fit.exponential.plot_pdf(color='r', linestyle='--', ax=fig)
	#fit.truncated_power_law.plot_pdf(color='y', linestyle='--', ax=fig)
	#logger.info(fit.distribution_compare('power_law', 'exponential'))
	#logger.info(fit.distribution_compare('power_law', 'lognormal'))
	#logger.info(fit.distribution_compare('power_law', 'truncated_power_law'))

	plt.show()

	#f.savefig('%s/figures/powerlaw_degree_distribution.eps'%(root_folder()), bbox_inches='tight')

n_data = 3
n_graphs = 2
#
def plot_powerlaw_combined(data, data_inst, fig, units):
	from powerlaw import plot_pdf, Fit, pdf
	annotate_coord = (-.4, .95)
	ax1 = fig.add_subplot(n_graphs,n_data,data_inst)
	plot_pdf(data, ax=ax1, color='b', linewidth=2)
	
	fit = Fit(data, xmin=1, discrete=True)
	fit.power_law.plot_pdf(ax=ax1, linestyle=':', color='g')
	p = fit.power_law.pdf()

	fit = Fit(data, discrete=True)
	fit.power_law.plot_pdf(ax=ax1, linestyle='--', color='g')

	from pylab import setp
	setp( ax1.get_xticklabels(), visible=False)

	if data_inst==1:
	   ax1.annotate("A", annotate_coord, xycoords="axes fraction", fontsize=14)        
	   ax1.set_ylabel(r"$p(X)$")# (10^n)")

	ax2 = fig.add_subplot(n_graphs,n_data,n_data+data_inst)#, sharex=ax1)#, sharey=ax2)
	fit.power_law.plot_pdf(ax=ax2, linestyle='--', color='g')
	fit.exponential.plot_pdf(ax=ax2, linestyle='--', color='r')
	fit.plot_pdf(ax=ax2, color='b', linewidth=2)
	
	ax2.set_ylim(ax1.get_ylim())
	ax2.set_yticks(ax2.get_yticks()[::2])
	ax2.set_xlim(ax1.get_xlim())
	
	if data_inst==1:
		ax2.annotate("B", annotate_coord, xycoords="axes fraction", fontsize=14)

	ax2.set_xlabel(units)

# function used to generate the figure in the manuscript
def plot_all_combined():
	import matplotlib.pyplot as plt

	budgetYears = range(2006,2010)
	
	logger.info("================================================================")
	logger.info(budgetYears)

	wg_rcn_2006_2009, degree_rcn_2006_2009, strength_rcn_2006_2009 = get_data(budgetYears)


	budgetYears = range(2010,2013)
	
	logger.info("================================================================")
	logger.info(budgetYears)

	wg_rcn_2010_2012, degree_rcn_2010_2012, strength_rcn_2010_2012 = get_data(budgetYears)

	budgetYears = range(2006,2013)
	
	logger.info("================================================================")
	logger.info(budgetYears)

	wg_rcn_2006_2012, degree_rcn_2006_2012, strength_rcn_2006_2012 = get_data(budgetYears)

	f = plt.figure(figsize=(12,6))
	data = strength_rcn_2006_2009
	data_inst = 1
	units = 'RCN 2006 - 2009'
	plot_powerlaw_combined(data, data_inst, f, units)

	data_inst = 2
	data = strength_rcn_2010_2012
	units = 'RCN 2010 - 2012'
	plot_powerlaw_combined(data, data_inst, f, units)

	data_inst = 3
	data = strength_rcn_2006_2012
	units = 'RCN 2006 - 2012'
	plot_powerlaw_combined(data, data_inst, f, units)

	f.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=.3, hspace=.2)
	f.savefig('%s/figures/powerlaw_degree_distribution.eps'%(root_folder()), bbox_inches='tight')

def display_fitting(X):
	import powerlaw
	fit = powerlaw.Fit(X, discrete=True)
	logger.info('alpha: %.3f'%fit.power_law.alpha)
	logger.info('xmin: %.3f'%fit.power_law.xmin)
	logger.info('sigma: %.3f'%fit.power_law.sigma)
	logger.info('D: %.3f'%fit.power_law.D)

if __name__ == '__main__':

	budgetYears = range(2006,2010)
	wg_rcn_2006_2009, degree_rcn_2006_2009, strength_rcn_2006_2009 = get_data(budgetYears)

	logger.info("================================================================")
	logger.info(budgetYears)
	display_fitting(strength_rcn_2006_2009)


	budgetYears = range(2010,2013)
	wg_rcn_2010_2012, degree_rcn_2010_2012, strength_rcn_2010_2012 = get_data(budgetYears)

	logger.info("================================================================")
	logger.info(budgetYears)
	display_fitting(strength_rcn_2010_2012)

	budgetYears = range(2006,2013)
	wg_rcn_2006_2012, degree_rcn_2006_2012, strength_rcn_2006_2012 = get_data(budgetYears)

	logger.info("================================================================")
	logger.info(budgetYears)
	display_fitting(strength_rcn_2006_2012)

	#powerlaw_fit_p_value(degree)


