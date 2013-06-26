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

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# data from 2010 - 2012 is our reference network to identify ctsa investigators

refNetwork = load_network_for(range(2010,2013))
refG = refNetwork.g.copy()

def set_category_by_is_ctsa(g, refG = None):
	for node in g.vs:
		if refG == None:
			node['category'] = node['ctsa']
		else:
			f = refG.vs.select(name_eq = node['name'])
			
			if len(f) > 0:
				#logger.info(f[0]['name'])
				node['category'] = f[0]['ctsa']
			else:
				node['category'] = 0.0

	return g

def average_strength(g, category):

	nodes = g.vs.select(category_eq = category)

	s = 0.0

	strengths = g.strength(weights='weight')

	i = []

	for node in nodes:
		i.append(node.index)

	return sum(np.array(strengths)[i])/len(i)

def average_strength_for(budgetYears):

	logger.info(budgetYears)

	network = load_network_for(budgetYears)
	g = network.g.copy()

	# pick the largest component of the network, the subgraph without any isolated nodes (nodes that are not connected to any other nodes)
	g = ResearchCollaborationNetwork.largest_component(g)

	g = set_category_by_is_ctsa(g, refG)

	logger.info('ctsa: %0.2f'%average_strength(g, 1.0))
	logger.info('non-ctsa: %0.2f'%average_strength(g, 0.0))



def average_shortest_path(g, weights = None, source = None, target = None):

	nodes = g.vs.select(category_eq = source)

	# if no target, it's all nodes
	if target == None:
		otherNodes = None
	else:
		otherNodes = g.vs.select(category_eq = target)

	cap = 0.0
	shortest_paths = g.shortest_paths(nodes, otherNodes, weights=weights, mode=igraph.ALL)
	for v in shortest_paths:
		cap += float(sum(np.array(v, dtype=np.float)))/ (len(v) - 1) #discount self reference

	return cap/len(shortest_paths)

def average_shortest_path_for(budgetYears):

	logger.info(budgetYears)

	network = load_network_for(budgetYears)
	g = network.g.copy()

	# pick the largest component of the network, the subgraph without any isolated nodes (nodes that are not connected to any other nodes)
	g = ResearchCollaborationNetwork.largest_component(g)

	g = set_category_by_is_ctsa(g, refG)

	weights = [ 1/weight for weight in g.es['weight']]

	logger.info('within non-CTSA investigators: %0.3f'%average_shortest_path(g, weights = weights, source = 0.0, target = 0.0))
	logger.info('within CTSA investigators: %0.3f'%average_shortest_path(g, weights = weights, source=1.0, target = 1.0))
	#logger.info('from CTSA to non-CTSA: %0.3f'%average_shortest_path(g, weights = weights, source = 1.0, target = 0.0))
	logger.info('from non-CTSA to all: %0.3f'%average_shortest_path(g, weights = weights, source = 0.0, target = None))
	logger.info('from CTSA to all: %0.3f'%average_shortest_path(g, weights = weights, source = 1.0, target = None))


if __name__ == '__main__':	
	
	logger.info("strength")
	
	average_strength_for(range(2006,2010))
	average_strength_for(range(2010,2013))

	logger.info('average_shortest_path')

	average_shortest_path_for(range(2006,2010))
	average_shortest_path_for(range(2010,2013))




