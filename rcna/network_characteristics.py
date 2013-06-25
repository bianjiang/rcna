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

def num_of_isolated_components(g):
	gs = g.decompose(mode=igraph.STRONG)
	for g in gs:
		logger.info(g.summary())

	quit()
	return len(gs)


def diversity(g, weights=None, category='department'):
	'''
	Basically, this calculates the average_path_length from one category of nodes to all other categories of nodes.
	A basic example is to use department as a category, and calculate this as evidence of cross-disciplinary collaborations. 
	'''

	categoryCodes = set(g.vs[category])

	g.vs['category'] = g.vs[category]
		
	average_path_length = 0.0
	for c in categoryCodes:

		nodes = g.vs.select(category_eq = c)
		otherNodes = g.vs.select(category_ne = c)

		cap = 0.0
		cnt = 0
		for node in nodes:

			shortest_paths = g.shortest_paths(node, otherNodes, weights='weight', mode=igraph.ALL)

			ap = [pl for pl in shortest_paths[0] if np.isfinite(pl)]


			if len(ap) > 0:
				cap += sum(ap)/(len(ap) - 1)
			else:
				continue # if no shortest path, ignore this node, shouldn't count it

			cnt += 1


		average_path_length += cap/cnt

	return len(categoryCodes)/average_path_length

def average_number_of_new_edges(cg, pg):
	'''
		This counts number of new edges of each node comparing to the previous year
		for aggregated graphs, it compares to the previous aggregated graph
	'''

	# loop through the current graph and find the corresponding node in the previous graph
	found_cnt = 0
	new_edges = 0.0 # counting weights
	for v in cg.vs:

		found = pg.vs.select(name_eq = v['name'])

		for f in found:
			found_cnt += 1
			new_edges += v.strength(weights='weight') - f.strength(weights='weight')

	return new_edges/found_cnt

def average_shortest_path_length_weighted(g, weights=None):

	cap = 0.0
	shortest_paths = g.shortest_paths(weights=weights, mode=igraph.ALL)

	for v in shortest_paths:
		cap += float(sum(np.array(v, dtype=np.float)))/ (len(v) - 1) #discount self reference

	return cap/len(shortest_paths)

def network_characteristics(budgetYears):

	logger.info("================================================================")
	logger.info(budgetYears)

	network = load_network_for(budgetYears)

	g = network.g.copy()

	# simplified network is the one without any isolated nodes (nodes that are not connected to any other nodes)
	g = ResearchCollaborationNetwork.simplify(g)

	logger.info('# of nodes: %d'%(len(g.vs)))

	logger.info('# of edges: %d'%(len(g.es)))

	logger.info('density: %.3f'%(g.density()))

	new_edges = 0.0

	# 2006 is the baseline
	if budgetYears[0] > 2006:
		if budgetYears[0]  == 2010 and budgetYears[-1] == 2012:
			pBudgetYears = range(2006,2010)
		else:
			pBudgetYears = np.array(budgetYears) - 1

		pNetwork = load_network_for(pBudgetYears)
		pg = pNetwork.g.copy()
		pg = ResearchCollaborationNetwork.simplify(pg)

		new_edges = average_number_of_new_edges(g, pg)
	logger.info('average number of new edges: %.3f'%new_edges)

	logger.info('# of isolated components: %d'%(num_of_isolated_components(g)))


	# only the largest component, mainly because shortest path length is rather arbitrary on graphs with isolated components, which our RCNs are.
	g = ResearchCollaborationNetwork.largest_component(g)
	weights = g.es['weight']
	r_weights = [ 1/float(weight) for weight in g.es['weight']]
	no_weigths = [ 1 for weight in g.es['weight']]

	logger.info('# of nodes (largest component): %d'%(len(g.vs)))

	logger.info('# of edges (largest component): %d'%(len(g.es)))

	C_g = g.transitivity_avglocal_undirected(mode='zero', weights=no_weigths)
	logger.info('C_g (weights = None): %.3f'%C_g)

	C_wg = g.transitivity_avglocal_undirected(mode='zero', weights=weights)
	logger.info('C_g (weights = number of collaborations): %.3f'%C_wg)

	C_tg = g.transitivity_undirected(mode='zero')
	logger.info('C_g (triplets definition): %.3f'%C_tg)

	L_g = average_shortest_path_length_weighted(g, no_weigths)
	logger.info("L_g (weights = 1): %.3f"%L_g)

	L_wg = average_shortest_path_length_weighted(g, r_weights)
	logger.info("L_g (weights = 1/weights): %.3f"%L_wg)

	D_wg = diversity(g, r_weights)
	logger.info("D_g (weights = 1/weights): %.3f"%D_wg)


if __name__ == '__main__':

	for budgetYear in range(2006, 2010):
		network_characteristics(range(budgetYear,budgetYear+1))

	network_characteristics(range(2006,2010))

	for budgetYear in range(2010, 2013):
		network_characteristics(range(budgetYear,budgetYear+1))

	network_characteristics(range(2010,2013))

	network_characteristics(range(2006,2013))
