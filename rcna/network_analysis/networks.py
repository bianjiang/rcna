#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Social Network Analysis of the UAMS's CTSA grant'''
'''
	networks.py for network_analysis
	generate network from grant data
''' 
__appname__ = 'Research Collaboration Social Network Analysis'
__author__  = 'Jiang Bian'
__version__ = '0.0.1'
__license__ = 'MIT'

import logging
import itertools
import igraph
import json

from operator import itemgetter, attrgetter

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


class GrantResearcherNetwork(object):

	def g():
		doc = 'The internal igraph object.'
		def fget(self):
			return self._g
		def fset(self, value):
			self._g = value
		def fdel(self):
			del self._g
		return locals()
	g = property(**g())

	def nodes():
		doc = 'The internal nodes list.'
		def fget(self):
			return self._nodes
		def fset(self, value):
			self._nodes = value
		def fdel(self):
			del self._nodes
		return locals()
	nodes = property(**nodes())

	def edges():
		doc = 'The internal edge list, src -> dest + weight'
		def fget(self):
			return self._edges
		def fset(self, value):
			self._edges = value
		def fdel(self):
			del self._nodes
		return locals()
	edges = property(**edges())

	#internal index when creating from raw, don't get confused with igraph node.index
	@staticmethod
	def node_index(nodes, id):
		if id not in nodes:
			nodes[id] = {'index_': len(nodes)} # autoincrement, start with 0

		return nodes[id]['index_']	

	@classmethod
	def read(cls, filename):

		g = igraph.Graph.Read(filename,format="graphml")
		
		# doesn't seem to have a need to recrate the nodes and edges from loaded graph
		nodes = {}
		edges = {}

		for node in g.vs:
			GrantResearcherNetwork.node_index(nodes, int(node['name']))

		for edge in g.es:
			v1 = int(g.vs[edge.source]['name'])
			v2 = int(g.vs[edge.target]['name'])

			m = min(v1, v2)
			n = max(v1, v2)

			#always min-max
			key = '%d-%d'%(m,n)
			#logger.info(key)
			edges[key] = edge['weight']


		return cls(nodes, edges, g)


	def __init__(self, nodes = None, edges = None, g = None):
		self.nodes = nodes
		self.edges = edges
		self.g = g

	@staticmethod
	def simplify(g):
		#remove multiple, loops
		g = g.simplify(multiple=True, loops=True,combine_edges=sum)

		# convert to undirected
	  	g.to_undirected(combine_edges=sum)

	  	# delete unlinked nodes
	  	g.vs.select(_degree = 0).delete()

	  	return g

	#get the largest component (the component with the most connected nodes)
	@staticmethod
	def largest_component(g):
		g = GrantResearcherNetwork.simplify(g)

		g_ = None
		vs_ = 0
		for gs in g.decompose(mode=igraph.STRONG):


			if len(gs.vs) > vs_:
				vs_ = len(gs.vs)
				g_ = gs

		return g_

	# in graphml format, the nodes can have many attributes, so we don't need to generate the node attributes from raw data anymore
	@staticmethod
	def d3(g, filename):

		d3_results = {}
		d3_nodes = []
		d3_edges = []		

		for node in g.vs:
			d3_nodes.append(dict({'index':int(node.index)}.items() + node.attributes().items()))

		for edge in g.es:
			d3_edges.append(dict({'source':edge.source, 'target':edge.target}.items() + edge.attributes().items()))

		d3_results['nodes'] = d3_nodes
		d3_results['links'] = d3_edges


		## This part is used to generate the d3 json for visualization
		with open(filename, 'w') as outfile:
	  		json.dump(d3_results, outfile)

	  	logger.info('convert to d3 json into: %s'%filename)




