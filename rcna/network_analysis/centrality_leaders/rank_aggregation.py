#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division

"""Social Network Analysis of the UAMS's CTSA grant"""
'''
	rank_aggregation.py for network_analysis
	various rank aggregation algorithms specific for this project
	currently, only kemeny-yound method is here
	borrowed from https://github.com/eswald/Ranked-Voting/
''' 
__appname__ = "Research Collaboration Social Network Analysis"
__author__  = "Jiang Bian"
__version__ = "0.0.1"
__license__ = "MIT"

import logging
import numpy as np
import sys
from collections import defaultdict
from itertools import permutations

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

r'''Ranked voting methods.
	Each method here is a function with two parameters:
		`votes` - A sequence of tuples.
			The first item is a list of candidate keys in ranked order;
			each item may be a tuple to indicate equal rankings.
			The second item is the number of times this sequence appears.
		`candidates` - A sequence of candidate keys.
			Keys in the vote rankings that don't appear in this list will be ignored.
'''#"""#'''

from collections import defaultdict

try:
	from itertools import permutations
except ImportError:
	# Python 2.5 doesn't seem to have this function.
	# Copied from http://docs.python.org/library/itertools.html#itertools.permutations
	def permutations(iterable, r=None):
		# permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
		# permutations(range(3)) --> 012 021 102 120 201 210
		pool = tuple(iterable)
		n = len(pool)
		r = n if r is None else r
		if r > n:
			return
		indices = range(n)
		cycles = range(n, n-r, -1)
		yield tuple(pool[i] for i in indices[:r])
		while n:
			for i in reversed(range(r)):
				cycles[i] -= 1
				if cycles[i] == 0:
					indices[i:] = indices[i+1:] + indices[i:i+1]
					cycles[i] = n - i
				else:
					j = cycles[i]
					indices[i], indices[-j] = indices[-j], indices[i]
					yield tuple(pool[i] for i in indices[:r])
					break
			else:
				return

try:
	next
except NameError:
	# Also new in Python 2.5, in preparation for an interface change.
	def next(iterable):
		return iterable.next()

__all__ = []
methods = {}

def method(name):
	def export(method):
		methods[name] = method
		__all__.append(method.__name__)
		return method
	return export

def unwind(ranks, candidates):
	candidates = set(candidates)
	for row in ranks:
		if not isinstance(row, (tuple, set, list)):
			row = [row]
		rank = set(row) & candidates
		if rank:
			yield rank

