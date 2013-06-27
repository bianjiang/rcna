#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Social Network Analysis of the UAMS's CTSA grant
link_prediction_test.py

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
import random
import matplotlib.pyplot as plt


from misc.utils import root_folder
from network_analysis.utils import load_network_for
from network_analysis.networks import ResearchCollaborationNetwork

import network_analysis.link_prediction.pagerank as pgrank
import network_analysis.link_prediction.benchmark.benchmarks as benchmarks
import network_analysis.link_prediction.benchmark.utils as utils
import network_analysis.link_prediction.benchmark.pyroc as pyroc
import network_analysis.link_prediction.benchmark.rocarea as roc
from random import shuffle

def per_candidate(budgetYears):
	startBudgetYear = budgetYears[0]
	endBudgetYear = budgetYears[-1]

	logger.info('---------------- %s-%s -------------------'%(startBudgetYear, endBudgetYear))

	network = load_network_for(budgetYears)

	g = network.g.copy()

	ResearchCollaborationNetwork.simplify(g)

	logger.info(g.summary())

	adj = np.array(g.get_adjacency(igraph.GET_ADJACENCY_BOTH).data)

	m, _ = adj.shape

	cNodes = g.vs.select(_degree_gt=15) #range(len(g.vs))
	candidates = []
	for cNode in cNodes:
		candidates.append(cNode.index)

	shuffle(candidates)
	candidates = candidates[:10]

	total_auc = 0.0
	precision_at_k = {3: 0.0, 5: 0.0, 10: 0.0}
	mapk = precision_at_k
	kfold = 5	

	roc_samples = []

	progress = len(candidates)

	# for each candidate we do training and testing...
	for c in candidates:		

		logger.info('%d-----------------------'%progress)

		nonobservedlinks = {}
	
		nonobserved_actual_edges = []

		nonobserved_nonexist_edges = []
		
		# undirectd graph, so only care if the source is in candidates or not
		for j in range(m):
			key = '%d,%d'%(c,j)
			nonobservedlinks[key] = adj[c,j]
			#logger.info(adj[c,j])

			if adj[c,j] > 0:
				nonobserved_actual_edges.append(key)
			else:
				nonobserved_nonexist_edges.append(key)

		cnt = 0
		auc = 0.0
		#average precision at k is defined per candidate
		apk = precision_at_k
		for ((es_p_training, es_p_validation), (es_m_training, es_m_validation)) in zip(utils.k_fold_cross_validation(list(nonobserved_actual_edges), kfold), utils.k_fold_cross_validation(list(nonobserved_nonexist_edges), kfold)):
		
			#logger.info('--------iteration %d-------------'%cnt)

			#logger.info('xxxxxxxxxxxxxxxxxxxxxxxx')
			#logger.info('positive training: %d'%len(es_p_training))
			#logger.info('positive validation: %d'%len(es_p_validation))
			#logger.info('------------------------')
			#logger.info('negative training: %d'%len(es_m_training))
			#logger.info('negative validation: %d'%len(es_m_validation))
			#logger.info('xxxxxxxxxxxxxxxxxxxxxxxx')

			training = es_p_training + es_m_training
			validation = es_p_validation + es_m_validation

			#logger.info('training: %d; valiation: %d'%(len(training), len(validation)))
			
			# create training graph
			trainingG = g.copy()

			edges_2_delete = []
			#// remove edges from the validation set
			for link in validation:
				v = link.split(',')
				v1 = int(v[0])
				v2 = int(v[1])
				eId = trainingG.get_eid(v1,v2, directed=False, error=False)
				if eId != -1:
					edges_2_delete.append(eId)

			trainingG.delete_edges(edges_2_delete)

			#logger.info('-----training graph:-----\r\n %s \r\n -----end training graph:-----'%trainingG.summary())

			rwr_scores = pgrank.rwr_score(trainingG, validation)

			for k, rwr_score in rwr_scores.iteritems():
				if rwr_score > 1:
					logger.info('overflow? rwr_score: %0.2f'%(rwr_score))

			actual = []
			posterior = []
			actual_edges = []

			for k in validation:
				actual.append(nonobservedlinks[k])
				if nonobservedlinks[k] > 0:
					actual_edges.append(k)
				
				posterior.append(rwr_scores[k])
				
				roc_samples.append((k, nonobservedlinks[k], rwr_scores[k]))

			#logger.info('actual edges: %s'%actual_edges)		
			#logger.info('posterior: %s'%posterior)

			auc_ = benchmarks.auc(actual, posterior)
			auc += auc_
			total_auc += auc_

			#area, [ax, lines] = roc.roc_curve(labels=np.array(actual),scores=np.array(posterior))

			for topK, p in mapk.iteritems():
				predictedIndexes = sorted(range(len(posterior)), reverse=True, key=lambda k: posterior[k])[:topK]
				predicted = np.array(validation)[predictedIndexes]

				apk_ = benchmarks.apk(actual_edges, predicted, topK)
				apk[topK] += apk_	
				mapk[topK] += apk_

			cnt += 1	

		logger.info('%d: auc: %f'%(c, float(auc)/kfold))

		for topK, p in apk.iteritems():
			logger.info('%d: ap@%d: %f'%(c, topK, (apk[topK]/kfold)))

		progress -= 1	

	logger.info('auc: %f'%(float(total_auc)/(kfold*len(candidates))))
	for topK, p in mapk.iteritems():
		logger.info('map@%d: %f'%(topK, (mapk[topK]/(kfold*len(candidates)))))

	np.save('%s/data/%s-%s.per_user.roc.samples.npy'%(root_folder(),startBudgetYear, endBudgetYear), np.array(roc_samples))


