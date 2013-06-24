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
import csv
import igraph
import numpy as np
from misc.utils import root_folder
from network_analysis.utils import load_network_for
from network_analysis.networks import ResearchCollaborationNetwork
import network_analysis.centrality_leaders.rank_aggregation as rg
import network_analysis.centrality_leaders.centrality_leaders as cl


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def draw(g, filename):
	layout = g.layout('kk')

	color_dict = {0: 'gray', 1: 'green'}

	centrality_sizes = []

	for v in g.vs:
		if v['centrality_leader'] != None:
			centrality_sizes.append(int(v['centrality_leader']) * 2.5 + 10)
		else:
			centrality_sizes.append(10)

	visual_style = {}
	visual_style['vertex_size'] = centrality_sizes
	visual_style['vertex_color'] = [color_dict[int(ctsa)] for ctsa in g.vs['ctsa']]
	#visual_style['vertex_label'] = g.vs['name']
	visual_style['edge_width'] = [e_weight for e_weight in g.es['weight']]
	visual_style['layout'] = layout
	visual_style['bbox'] = (1000, 1000)
	visual_style['margin'] = 20

	igraph.plot(g, filename, **visual_style)


def centrality_leaders(budgetYears):
	

	network = load_network_for(budgetYears)

	g = network.g.copy()

	g = ResearchCollaborationNetwork.largest_component(g)

  	topK = 10
  	
  	candidates, rankings = cl.centrality_leaders(g)

  	for r in range(len(rankings))[:topK]:
  		#logger.info('tier: %d'%r)
  		for i in list(rankings[r]):
  			node_name = g.vs[candidates[i]]['name']

  			g.vs[candidates[i]]['centrality_leader'] = topK + 1 - r # set the node's centrality_leader attribute, the lower the better

  	startBudgetYear = budgetYears[0]
	endBudgetYear = budgetYears[-1]

  	filename = '%s/figures/%s-%s-centrality-leaders.png'%(root_folder(),startBudgetYear, endBudgetYear)
 	draw(g, filename)

  	
	
if __name__ == '__main__':
	centrality_leaders(range(2006,2010))
	centrality_leaders(range(2010,2013))