class Graph(object):
	r'''Basic graph structure.
		Designed for use by voting algorithms.
	'''#"""#'''
	
	def __init__(self, vertices):
		r'''Create a new Graph.
			`vertices` is a sequence of distinct hashable objects.
		'''#"""#'''
		# Store the inbound connections in a dictionary.
		# Outbound would make remove_vertex() easier, but roots() harder.
		self.vertices = dict((v, set()) for v in vertices)
	
	def edge(self, source, sink):
		r'''Create an edge from the source to the sink.
			This method provides no protections against cycles.
		'''#"""#'''
		self.vertices[sink].add(source)
		return True
	
	def acyclic_edges(self, edges):
		r'''Create edges from the (source, sink) pairs,
			as long as the graph remains acyclic.
			`edges` must be a sequence of vertex pairs.
			Returns the number of edges created.
		'''#"""#'''
		
		# Optimistically add all edges.
		completed = set()
		for source, sink in edges:
			self.vertices[sink].add(source)
			completed.add((source, sink))
		
		# Prune any new cyclic edges.
		cyclic = self.prune_cycles(completed)
		return len(completed) - len(cyclic)
	
	def prune_cycles(self, edges):
		r'''Remove any of the specified edges that participate in cycles.
			`edges` must be a sequence of vertex pairs.
			Returns a set of the edges removed.
		'''#"""#'''
		
		# Collect all of the edges in cycles.
		cyclic = set()
		for source, sink in edges:
			seen = set()
			connected = set([source])
			while connected:
				vertex = connected.pop()
				inbound = self.vertices[vertex]
				if sink in inbound:
					cyclic.add((source, sink))
					break
				seen.add(vertex)
				connected.update(inbound - seen)
		
		# Prune all collected edges at once.
		for source, sink in cyclic:
			self.remove_edge(source, sink)
		
		return cyclic
	
	def river_edges(self, edges):
		r'''Create each of the specified edges that would not
			introduce a cycle or an outbound branching.
			`edges` must be a sequence of vertex pairs.
			Returns a set of edges that were not created.
		'''#"""#'''
		
		# Group the edges by their outbound vertex.
		sinks = defaultdict(set)
		for source, sink in edges:
			sinks[sink].add(source)
		
		# Create any edges that don't create branches.
		blocked = set()
		completed = set()
		for sink in sinks:
			sources = sinks[sink]
			if self.vertices[sink] or len(sources) > 1:
				# Outbound branching detected.
				for source in sources:
					blocked.add((source, sink))
			else:
				source = sources.pop()
				self.vertices[sink].add(source)
				completed.add((source, sink))
		
		# Prune any new cyclic edges.
		cyclic = self.prune_cycles(completed)
		
		return blocked | cyclic
	
	def edges(self):
		r'''Collect all edges in the graph.
		'''#"""#'''
		for sink in self.vertices:
			for source in self.vertices[sink]:
				yield source, sink
	
	def roots(self):
		r'''Collect the vertices with no inbound edges.
			These are the roots of the tree, or the best choices.
		'''#"""#'''
		return [key for key in self.vertices if not self.vertices[key]]
	
	def pop(self):
		r'''Collect and remove root vertices in a single call.
		'''#"""#'''
		roots = set()
		for key, value in list(self.vertices.items()):
			if not value:
				roots.add(key)
				del self.vertices[key]
		
		for inbound in self.vertices.values():
			inbound.difference_update(roots)
		
		return roots
	
	def paths(self, source, sink):
		r'''Collect all paths from the source to the sink.
			Tends to yield shorter paths first.
		'''#"""#'''
		paths = [([sink], self.vertices[sink])]
		while paths:
			path, steps = paths.pop(0)
			for item in steps:
				if item == source:
					yield [item] + path
				elif item not in path:
					inbound = self.vertices[item]
					if inbound:
						paths.append(([item] + path, inbound))
	
	def remove_vertex(self, vertex):
		r'''Remove a vertex from the graph.
			Also removes any edges connected to that vertex.
		'''#"""#'''
		del self.vertices[vertex]
		for inbound in self.vertices.values():
			inbound.discard(vertex)
	
	def remove_edge(self, source, sink):
		r'''Remove an edge from the graph.
		'''#"""#'''
		self.vertices[sink].remove(source)
	
	def __nonzero__(self):
		r'''Truth value for the graph.
			A Graph is true if it contains any vertices.
		'''#"""#'''
		return bool(self.vertices)

def pairwise(votes, candidates):
	r'''Collects pairwise majorities from the ballots.
		Returns a dictionary of (winner, loser) => (major, minor),
		suitable for passing into regrouped().
	'''#"""#'''
	comparisons = defaultdict(int)
	for ranks, count in votes:
		above = set()
		for row in unwind(ranks, candidates):
			for candidate in row:
				for former in above:
					comparisons[former, candidate] += count
			above.update(row)
	
	majorities = {}
	for a,b in comparisons:
		major = comparisons[a, b]
		minor = comparisons.get((b, a), 0)
		if major > minor:
			majorities[a, b] = (major, minor)
	
	return majorities

def regrouped(mapping, reverse=True):
	r'''Collects sets of keys with identical values,
		sorted from greatest to least.
	'''#"""#'''
	counts = defaultdict(set)
	for key in mapping:
		counts[mapping[key]].add(key)
	
	for value in sorted(counts, reverse=reverse):
		yield counts[value]

def pairs(sequence):
	r'''Yield each pair of the sequence exactly once, preserving order.
		For example, if "A" follows "B" are in the sequence, the result
		contains ("B", "A") somewhere, but not ("A", "B").
	'''#"""#'''
	items = list(sequence)
	for b in xrange(1, len(items)):
		for a in xrange(0, b):
			yield items[a], items[b]

