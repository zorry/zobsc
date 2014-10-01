from __future__ import print_function
import sys
import re
import os
import errno

def  get_file_text(filename):
	# Return the filename contents
	try:
		textfile = open(filename)
	except:
		return "No file", filename
	text = ""
	for line in textfile:
		text += unicode(line, 'utf-8')
	textfile.close()
	return text

def  get_ebuild_cvs_revision(filename):
	"""Return the ebuild contents"""
	try:
		ebuildfile = open(filename)
	except:
		return "No Ebuild file there"
	text = ""
	dataLines = ebuildfile.readlines()
	for i in dataLines:
		text = text + i + " "
	line2 = dataLines[2]
	field = line2.split(" ")
	ebuildfile.close()
	try:
		cvs_revision = field[3]
	except:
		cvs_revision = ''
	return cvs_revision

def  get_log_text_list(filename):
	"""Return the log contents as a list"""
	try:
		logfile = open(filename)
	except:
		return None
	text = []
	dataLines = logfile.readlines()
	for i in dataLines:
		text.append(i)
	return text
