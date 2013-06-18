#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Social Network Analysis of the UAMS's CTSA grant"""
'''
	utils.py for grant_data
''' 
__appname__ = "Research Collaboration Social Network Analysis"
__author__  = "Jiang Bian"
__version__ = "0.0.1"
__license__ = "MIT"

import logging
import os
import numpy as np
from network_analysis.networks import GrantResearcherNetwork

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def root_folder():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

def save_to_R(X, filename):
	import numpy as np
	from rpy2.robjects import r
	import pandas.rpy.common as com
	from pandas import DataFrame
	df = DataFrame(np.array(X))
	df = com.convert_to_r_dataframe(df)
	r.assign("X", df)
	r("save(X, file='%s.gz', compress=TRUE)"%(filename))

def load_network_for(budgetYears):

	startBudgetYear = budgetYears[0]
	endBudgetYear = budgetYears[-1]
	
	filename = '%s/data/networks/%d-%d.graphml'%(root_folder(),startBudgetYear, endBudgetYear)
	network = GrantResearcherNetwork.read(filename)

	return network