@method("Ranked Pairs")
def rankedpairs(votes, candidates):
	# Tideman method, using a graph of preferences data.
	# Modified by ignoring unstated candidates, instead of
	# assuming that they're all worse than the ranked ones.
	majorities = pairwise(votes, candidates)
	graph = Graph(candidates)
	for rank in regrouped(majorities):
		graph.acyclic_edges(rank)
	
	while graph:
		winners = graph.pop()
		yield winners

@method("Instant-Runoff")
def instantrunoff(votes, candidates):
	# Instant Runoff Voting (IRV)
	# Modified to return a total ordering.
	candidates = set(candidates)
	majority = sum(item[1] for item in votes) / 2
	
	winners = []
	losers = []
	while candidates:
		totals = dict.fromkeys(candidates, 0)
		for ranks, count in votes:
			for row in unwind(ranks, candidates):
				# Divide the votes evenly among the preferences.
				value = count / len(row)
				for candidate in row:
					totals[candidate] += value
				break
		
		counts = defaultdict(set)
		for key in totals:
			counts[totals[key]].add(key)
		
		top = max(counts)
		if top > majority:
			# We have a winner!
			found = counts[top]
			winners.append(found)
		else:
			# Eliminate the losers.
			found = counts[min(counts)]
			losers.insert(0, found)
		
		# Remove ranked candidates from the list
		candidates.difference_update(found)
	
	return winners + losers

@method("Plurality")
def plurality(votes, candidates):
	# First past the post, winner takes all.
	# Only the top preference is even looked at.
	totals = dict.fromkeys(candidates, 0)
	for ranks, count in votes:
		for row in unwind(ranks, candidates):
			value = count / len(row)
			for candidate in row:
				totals[candidate] += value
			break
	
	return [rank for rank in regrouped(totals)]

@method("Borda Count")
def borda(votes, candidates):
	# Borda Count method.
	# The over/under count system makes each ballot zero-sum, which allows
	# incomplete ballots to have less impact on unranked candidates.
	ratings = dict.fromkeys(candidates, 0)
	for ranks, count in votes:
		# First, subtract points for each candidate ranked higher.
		seen = 0
		for row in unwind(ranks, candidates):
			value = count * seen
			seen += len(row)
			for candidate in row:
				ratings[candidate] -= value
		
		# Second, add points for each candidate ranked lower.
		for row in unwind(ranks, candidates):
			seen -= len(row)
			value = count * seen
			for candidate in row:
				ratings[candidate] += value
	
	return [rank for rank in regrouped(ratings)]

@method("Bucklin")
def bucklin(votes, candidates):
	# The Bucklin or Grand Junction voting system.
	# Seems to work well for three candidates, but not more.
	majority = sum(item[1] for item in votes) / 2
	
	for n in range(1, len(candidates) + 1):
		totals = dict.fromkeys(candidates, 0)
		for ranks, count in votes:
			seen = 0
			for row in unwind(ranks, candidates):
				if len(row) > n - seen:
					# Divide the votes evenly among the preferences.
					# Letting each one count fully would let some ballots
					# count more than others.
					value = count * (n - seen) / len(row)
				else:
					value = count
				
				for candidate in row:
					totals[candidate] += value
				
				seen += len(row)
				if seen >= n:
					break
		
		counts = defaultdict(set)
		for key in totals:
			counts[totals[key]].add(key)
		
		result = sorted(counts, reverse=True)
		if result[0] > majority:
			# We have a winner!
			return [counts[total] for total in result]
	else:
		# No majority exists.
		# This might not be the best result,
		# but I'm not sure how to better express the lack of majority.
		return [candidates]

@method("Minimax")
def minimax(votes, candidates):
	# Minimax / Successive reversal / Simpson method.
	# Using rankings, select unbeaten candidates.
	# If there aren't any, drop the weakest wins.
	majorities = pairwise(votes, candidates)
	graph = Graph(candidates)
	for a, b in majorities:
		graph.edge(a, b)
	
	groups = regrouped(majorities, False)
	while graph:
		winners = graph.pop()
		if winners:
			yield winners
		else:
			for sink, source in next(groups):
				if (sink, source) in graph.edges():
					graph.remove_edge(sink, source)