def per_network(budgetYears):

	startBudgetYear = budgetYears[0]
	endBudgetYear = budgetYears[-1]

	logger.info('---------------- %s-%s -------------------'%(startBudgetYear, endBudgetYear))

	network = load_network_for(budgetYears)

	g = network.g.copy()

	ResearchCollaborationNetwork.simplify(g)

	logger.info(g.summary())

	# randomly pick 20 users 
	candidates = range(len(g.vs))
	shuffle(candidates)
	candidates = candidates[:20]

	adj = np.array(g.get_adjacency(igraph.GET_ADJACENCY_BOTH).data)

	m, _ = adj.shape

	nonobservedlinks = {}
	
	nonobserved_actual_edges = []

	nonobserved_nonexist_edges = []

	for i in range(m):
		# undirectd graph, so only care if the source is in candidates or not
		if i not in candidates:
			continue
		for j in range(i + 1, m):
			key = '%d,%d'%(i,j)
			nonobservedlinks[key] = adj[i,j]

			if adj[i,j] > 0:
				nonobserved_actual_edges.append(key)
			else:
				nonobserved_nonexist_edges.append(key)

	#logger.info('-----original graph:-----\r\n %s \r\n -----end original graph:-----'%g.summary())
	
	auc = 0.0
	
	apk = {3: 0.0, 5: 0.0, 10: 0.0}

	kfold = 10
	
	cnt = 0;
	
	roc_samples = []



	for ((es_p_training, es_p_validation), (es_m_training, es_m_validation)) in zip(utils.k_fold_cross_validation(list(nonobserved_actual_edges), kfold), utils.k_fold_cross_validation(list(nonobserved_nonexist_edges), kfold)):
		
		logger.info('--------iteration %d-------------'%cnt)

		logger.info('xxxxxxxxxxxxxxxxxxxxxxxx')
		logger.info('positive training: %d'%len(es_p_training))
		logger.info('positive validation: %d'%len(es_p_validation))
		logger.info('------------------------')
		logger.info('negative training: %d'%len(es_m_training))
		logger.info('negative validation: %d'%len(es_m_validation))
		#logger.info('xxxxxxxxxxxxxxxxxxxxxxxx')

		training = es_p_training + es_m_training
		validation = es_p_validation + es_m_validation

		#logger.info('training: %d; valiation: %d'%(len(training), len(validation)))
		
		# create training graph
		trainingG = g.copy()
		
		edges_2_delete = []
		#// remove edges from the validation set
		for link in validation:
			v = link.split(',')
			v1 = int(v[0])
			v2 = int(v[1])
			eId = trainingG.get_eid(v1,v2, directed=False, error=False)
			if eId != -1:
				edges_2_delete.append(eId)

		trainingG.delete_edges(edges_2_delete)

		#logger.info('-----training graph:-----\r\n %s \r\n -----end training graph:-----'%trainingG.summary())

		rwr_scores = pgrank.rwr_score(trainingG, validation)

		actual = []
		posterior = []
		actual_edges = []

		for k in validation:
			actual.append(nonobservedlinks[k])
			if nonobservedlinks[k] > 0:
				actual_edges.append(k)
			
			posterior.append(rwr_scores[k])
			
			roc_samples.append((k, nonobservedlinks[k], rwr_scores[k]))

		#logger.info('actual edges: %s'%actual_edges)		
		#logger.info('posterior: %s'%posterior)

		auc_ = benchmarks.auc(actual, posterior)
		auc += auc_

		#area, [ax, lines] = roc.roc_curve(labels=np.array(actual),scores=np.array(posterior))

		for topK, p in apk.iteritems():
			predictedIndexes = sorted(range(len(posterior)), reverse=True, key=lambda k: posterior[k])[:topK]
			predicted = np.array(validation)[predictedIndexes]

			apk_ = benchmarks.apk(actual_edges, predicted, topK)
			apk[topK] += apk_	


		cnt += 1


	# take a look at http://www.machinedlearnings.com/2012/06/thought-on-link-prediction.html
	logger.info('auc: %f'%(auc/kfold))
	for topK, p in apk.iteritems():
		logger.info('ap@%d: %f'%(topK, (apk[topK]/kfold)))

	#plt.show()
	np.save('%s/data/%s-%s.per_network.roc.samples.npy'%(root_folder(),startBudgetYear, endBudgetYear), np.array(roc_samples))
	#roc = pyroc.ROCData(roc_samples)
	#logger.info('pyroc-auc: %f'%(roc.auc()))
	#roc.plot(title='ROC Curve')


if __name__ == '__main__':

	#per_candidate(range(2006,2010))
	#per_candidate(range(2010,2013))
	#per_candidate(range(2006,2013))

	per_network(range(2006,2010))
	per_network(range(2010,2013)) 
	#per_network(range(2006,2013)) 

