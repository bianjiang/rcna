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

	fit = powerlaw.Fit(X, discrete=True)
	logger.info(fit.power_law.alpha)
	logger.info(fit.power_law.xmin)
	logger.info(fit.power_law.sigma)
	logger.info(fit.power_law.D)
	logger.info(fit.supported_distributions)

	fig2 = fit.plot_pdf(color='b', linewidth=2)
	fit.power_law.plot_pdf(color='g', linestyle='--', ax=fig2)
	#fit.lognormal.plot_pdf(color='b', linestyle='--', ax=fig2)
	#fit.exponential.plot_pdf(color='r', linestyle='--', ax=fig2)
	#fit.truncated_power_law.plot_pdf(color='y', linestyle='--', ax=fig2)
	#logger.info(fit.distribution_compare('power_law', 'exponential'))
	#logger.info(fit.distribution_compare('power_law', 'lognormal'))
	#logger.info(fit.distribution_compare('power_law', 'truncated_power_law'))

	plt.show()

n_data = 2
n_graphs = 4

def plot_basics(data, data_inst, fig, units):
	from powerlaw import plot_pdf, Fit, pdf
	annotate_coord = (-.4, .95)
	ax1 = fig.add_subplot(n_graphs,n_data,data_inst)
	plot_pdf(data[data>0], ax=ax1, linear_bins=True, color='r', linewidth=.5)
	x, y = pdf(data, linear_bins=True)
	ind = y>0
	y = y[ind]
	x = x[:-1]
	x = x[ind]
	ax1.scatter(x, y, color='r', s=.5)
	plot_pdf(data[data>0], ax=ax1, color='b', linewidth=2)
	from pylab import setp
	setp( ax1.get_xticklabels(), visible=False)
	#ax1.set_xticks(ax1.get_xticks()[::2])
	ax1.set_yticks(ax1.get_yticks()[::2])
	locs,labels = plt.yticks()
	#yticks(locs, map(lambda x: "%.0f" % x, log10(locs)))
	if data_inst==1:
		ax1.annotate("A", annotate_coord, xycoords="axes fraction", fontsize=14)

	
	from mpl_toolkits.axes_grid.inset_locator import inset_axes
	ax1in = inset_axes(ax1, width = "30%", height = "30%", loc=3)
	ax1in.hist(data, normed=True, color='b')
	ax1in.set_xticks([])
	ax1in.set_yticks([])

	
	ax2 = fig.add_subplot(n_graphs,n_data,n_data+data_inst, sharex=ax1)
	plot_pdf(data, ax=ax2, color='b', linewidth=2)
	fit = Fit(data, xmin=1, discrete=True)
	fit.power_law.plot_pdf(ax=ax2, linestyle=':', color='g')
	p = fit.power_law.pdf()
	#ax2.set_ylim(min(p), max(p))
	ax2.set_xlim(ax1.get_xlim())
	
	fit = Fit(data, discrete=True)
	fit.power_law.plot_pdf(ax=ax2, linestyle='--', color='g')
	from pylab import setp
	setp( ax2.get_xticklabels(), visible=False)
	#ax2.set_xticks(ax2.get_xticks()[::2])
	if ax2.get_ylim()[1] >1:
		ax2.set_ylim(ax2.get_ylim()[0], 1)
	
	ax2.set_yticks(ax2.get_yticks()[::2])
	#locs,labels = yticks()
	#yticks(locs, map(lambda x: "%.0f" % x, log10(locs)))
	if data_inst==1:
	   ax2.annotate("B", annotate_coord, xycoords="axes fraction", fontsize=14)        
	   ax2.set_ylabel(r"$p(X)$")# (10^n)")
		
	ax3 = fig.add_subplot(n_graphs,n_data,n_data*2+data_inst)#, sharex=ax1)#, sharey=ax2)
	fit.power_law.plot_pdf(ax=ax3, linestyle='--', color='g')
	fit.exponential.plot_pdf(ax=ax3, linestyle='--', color='r')
	fit.plot_pdf(ax=ax3, color='b', linewidth=2)
	
	#p = fit.power_law.pdf()
	ax3.set_ylim(ax2.get_ylim())
	ax3.set_yticks(ax3.get_yticks()[::2])
	ax3.set_xlim(ax1.get_xlim())
	
	#locs,labels = yticks()
	#yticks(locs, map(lambda x: "%.0f" % x, log10(locs)))
	if data_inst==1:
		ax3.annotate("C", annotate_coord, xycoords="axes fraction", fontsize=14)

	#if ax2.get_xlim()!=ax3.get_xlim():
	#    zoom_effect01(ax2, ax3, ax3.get_xlim()[0], ax3.get_xlim()[1])
	ax3.set_xlabel(units)

if __name__ == '__main__':
	import matplotlib.pyplot as plt

	budgetYears = range(2006,2013)
	
	logger.info("================================================================")
	logger.info(budgetYears)

	wg_rcn_2006_2012, degree_rcn_2006_2012, strength_rcn_2006_2012 = get_data(budgetYears)

	powerlaw_fit_p_value(degree_rcn_2006_2012)

	powerlaw_fit_p_value(strength_rcn_2006_2012)
	quit()

	budgetYears = range(2006,2010)
	
	logger.info("================================================================")
	logger.info(budgetYears)

	wg_rcn_2009_2010, degree_rcn_2009_2010, strength_rcn_2009_2010 = get_data(budgetYears)


	budgetYears = range(2010,2013)
	
	logger.info("================================================================")
	logger.info(budgetYears)

	wg_rcn_2010_2013, degree_rcn_2010_2013, strength_rcn_2010_2013 = get_data(budgetYears)

	f = plt.figure(figsize=(8,11))
	data = degree_rcn_2009_2010
	data_inst = 1
	units = 'RCN 2009 - 2010'

	plot_basics(data, data_inst, f, units)

	data_inst = 2
	data = degree_rcn_2010_2013
	units = 'RCN 2010 - 2012'
	plot_basics(data, data_inst, f, units)

	f.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=.3, hspace=.2)
	f.savefig('%s/figures/powerlaw_degree_distribution.eps'%(root_folder()), bbox_inches='tight')
	#plt.show()
	#plot_powerlaw(degree)
	#powerlaw_fit_p_value(degree)