@method("Beatpath")
def beatpath(votes, candidates):
	# Schulze method, equivalent to Cloneproof Schwartz Sequential Dropping.
	majorities = pairwise(votes, candidates)
	graph = Graph(candidates)
	for a, b in majorities:
		graph.edge(a, b)
	
	def path_steps(path):
		sequence = iter(path)
		prev = next(sequence)
		for item in sequence:
			yield prev, item
			prev = item
	
	def beat_strength(source, sink):
		# max() doesn't like empty iterables.
		strength = 0
		for path in graph.paths(source, sink):
			path_strength = min(majorities[step]
				for step in path_steps(path))
			if path_strength > strength:
				strength = path_strength
		return strength
	
	final = Graph(candidates)
	for source, sink in pairs(candidates):
		major = beat_strength(sink, source)
		minor = beat_strength(source, sink)
		if major > minor:
			final.edge(sink, source)
		elif minor > major:
			final.edge(source, sink)
	
	while final:
		winners = final.pop()
		yield winners

@method("River")
def river(votes, candidates):
	# A compromize between Beatpath and Ranked Pairs
	# http://web.archive.org/web/20071031155527/http://lists.electorama.com/pipermail/election-methods-electorama.com/2004-October/013971.html
	majorities = pairwise(votes, candidates)
	graph = Graph(candidates)
	retries = []
	for rank in regrouped(majorities):
		result = graph.river_edges(rank)
		if result:
			retries.append(result)
	
	# Attempt a more total ordering.
	for rank in retries:
		graph.acyclic_edges(rank)
	
	while graph:
		winners = graph.pop()
		yield winners

@method("Kemeny-Young")
def kemeny(votes, candidates):
	# Kemeny-Young maximum likelihood method.
	# http://en.wikipedia.org/wiki/Kemeny-Young_method
	
	#logger.info(len(candidates))
	if len(candidates) > 20:
		# This calculation would take entirely too long.
		# There are ways to optimize it, but they get a little nuts.
		return [tuple(candidates)]
	
	comparisons = defaultdict(int)
	for ranks, count in votes:
		above = set()
		for row in unwind(ranks, candidates):
			for candidate in row:
				for former in above:
					comparisons[former, candidate] += count
			above.update(row)
	
	maximum = 0
	finalists = []
	for perm in permutations(candidates):
		total = sum(comparisons[a, b] for a, b in pairs(perm))
		if total > maximum:
			maximum = total
			finalists = [perm]
		elif total == maximum:
			finalists.append(perm)
	
	if len(finalists) == 1:
		# Shortcut for an unambiguous result
		result = [[item] for item in finalists[0]]
	else:
		# Collapse the ties.
		logger.info("here")
		ties = 0
		tied = set()
		result = []
		for rank in range(len(candidates)):
			winners = set(finalist[rank] for finalist in finalists)
			ties += 1
			tied.update(winners)
			if len(tied) == ties:
				result.append(tied)
				ties = 0
				tied = set()
	
	return result

# if reverse == True, then the higher score its better, otherwise the lower is better
# this corresponding to the reverse option in the sorted function
# default is the higher score is better
def sorted_keys(r, reverse = True):
	return sorted(range(len(r)), reverse=reverse, key=lambda k:r[k])

class RankBallots(object):

	def __init__(self, candidates_list):
		##create a candidate dict from list
		self.candidates = dict(zip(range(len(candidates_list)), candidates_list))
		self.ballots = []

	# each input scores is a list of scores, ordered in the same order of the orginal candidates_list
	# e.g., item 0 in ballot corresponding to the scores of item 0 in candidates_list 
	# if reverse == True, then the higher score its better, otherwise the lower is better
	# this corresponding to the reverse option in the sorted function
	# default is the higher score is better
	# 
	# each ballot is ranking of the candidates based on its score in the score list
	def add_ballot(self, scores, reverse = True):
		self.ballots.append((sorted_keys(scores, reverse), len(self.ballots)))

	def ranking(self, methodname='borda'):
		logger.info('voting method: %s'%methodname)
		thismodule = sys.modules[__name__]

		method = getattr(thismodule, methodname)
		if not method:
			raise Exception("Method %s not implemented" % method_name)
		
		return method(self.ballots, self.candidates)
		
		

