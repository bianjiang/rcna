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
from misc.utils import root_folder, load_network_for
from network_analysis.networks import GrantResearcherNetwork



logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')



def statistics_of_ctsa():
	# the ctsa grant's prn is 35030, 36697

	logger.info('root: %s'%root_folder())


	dataloader = GrantDataLoader()

	startShortYear = 10
	endShortYear = 12

	ctsaARIARecord = dataloader.findObject('ARIAGrant', [
		lambda o: int(o.attributes['PRN']) == 35030 or int(o.attributes['PRN']) == 36697,
		lambda o: get_fiscal_year(o.attributes['BudgetStartDate']) >= startShortYear and get_fiscal_year(o.attributes['BudgetStartDate']) <= endShortYear
		])
	
	logger.info('# of CTSA records: %d'%len(ctsaARIARecord))

	investigators = []

	for ctsaReocrd in ctsaARIARecord:

		recordID = ctsaReocrd.attributes['ARIARecordID']
		logger.info('id: %s; title: %s'%(recordID,ctsaReocrd.attributes['Title']))

		grantInvestigators = dataloader.findObject('ARIAGrantRole', [
					lambda o: int(o.attributes['ARIARecordID']) == int(recordID),
					lambda o: o.attributes['Role'] in ['Principal Investigator', 'Co-Investigator', 'Sub-Investigator']
					])

		for investigator in grantInvestigators:
			logger.info(investigator.attributes['SAPID'])

			investigators.append(int(investigator.attributes['SAPID']))

		logger.info('# of investigators: %d'%len(grantInvestigators))

	logger.info('# of investigators for year %d: %d'%(startShortYear, len(set(investigators))))

	logger.info(set(investigators))



def num_of_isolated_components(budgetYears):

	startBudgetYear = budgetYears[0]
	endBudgetYear = budgetYears[-1]


	network = GrantResearcherNetwork.read(budgetYears)	
	g = network.g.copy()

	gs = g.decompose(mode=igraph.STRONG)

	logger.info('%s-%s: #number of isolated components: %d'%(startBudgetYear, endBudgetYear, len(gs)))
 
def average_shortest_path_length(g):

	weights = [ 1/float(weight) for weight in g.es['weight']]

	cap = 0.0
	cnt = 0
	for v in g.vs:
		shortest_paths = g.shortest_paths(v, weights=weights, mode=igraph.ALL)
		ap = [pl for pl in shortest_paths[0] if np.isfinite(pl)]

		#logger.info(ap)

		if len(ap) > 0:
			cap += sum(ap)/len(ap)
		else:
			continue

		cnt += 1

	return cap/cnt



def ctsa_statistics(budgetYears):

	startBudgetYear = budgetYears[0]
	endBudgetYear = budgetYears[-1]

	dataloader = GrantDataLoader()


	ctsaInvestigator = dataloader.findObject('UAMSCTSAResearcher', [
				lambda o: int(o.attributes['year']) >= startBudgetYear and int(o.attributes['year']) <= endBudgetYear
				])

	logger.info('%s-%s: %d'%(startBudgetYear, endBudgetYear, len(ctsaInvestigator)))

def set_category_code_by_department(budgetYears):
	
	startBudgetYear = budgetYears[0]
	endBudgetYear = budgetYears[-1]

	dataloader = GrantDataLoader()

	#logger.info('----------------------------------------------')
	#logger.info('---------------- %s-%s -------------------'%(startBudgetYear, endBudgetYear))
	network = GrantResearcherNetwork.read(budgetYears)

	g = network.g
	#GrantResearcherNetwork.simplify(g)

	departments = []

	for node in g.vs:
		sapID = node['name']

		investigator = dataloader.findObject('ARIAUser', [
			lambda o: int(o.attributes['sapID']) == int(sapID),
			]).pop()

		

		dept_name = investigator.attributes['dept_name'].lower().strip()

		if dept_name not in departments:
			departments.append(dept_name)

		categoryCode = departments.index(dept_name)

		#logger.info('sapId: %s; department: %s; categoryCode: %s '%(sapID, investigator.attributes['dept_name'], categoryCode))

		node['department'] = dept_name
		node['category'] = categoryCode

	del g.vs['id']

	network.write(budgetYears, extra = 'category')

def diversities(budgetYears):
	'''
	Basically, this calculates the average_path_length from one category of nodes to all other categories of nodes.
	A basic example is to use department as a category, and calculate this as evidence of cross-disciplinary collaborations. 
	'''
	startBudgetYear = budgetYears[0]
	endBudgetYear = budgetYears[-1]

	#logger.info('----------------------------------------------')
	#logger.info('---------------- %s-%s -------------------'%(startBudgetYear, endBudgetYear))
	network = GrantResearcherNetwork.read(budgetYears, extra='category')

	g = network.g.copy()
	GrantResearcherNetwork.simplify(g)
	#logger.info(g.summary())

	# doing this, so we can separate the data generation process from actual calculate later on.

	categoryCodes = set(g.vs['category'])

	density = g.density()
	
	# the weight needs to change to inverse as shortest path measures the closeness of the network
	for e in g.es:
		e['weight'] = 1/e['weight']

	#logger.info(g.es['weight'])

	#quit()		
		
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
				cap += sum(ap)/len(ap)
			else:
				continue # if no shortest path, ignore this node, shouldn't count it

			cnt += 1


		average_path_length += cap/cnt

	return len(categoryCodes)/average_path_length

