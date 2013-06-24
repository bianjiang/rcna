#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Social Network Analysis of the UAMS's CTSA grant"""
'''
	pagerank.py for network_analysis
	various pagerank algorithms specific for this project
''' 
__appname__ = "Research Collaboration Social Network Analysis"
__author__  = "Jiang Bian"
__version__ = "0.0.1"
__license__ = "MIT"

import logging
import math
import igraph
import numpy as np
from numpy import linalg as LA

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

'''
	p_{ij} = 1 / deg(i) // out-degree of i
    // row-stochastic and need to get P^{T} to get column-stochastic
'''
def adj_to_transition_matrix(adj):
	# square matrix
	m, _ = adj.shape	

	P = np.zeros((m, m))
	for i in range(m):
		row_total = float(adj[i].sum())
		
		for j in range(m):
			P[i,j] = adj[i,j] / float(row_total) if row_total != 0.0 else 0.0
		 
	return np.transpose(P)

def diff(r, rp):
	return np.sum(np.abs(r - rp))

### initial vector is the same as the personalized vector
def personalized_pagerank(g, alpha = 0.85, tolerance = 1 / math.pow(10, 5), max_iteration = math.pow(10,6), v = None):

	m = len(g.vs)

	v = np.ones(m) / float(m) if v is None else np.array(v) # if the personalized vector is None, then use uniform distribution

	if v.size != m:
		raise Exception('personalized vector v needs to be the same size of the number of nodes in the graph')
	#logger.info(g.attributes())
	

	edge_attribute = 'weight' if 'weight' in g.edge_attributes() else None
	# for undirected graph, the pagerank calculation treat an edge as two edges with directions, igraph.GET_ADJACENCY_BOTH is ignored if the graph is a directed graph
	# Note: g.get_adjacency() returns a igraph matrix
	adj = np.array(g.get_adjacency(igraph.GET_ADJACENCY_BOTH, attribute=edge_attribute).data)


	P = adj_to_transition_matrix(adj)

	#logger.info(P)

	r = v #np.ones(m) / float(m)
	rp = 0.0

	residue = float(1.0)

	Z = alpha * P

	max_ = max_iteration

	while max_ > 0 and diff(r, rp) > tolerance:

		rp = r

		z = Z.dot(r)

		beta = 1.0 - LA.norm(z, 1)

		r = z + beta * v # v is the personalized vector

	if diff(r, rp) > tolerance:
		raise Exception('fail to converge within %d iterations'%(max_iteration))

	return r

# this will gives a probability of any links in the graph
# basically, rwr_score = personalized_pagerank_{xy} + personalized_pagerank_{yx}
# see: http://arxiv.org/pdf/1010.0725v1.pdf p12 15) 
def rwr_score(g, candidates = [], alpha = 0.90, tolerance = 1 / math.pow(10, 5), max_iteration = math.pow(10,6)):

	directed = g.is_directed()
	personalized_pagerank_scores = {}

	nodes = []
	for link in candidates:
		v = link.split(',')
		v1 = int(v[0])
		v2 = int(v[1])

		nodes.append(v1)
		nodes.append(v2)

	progress = len(set(nodes))
	for node in set(nodes):
		reset_v = [0.0] * len(g.vs)
		reset_v[node] = 1.0

		personalized_pagerank_scores[node] = personalized_pagerank(g, alpha=alpha, tolerance=tolerance, max_iteration=max_iteration, v=reset_v)

		progress -= 1
		#logger.info(progress)

	rwr_scores = {}

	for link in candidates:
		v = link.split(',')
		v1 = int(v[0])
		v2 = int(v[1])

		rwr_scores[link] = (personalized_pagerank_scores[v1][v2] +  personalized_pagerank_scores[v2][v1]) / 2 #personalized_pagerank_scores[v1][v2] if directed else personalized_pagerank_scores[v1][v2] +  personalized_pagerank_scores[v2][v1]

	return rwr_scores

	





	
	