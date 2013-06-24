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

# we are assuming all nodes in the network are connected (there is really no meaning for average path length for disconnected network)
# in the paper we analyze the largest component
def average_shortest_path_length(g):

	# ap = 0.0
	# cnt = 0
	# for v in g.shortest_paths(mode=igraph.ALL):
	# 	ap += float(sum(v))/(len(v) - 1)
		
	# return float(ap)/len(g.vs)
	return g.average_path_length(directed = False, unconn=False)

def clustering_coefficient(g):
	# use Watts and Strogatz definition of clustering coefficient
	return g.transitivity_avglocal_undirected(mode='zero')

# ER graph doesn't have weights... (this might be a nice project to see what if we consider weights, (allow the same edge get picked again))
def smallworldness_measure(g, rg):


	C_g = clustering_coefficient(g)
	C_r = clustering_coefficient(rg)

	L_g = average_shortest_path_length(g) #average_shortest_path_length(g)
	L_r = average_shortest_path_length(rg)

	gamma_ = C_g / C_r 
	lambda_ = L_g / L_r 

	return gamma_ / lambda_


# in smallworldness, we don't consider weight (as there is no method to generate weighted ER graph (you can have a process where you allow multiple edges between the same two nodes, but the statistical properties of this kind of network is unknown, and the affects of the smallworldness property is unknown) )
def smallworldness(network, rep = 1000):

	g = network.g.copy()
	#logger.info(g.summary())
	# there is no point to consider a disconnected graph ( the average path length means nothing)
	g = ResearchCollaborationNetwork.largest_component(g)
	
	n = len(g.vs)
	m = len(g.es)

	p = float(m) * 2 /(n*(n-1))

	# sharp threshold: define the connectedness of a ER graph http://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93R%C3%A9nyi_model
	c = float((np.exp(1) + 1)) * np.log(n) / n

	logger.info("Small-world-ness measure: %d iterations; Erdos_Renyi: p = %f (%d/%d), n  = %d, np = %f, (1 + e) * (ln n / n) = %f"%(rep, p, m, (n*(n-1))/2, n, n * p,  c))
	
	ss = []

	for bb in range(rep):
		rg = igraph.Graph.Erdos_Renyi(n, p, directed = False, loops = False)

		s = smallworldness_measure(g, rg)

		ss.append(s)

	mean_s = np.mean(ss)

	return mean_s, ss


if __name__ == '__main__':

	network = load_network_for(range(2006,2010))

	s, ss = smallworldness(network, rep = 1000)

	logger.info("Small-world-ness (2006 - 2009): %f"%s)


	network = load_network_for(range(2010,2013))

	s, ss = smallworldness(network, rep = 1000)

	logger.info("Small-world-ness (2010 - 2013): %f"%s)

	