def average_number_of_new_edges(cbudgetYears, pbudgetYears):
	'''
		This counts number of new edges of each node comparing to the previous year
		for aggregated graphs, it compares to the previous aggregated graph
	'''
	startBudgetYear = cbudgetYears[0]
	endBudgetYear = cbudgetYears[-1]

	if startBudgetYear == 2006:
		return 0.0
	#logger.info('----------------------------------------------')
	#logger.info('---------------- %s-%s -------------------'%(startBudgetYear, endBudgetYear))
	cNetwork = GrantResearcherNetwork.read(cbudgetYears)
	pNetwork = GrantResearcherNetwork.read(pbudgetYears)

	cg = cNetwork.g.copy()
	GrantResearcherNetwork.simplify(cg)

	pg = pNetwork.g.copy()
	GrantResearcherNetwork.simplify(pg)

	# loop through the current graph and find the corresponding node in the previous graph
	found_cnt = 0
	new_edges = 0.0 # counting weights
	for v in cg.vs:

		found = pg.vs.select(name_eq = v['name'])

		for f in found:
			found_cnt += 1
			new_edges += v.strength(weights='weight') - f.strength(weights='weight')

	return new_edges/found_cnt


def statistics(budgetYears):
	startBudgetYear = budgetYears[0]
	endBudgetYear = budgetYears[-1]

	#logger.info('----------------------------------------------')
	#logger.info('---------------- %s-%s -------------------'%(startBudgetYear, endBudgetYear))
	network = GrantResearcherNetwork.read(budgetYears)

	g = network.g.copy()
	GrantResearcherNetwork.simplify(g)

	#logger.info('#number of nodes: %d'%(len(g.vs)))
	#logger.info('#number of edges: %d'%(len(g.es)))

	gs = g.decompose(mode=igraph.STRONG)

	#logger.info('#number of isolated components: %d'%(len(gs)))
	if int(startBudgetYear) == int(endBudgetYear):
		fy = startBudgetYear
		logger.info('%s & %d & %d & %0.2f & %d & %0.2f & %0.2f & %0.2f & %0.2f \\\\'%(fy,len(g.vs),len(g.es), round(g.density(), 2), len(gs), round(g.transitivity_undirected(), 2), round(average_shortest_path_length(g),2), round(diversities(budgetYears), 2), round(average_number_of_new_edges(budgetYears, range(startBudgetYear-1, startBudgetYear)), 2)))
	else:
		fy = '%s -- %s'%(startBudgetYear, endBudgetYear)
		logger.info('\\textbf{%s} & \\textbf{%d} & \\textbf{%d} & \\textbf{%0.2f} & \\textbf{%d} & \\textbf{%0.2f} & \\textbf{%0.2f} & \\textbf{%0.2f} & \\textbf{%0.2f} \\\\'%(fy,len(g.vs),len(g.es), round(g.density(), 2),len(gs), round(g.transitivity_undirected(), 2), round(average_shortest_path_length(g),2), round(diversities(budgetYears), 2), 0.0))
	logger.info('\\hline')
	#logger.info('---------------- %s-%s -------------------'%(startBudgetYear, endBudgetYear))
	#logger.info('----------------------------------------------')

def network_characteristics(network):
	g = network.g.copy()

	#g = GrantResearcherNetwork.largest_component(g)
	g = GrantResearcherNetwork.simplify(g)
	logger.info(g.summary())

	weights =  [1.0/weight for weight in g.es['weight']]

	C_g = g.transitivity_avglocal_undirected(mode='zero', weights=None)
	logger.info('C_g (weights = None): %f'%C_g)

	C_g = g.transitivity_avglocal_undirected(mode='zero', weights=g.es['weight'])
	logger.info('C_g (weights = number of collaborations): %f'%C_g)

	C_g = g.transitivity_avglocal_undirected(mode='zero', weights=weights)
	logger.info('C_g (weights = resistance factor): %f'%C_g)

	C_g = g.transitivity_undirected(mode='zero')
	logger.info('C_g (triplets definition): %f'%C_g)

if __name__ == '__main__':

	network = load_network_for(range(2006,2010))

	network_characteristics(network)

	network = load_network_for(range(2010,2013))

	network_characteristics(network)

	quit()
	logger.info('\\hline')
	for budgetYear in range(2006, 2010):
		network_characteristics(range(budgetYear,budgetYear+1))

	network_characteristics(range(2006,2010))
	logger.info('\\hline')
	for budgetYear in range(2010, 2013):
		statistics(range(budgetYear,budgetYear+1))

	statistics(range(2010,2013))
