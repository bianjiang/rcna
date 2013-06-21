#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Social Network Analysis of the UAMS's CTSA grant'''
 
__appname__ = 'Research Collaboration Social Network Analysis'
__author__  = 'Jiang Bian'
__version__ = '0.0.1'
__license__ = 'MIT'


import logging
import nose
import itertools
import os
import json
import cProfile
from misc.utils import root_folder, load_network_for
from network_analysis.networks import GrantResearcherNetwork
import igraph

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def vertex_colors(g):
	colors = []
	for v in g.vs:
		# if v['ctsa'] == 0 and v['role'] != 'Principal Investigator':
		# 	colors.append('gray')
		# elif v['ctsa'] == 0 and v['role'] == 'Principal Investigator':
		# 	colors.append('purple')
		# elif v['ctsa'] == 1 and v['role'] != 'Principal Investigator':
		# 	colors.append('green')
		# else:
		# 	colors.append('yellow')
		if v['ctsa'] == 0:
			colors.append('gray')
		else:
			colors.append('green')
	return colors


def draw(g, filename):
	layout = g.layout('kk')

	visual_style = {}
	visual_style['vertex_size'] = 30

	visual_style['vertex_color'] = vertex_colors(g) #[color_dict[int(ctsa)] for ctsa in g.vs['ctsa']]
	#visual_style['vertex_label'] = g.vs['name']
	visual_style['edge_width'] = [e_weight for e_weight in g.es['weight']]
	visual_style['layout'] = layout
	visual_style['bbox'] = (1000, 1000)
	visual_style['margin'] = 20

	igraph.plot(g, filename, **visual_style)

def draw_g(budgetYears):
	network = load_network_for(budgetYears)
	
	g = network.g.copy()
	#g = g.simplify(multiple=True, loops=True,combine_edges=sum)

	# convert to undirected
	#g.to_undirected(combine_edges=sum)

	g = GrantResearcherNetwork.simplify(g)

	startBudgetYear = budgetYears[0]
	endBudgetYear = budgetYears[-1]

	filename = '%s/figures/%s-%s-%d.png'%(root_folder(),startBudgetYear, endBudgetYear,len(g.vs))
	#logger.info(g.summary())
	draw(g, filename)

	gl = GrantResearcherNetwork.largest_component(g)
	
	filename = '%s/figures/%s-%s-%d-largest-component.png'%(root_folder(),startBudgetYear, endBudgetYear,len(gl.vs))

	draw(gl, filename)

if __name__ == '__main__':

	draw_g(range(2006,2010))

	draw_g(range(2010,2013))
