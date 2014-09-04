#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Social Network Analysis of the UAMS's CTSA grant
centrality_leaders.py
this is a centrality based leader identification methods...
measures various centralities of the network, and range nodes based on its centrality values
however, various cetnrality measures gives different ranking orders,
so we use rank_aggregation to  identify the most popular choices in an election, where each centrality measure can be consider as a ballot 
'''

__appname__ = 'Research Collaboration Social Network Analysis'
__author__  = 'Jiang Bian'
__version__ = '0.0.1'
__license__ = 'MIT'

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

import igraph
import numpy as np
import network_analysis.centrality_leaders.rank_aggregation as rg

def centrality_leaders(g, k = None):
	'''
	g is the igraph object
	k picks the top k candidates from each measures... the problem is its computationally infeasible to get the full list ranked
	'''
	weights_as_cost = [ 1/weight for weight in g.es['weight']]

	# 1. degree centrality
	#degrees = g.degree() # higher is better
	degrees = g.strength(weights='weight')
	# 2. betweennesses centrality
	betweennesses = g.betweenness(weights=weights_as_cost, directed = False) # higher is better

	# 3. closeness centrality
	closenesses = g.closeness(weights=weights_as_cost) # higher is better

	# 4. eigenvector_centrality
	evcents = g.evcent(weights=weights_as_cost,directed = False) # which one?

	if k == None:
		k = len(g.vs)

	degrees_topK = rg.sorted_keys(degrees)[0:k]
	betweennesses_topK = rg.sorted_keys(betweennesses)[0:k]
	closeness_topK = rg.sorted_keys(closenesses)[0:k]
	evcent_topK = rg.sorted_keys(evcents)[0:k]

	logger.info('degrees_top10: %s'%degrees_topK[:10])
	logger.info('betweennesses_top10: %s'%betweennesses_topK[:10])
	logger.info('closeness_top10: %s'%closeness_topK[:10])
	logger.info('evcent_top10: %s'%evcent_topK[:10])

	tops = list(set(degrees_topK + betweennesses_topK + closeness_topK + evcent_topK)) # just to get a unique list

	rankBallots = rg.RankBallots(tops)

	#logger.info('final candidates list: %s'%rankBallots.candidates)

	rankBallots.add_ballot(np.array(degrees)[tops]) # higher degree value is better

	rankBallots.add_ballot(np.array(betweennesses)[tops]) # higher is better

	rankBallots.add_ballot(np.array(closenesses)[tops]) # higher is better

	rankBallots.add_ballot(np.array(evcents)[tops]) # higher is beter

	return rankBallots.candidates, rankBallots.ranking()

