#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Social Network Analysis of the UAMS's CTSA grant
centrality_leaders.py

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
	visual_style['bbox'] = (1000, 400)
	visual_style['margin'] = 20

	igraph.plot(g, filename, **visual_style)


def centrality_leaders(budgetYears):

	network = load_network_for(budgetYears)

	g = network.g.copy()

	g = ResearchCollaborationNetwork.largest_component(g)

	topK = 10

	candidates, rankings = cl.centrality_leaders(g)

	ordered_list = []
	for r in range(len(rankings))[:topK]:
		#logger.info('tier: %d'%r)
		for i in list(rankings[r]):
			node_name = g.vs[candidates[i]]['name']
			ordered_list.append(node_name)
			# set the node's centrality_leader attribute, the higher the better
			g.vs[candidates[i]]['centrality_leader'] = topK + 1 - r

	startBudgetYear = budgetYears[0]
	endBudgetYear = budgetYears[-1]

	filename = '%s/figures/%s-%s-centrality-leaders.png' % (root_folder(), startBudgetYear, endBudgetYear)
	draw(g, filename)

	logger.info(ordered_list)


def update_graphml(budgetYears):
	startBudgetYear = budgetYears[0]
	endBudgetYear = budgetYears[-1]

	network = load_network_for(budgetYears)

	network.g.vs['centrality_leader'] = 0
	g = network.g.copy()

	g = ResearchCollaborationNetwork.largest_component(g)

	topK = 50

	candidates, rankings = cl.centrality_leaders(g)

	#logger.info(candidates)
	#logger.info(rankings)


	#ordered_list = []
	for r in range(len(rankings))[:topK]:
	
		logger.info('tier: %d'%r)
		
		for i in list(rankings[r]):
			node_name = g.vs[candidates[i]]['name']
			# ordered_list.append(node_name)
			# set the node's centrality_leader attribute, the higher the better

			#g.vs[candidates[i]]['centrality_leader'] = topK + 1 - r
			node = network.g.vs.select(name_eq=node_name)
			#logger.info(node['name'])
			node['centrality_leader'] = r + 1
			#logger.info(topK - r)
			# logger.info(node['name'])

	filename = '%s/data/networks/%d-%d.graphml' % (root_folder(), startBudgetYear, endBudgetYear)

	network.write(filename)


if __name__ == '__main__':

	for budgetYear in range(2006, 2013):
		update_graphml(range(budgetYear, budgetYear + 1))

	update_graphml(range(2006, 2010))
	update_graphml(range(2010, 2013))
	update_graphml(range(2006, 2013))

	# logger.info("2006-2010")
	# centrality_leaders(range(2006, 2010))

	# logger.info("2009-2012")
	# centrality_leaders(range(2010, 2013))

	# logger.info("2006-2012")
	# centrality_leaders(range(2006, 2013))
