#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Social Network Analysis of the UAMS's CTSA grant
convert_to_d3_json.py

'''

__appname__ = 'Research Collaboration Social Network Analysis'
__author__ = 'Jiang Bian'
__version__ = '0.0.1'
__license__ = 'MIT'


import logging
import os
import csv
import igraph
import numpy as np
from misc.utils import root_folder
from network_analysis.utils import load_network_for
from network_analysis.networks import ResearchCollaborationNetwork


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


def network_to_d3(budgetYears):

    network = load_network_for(budgetYears)
    #network = ResearchCollaborationNetwork.read(budgetYears)
    startBudgetYear = budgetYears[0]
    endBudgetYear = budgetYears[-1]
    filename = '%s/data/networks/%s-%s-complete.json' % (root_folder(),
                                                         startBudgetYear, endBudgetYear)
    ResearchCollaborationNetwork.d3(network.g, filename)

    # remove isolated nodes
    g = network.g.copy()
    g = ResearchCollaborationNetwork.simplify(g)
    filename = '%s/data/networks/%s-%s.json' % (root_folder(),
                                                startBudgetYear, endBudgetYear)
    ResearchCollaborationNetwork.d3(g, filename)

    # only the largest components
    g = network.g.copy()
    g = ResearchCollaborationNetwork.largest_component(g)
    filename = '%s/data/networks/%s-%s-largest-component.json' % (root_folder(),
                                                                  startBudgetYear, endBudgetYear)
    ResearchCollaborationNetwork.d3(g, filename)


if __name__ == '__main__':

    # generate network for each budget year
    for s in range(2006, 2013):
        budgetYears = range(s, s + 1)
        network_to_d3(budgetYears)

    # 2006 - 2009
    network_to_d3(range(2006, 2010))

    # 2010 - 2012
    network_to_d3(range(2010, 2013))

    # 2006 - 2013
    network_to_d3(range(2006, 2013))