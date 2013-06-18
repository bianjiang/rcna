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
hdlr = logging.FileHandler('./powerlaw_degree_distribution.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)

def get_data(budgetYears):
	network = load_network_for(range(2006,2010))

	wg = network.g.copy()
	GrantResearcherNetwork.simplify(wg)

	degree = np.array(wg.degree(), dtype=np.int)

	strength = np.array(wg.strength(loops=False,weights=wg.es['weight']), dtype=np.int)

	return wg, degree, strength


def powerlaw_fit_p_value(budgetYears):	

	wg, degree, strength = get_data(budgetYears)

	wg = GrantResearcherNetwork.largest_component(wg)
	logger.info(wg.summary())


	#save_to_R(degree, '%s/data/degree'%(root_folder()))
	#save_to_R(strength, '%s/data/strength'%(root_folder()))

	from network_analysis.powerlaw import plpva
	import powerlaw

	logger.info("degree p-value")
	fit = powerlaw.Fit(degree, discrete=True)
	logger.info(fit.power_law.alpha)
	logger.info(fit.power_law.xmin)
	logger.info(fit.power_law.sigma)
	logger.info(fit.power_law.D)

	logger.info(plpva.plpva(degree,fit.power_law.xmin))

	logger.info("strength p-value")
	fit = powerlaw.Fit(strength, discrete=True)
	logger.info(fit.power_law.alpha)
	logger.info(fit.power_law.xmin)
	logger.info(fit.power_law.sigma)
	logger.info(fit.power_law.D)

	logger.info(plpva.plpva(strength, fit.power_law.xmin))




if __name__ == '__main__':

	powerlaw_fit_p_value(range(2010,2013))

