"""
Simple implementation of ROC curve plotting with NumPy and matplotlib.
No bells and whistles, no fancy data structures, just one function and
a (hopefully) very gentle learning curve.
"""

__author__ = "David Warde-Farley <dwf AT cs.toronto.edu>"
__copyright__ = "(c) 2010 David Warde-Farley"
__license__ = "3-clause BSD license"


import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

import copy

import numpy as np
import matplotlib.pyplot as plt

def roc_curve_init(ax):
	#ax = plt.axes()
	
	ax.set_aspect(1)
	plt.xlabel('False positive rate (1-Specificity)', fontsize=12)
	plt.ylabel('True positive rate (Sensitivity)',  fontsize=12)
	ax.plot([0, 1], [0, 1], '--', color='grey', label='_nolegend_')

	for s in ax.spines:
		ax.spines[s].set_alpha(0.3)


def roc_curve(*args, **kwargs):
	"""
	Plot an ROC curve using matplotlib.

	Called either with positive and negative discriminants as
	first and second positional arguments, or with the keywords
	'positives' and 'negatives', or with the keywords 'labels'
	and 'scores', where len(labels) == len(scores) and labels
	is boolean or integer with [0, 1] values.

	Additional keyword arguments are passed along to the plot()
	command used to draw the curve.
	"""
	allscores, positives, negatives, ax, legend, newkwargs = \
			_parse_roc_curve_args(*args, **kwargs)

	allscores = np.sort(allscores)
	thres = np.zeros(len(allscores) + 1)
	thres[0] = min(allscores) - 1
	thres[1:-1] = (allscores[1:] + allscores[:-1]) / 2.
	thres[-1] = np.max(allscores) + 1
	thres = np.sort(np.unique(thres))
	npos = len(positives)
	nneg = len(negatives)
	positives = np.sort(positives)
	negatives = np.sort(negatives)
	FN = np.nan * np.empty(thres.shape, dtype=np.float64)
	TN = FN.copy(); TP = FN.copy(); FP = FN.copy()
	TN[0] = 0; TP[0] = npos - FN[0]
	FN[0] = 0; FP[0] = nneg - TN[0]
	sens = np.zeros(thres.shape)
	spec = np.zeros(thres.shape)
	xcoord = np.zeros(thres.shape)
	ycoord = np.zeros(thres.shape)
	for ii in range(1, len(thres)):
		FN[ii] = FN[ii - 1]
		TN[ii] = TN[ii - 1]
		while FN[ii] < npos and positives[FN[ii]] < thres[ii]:
			FN[ii] = FN[ii] + 1
		while TN[ii] < nneg and negatives[TN[ii]] < thres[ii]:
			TN[ii] = TN[ii] + 1
		TP[ii] = npos - FN[ii]
		FP[ii] = nneg - TN[ii]
		sens[ii] = TP[ii] / (TP[ii] + FN[ii])
		spec[ii] = TN[ii] / (FP[ii] + TN[ii])
		xcoord[ii] = 1 - spec[ii]
		ycoord[ii] = sens[ii]
	xcoord, ycoord = zip(*sorted(zip(xcoord, ycoord)))
	xcoord = np.asarray(xcoord)
	ycoord = np.asarray(ycoord)
	dx = np.diff(xcoord)
	my = (ycoord[:-1] + ycoord[1:]) / 2.
	area = np.sum(dx * my)
	lines = ax.plot(xcoord, ycoord, label=legend, **newkwargs)
	return area, [ax, lines]

def _parse_roc_curve_args(*args, **kwargs):
	"""
	Helper function that checks for valid argument combinations
	and preprocesses kwargs.
	"""
	if len(args) == 2:
		for kw in ('positives', 'negatives'):
			if kw in kwargs:
				raise ValueError("got duplicate argument for '%s'" % kw)
		for kw in ('labels', 'scores'):
			if kw in kwargs:
				raise ValueError("'%s' keyword unsupported with " % kw +
								 " positional args present")
		positives, negatives = args
		allscores = np.concatenate((positives, negatives))
		ax = roc_curve_init()
	elif len(args) != 0:
		raise ValueError('roc_curve() takes a maximum of 2 positional args')
	else:
		if 'positives' in kwargs and 'negatives' in kwargs:
			if 'scores' in kwargs or 'labels' in kwargs:
				raise ValueError(
					"'scores'/'labels' keywords cannot be used in " +
					"conjunction with 'positives'/'negatives'"
				)
			for kw in ('positives', 'negatives'):
				if kwargs[kw].ndim > 1:
					raise ValueError("%s.ndim == 1 required" % kw)
			positives = np.asarray(kwargs['positives'])
			negatives = np.asarray(kwargs['negatives'])
			allscores = np.concatenate((positives, negatives))
		elif 'scores' in kwargs and 'labels' in kwargs:
			if 'positives' in kwargs or 'negatives' in kwargs:
				raise ValueError(
					"'positives'/'negatives' keywords cannot be used in "
					"conjunction with 'scores'/'labels'"
				)
			for kw in ('scores', 'labels'):
				if kwargs[kw].ndim > 1:
					raise ValueError("%s.ndim == 1 required" % kw)
			if len(kwargs['labels']) != len(kwargs['scores']):
				raise ValueError("'scores' and 'labels' must be same length")
			labels = np.asarray(kwargs['labels'])
			if (labels == 1).sum() + (labels == 0).sum() != len(labels):
				raise ValueError("'labels' must take on only values {0,1}")
			# Turn into a boolean vector for indexing.
			labels = (labels == 1)
			allscores = np.asarray(kwargs['scores'])
			positives = allscores[labels]
			negatives = allscores[~labels]
		else:
			raise ValueError("Need either pos/neg positional args, " +
							 "'positives'/'negatives' keyword args, " +
							 "or 'labels'/'scores' keyword args")

		ax = kwargs['ax']
		legend = kwargs['legend']

	newkwargs = copy.copy(kwargs)
	for kw in ('positives', 'negatives', 'labels', 'scores', 'ax', 'legend'):
		try:
			del newkwargs[kw]
		except KeyError:
			pass
	return allscores, positives, negatives, ax, legend, newkwargs



