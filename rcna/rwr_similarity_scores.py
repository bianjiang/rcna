#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Social Network Analysis of the UAMS's CTSA grant
link_prediction_test.py

'''

__appname__ = 'Research Collaboration Social Network Analysis'
__author__ = 'Jiang Bian'
__version__ = '0.0.1'
__license__ = 'MIT'

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

import igraph
import json
import numpy as np

from misc.utils import root_folder
from network_analysis.utils import load_network_for
from network_analysis.networks import ResearchCollaborationNetwork
import network_analysis.link_prediction.pagerank as pgrank


def rwr_scores(budgetYears):
    startBudgetYear = budgetYears[0]
    endBudgetYear = budgetYears[-1]

    logger.info('---------------- %s-%s -------------------' %
                (startBudgetYear, endBudgetYear))

    network = load_network_for(budgetYears)

    #network = ResearchCollaborationNetwork.read(budgetYears)

    g = network.g.copy()
    ResearchCollaborationNetwork.simplify(g)

    logger.info(g.summary())

    adj = np.array(g.get_adjacency(igraph.GET_ADJACENCY_BOTH).data)

    links = []
    m = len(g.vs)
    for i in range(m):
        for j in range(i + 1, m):
            key = '%d,%d' % (i, j)
            links.append(key)

    rwr_scores = pgrank.rwr_score(g, links)

    rwrs = {}
    for link, score in rwr_scores.items():
        v = link.split(',')
        v1 = int(v[0])
        v2 = int(v[1])

        key = '%s,%s' % (g.vs[v1]['name'], g.vs[v2]['name'])
        if(float(score) > 0.001 and adj[v1][v2] == 0):
            rwrs[key] = score

    filename = '%s/data/networks/%d-%d-rwr.json' % (root_folder(),
                                                    startBudgetYear, endBudgetYear)

    with open(filename, 'w') as out:
        json.dump(rwrs, out)


if __name__ == '__main__':

    for budgetYear in range(2006, 2013):
        rwr_scores(range(budgetYear, budgetYear + 1))

    rwr_scores(range(2006, 2010))
    rwr_scores(range(2010, 2013))
    rwr_scores(range(2006, 2013))
