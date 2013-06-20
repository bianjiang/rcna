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
from misc.utils import root_folder, load_network_for, save_to_R
from network_analysis.networks import GrantResearcherNetwork
import scipy.stats

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
hdlr = logging.FileHandler('./powerlaw_degree_distribution.2.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)

def get_data(budgetYears):
	network = load_network_for(budgetYears)

	wg = network.g.copy()

	#wg = GrantResearcherNetwork.largest_component(wg)

	degree = np.array(wg.degree(), dtype=np.int)

	strength = np.array(wg.strength(loops=False,weights=wg.es['weight']), dtype=np.int)

	return wg, degree, strength


def powerlaw_fit_p_value(budgetYears):	

	logger.info("================================================================")
	logger.info(budgetYears)
	wg, degree, strength = get_data(budgetYears)


	from network_analysis.powerlaw import plpva
	import powerlaw

	
	fit = powerlaw.Fit(degree, discrete=True)
	logger.info("test degree powerlaw distribution p-value; alpha: %f; xmin: %f; sigma: %f, D: %f"%(fit.power_law.alpha, fit.power_law.xmin, fit.power_law.sigma, fit.power_law.D))

	p, gof = plpva.plpva(degree,fit.power_law.xmin)

	logger.info("p: %f; good-of-fitness: %f"%(p, gof))

	fit = powerlaw.Fit(strength, discrete=True)
	logger.info("test strength powerlaw distribution p-value; alpha: %f; xmin: %f; sigma: %f, D: %f"%(fit.power_law.alpha, fit.power_law.xmin, fit.power_law.sigma, fit.power_law.D))

	p, gof = plpva.plpva(strength, fit.power_law.xmin)

	logger.info("p: %f; good-of-fitness: %f"%(p, gof))



if __name__ == '__main__':

	powerlaw_fit_p_value(range(2006,2010))
	powerlaw_fit_p_value(range(2010,2013))

