#!/usr/bin/python3

"""
Scrapes magic item data from a given Archives of Nethys url.
Saves it as a json file for my TeX spellcards.

Copyright (c) 2021 Bernard Field, GNU GPL-v3.0
"""

from urllib.request import urlopen
import re
import argparse
from warnings import warn
import json

from bs4 import BeautifulSoup, NavigableString, Tag

def url2soup(url):
	"""Takes a webpage url, turns it into BeautifulSoup."""
	page = urlopen(url)
	html = page.read().decode("utf-8")
	soup = BeautifulSoup(html, "html.parser")
	return soup

abbreviations = {
	"PRPG Core Rulebook" : "PF Core",
	"Ultimate Equipment" : "PF Ult Equip",
	"Ultimate Magic" : "PF Ult Magic",
	"Ultimate Combat" : "PF Ult Combat",
	"Advanced Player's Guide" : "PF Adv Play",
	"Advanced Class Guide" : "PF Adv Class",
	"Pathfinder Society Field Guide" : "PFSoc Field Guide",
	"Pathfinder Society Primer" : "PFSoc Primer",
	"Cheliax, Empire of Devils" : "PFC Cheliax",
	"Champions of Purity" : "PFPC Champions of Purity",
	"Advanced Class Origins" : "PFPC Adv Class Origins",
	"Magic Tactics Toolbox" : "PFPC Magic Tactics Toolbox",
	"Monster Codex" : "PF Monster Codex",
	"adept" : "ade",
	"alchemist" : "alc",
	"antipaladin" : "apal",
	"arcanist" : "arc",
	"bard" : "bar",
	"bloodrager" : "brag",
	"cleric" : "cle",
	"druid" : "dru",
	"hunter" : "hun",
	"inquisitor" : "inq",
	"investigator" : "inv",
	"magus" : "mag",
	"medium" : "med",
	"mesmerist" : "mes",
	"occultist" : "occ",
	"oracle" : "ora",
	"paladin" : "pal",
	"psychic" : "psy",
	"ranger" : "ran",
	"redmantisassassin" : "rma",
	"shaman" : "sha",
	"skald" : "ska",
	"sorcerer" : "sor",
	"spiritualist" : "spi",
	"summoner" : "sum",
	"summoner (unchained)" : "sumU",
	"warpriest" : "war",
	"witch" : "wit",
	"wizard" : "wiz"
}

def abbreviate(name):
	"""Returns an abbreviated version of a string name, or just name."""
	try:
		newtxt = abbreviations[name]
	except KeyError:
		warn("Could not abbreviate '{0}'".format(name))
		newtxt = name
	return newtxt

def soup2dict(soup):
	"""
	Gives a dictionary from HTML data on magic items.
	
	Takes a BeautifulSoup from Archives of Nethys.
	Dictionary is able to be turned into a JSON.
	Dictionary has strings which are TeX compatible.
	Output fields are name, aura, cl, slot, price, weight, feat, spells,
	outher_requirements, source, description.
	"""
	# My dictionary to return
	json = {}
	# I only expect one table, and it has one span,
	# and that is where the data of interest is.
	span = soup.table.span
	name = _name_from_span(span)
	if name is not None:
		json['name'] = name
	source = _source_from_span(span)
	if source is not None:
		json['source'] = source
	aura = _aura_from_span(span)
	if aura is not None:
		json['aura'] = aura
	cl = _CL_from_span(span)
	if cl is not None:
		json['cl'] = cl
	slot = _slot_from_span(span)
	if slot is not None:
		json['slot'] = slot
	price = _price_from_span(span)
	if price is not None:
		json['price'] = price
	weight = _weight_from_span(span)
	if weight is not None:
		json['weight'] = weight
	description = _description_from_span(span)
	if description is not None:
		json['description'] = description
	feat, spells, others = _construction_from_span(span)
	json['feat'] = feat
	json['spells'] = spells
	json['other_requirements'] = others
	return json
	
def _name_from_span(span):
	# The name is easy. It is in the h1 header.
	# Strip leading and trailing whitespace
	return span.h1.text.strip()

def _source_from_span(span):
	spantxt = span.text
	# source appears between the words Source and Aura, immediately
	# after the title.
	startind = spantxt.find("Source ")+len("Source ")
	endind = spantxt.find("Aura")
	# Error checking: we did not find the names
	if startind < len("Source "):
		warn("We could not find 'Source '. Skipping element 'source'")
	elif endind == -1:
		warn("We could not find 'Aura'. Skipping element 'source'")
	else:
		# Top priority is PF Core.
		if "PRPG Core Rulebook" in spantxt[startind:endind]:
			return "PF Core"
		# May have multiple sources listed
		sources_raw = spantxt[startind:endind].split(', ')
		# In the end, I only want to show one source.
		# As a brief heuristic, we'll take the last one, but later
		# I'd probably want to build a ranking of sources to pick.
		source = sources_raw[-1]
		# Remove the page number, which is at the end
		ind = source.find(" pg. ")
		source = source[:ind]
		# Convert the full name to an acceptable abbreviation
		return abbreviate(source)

def _aura_from_span(span):
	spantxt = span.text
	# aura appears between the words Aura and CL, immediately
	# after the source.
	startind = spantxt.find("Aura ")+len("Aura ")
	endind = spantxt.find("CL")
	# Error checking: we did not find the names
	if startind < len("Aura "):
		warn("We could not find 'Aura '. Skipping element 'aura'")
	elif endind == -1:
		warn("We could not find 'CL'. Skipping element 'aura'")
	else:
		# Get the aura, remove trailing whitespace and semicolons
		aura = spantxt[startind:endind].strip(' ;')
		return aura

def _CL_from_span(span):
	# Find the CL tag. It is <b>CL</b>
	cltag = span.find("b", string="CL")
	if cltag is None:
		warn("Could not find CL tag. Skipping element 'cl'")
		return None
	# The next sibling should be the string we want
	cl = str(cltag.next_sibling)
	# Strip non-numeric characters
	return re.sub("[^0-9]", "", cl)

def _slot_from_span(span):
	# The <b>Slot</b> tag is the one we want.
	tag = span.find("b", string="Slot")
	if tag is None:
		warn("Could not find Slot tag. Skipping element 'slot'")
		return None
	# The next sibling should be the string we want
	# Strip spaces
	slot = str(tag.next_sibling).strip()
	# Strip trailing semicolon
	if slot[-1] == ";":
		slot = slot[0:-1]
	# If this is just a dash, make it TeX-friendly.
	if slot == "—":
		slot = "--"
	return slot

def _price_from_span(span):
	# The first <b>Price</b> tag is the one we want.
	tag = span.find("b", string="Price")
	if tag is None:
		warn("Could not find Price tag. Skipping element 'price'")
		return None
	# The next sibling should be the string we want
	# But, we might have multiple items, with logos interspersing.
	text_list = []
	for elem in tag.next_siblings:
		if isinstance(elem, Tag):
			if elem.name == "b" or elem.name == "h3":
				# Reached the end of the Price entry
				break
			text_list.append(elem.text)
		else:
			text_list.append(str(elem))
	price = ''.join(text_list)
	# Strip spaces
	price = str(price).strip()
	# Strip trailing semicolon
	if price[-1] == ";":
		price = price[0:-1]
	return price

def _weight_from_span(span):
	# The <b>Weight</b> tag is the one we want.
	tag = span.find("b", string="Weight")
	if tag is None:
		warn("Could not find Weight tag. Skipping element 'weight'")
		return None
	# The next sibling should be the string we want
	# Strip spaces, punctuation
	slot = str(tag.next_sibling).strip(' ;.')
	# If this is just a dash, make it TeX-friendly.
	if slot == "—":
		slot = "--"
	return slot

def _description_from_span(span):
	# The description is one or more paragraphs of text which may
	# contain some formatting.
	# It resides between the h3 tag "Description" and h3 tag "Construction"
	tag = span.find("h3", string="Description")
	if tag is None:
		warn("Could not find Description tag. Skipping element 'description'")
		return None
	text_list = []
	found_end = False
	# Step through each element until we reach the end of the description
	for elem in tag.next_siblings:
		if isinstance(elem, Tag):
			# Found end of Description
			if elem.name == 'h3':
				found_end = True
				break
			# Found a newline
			elif elem.name == 'br':
				# TeX newline, with escaped backslashes for JSON.
				text_list.append('\\\\')
			# Found bold text
			elif elem.name == 'b':
				text_list.append('\\textbf{{{0}}}'.format(elem.text))
			# Found italic text
			elif elem.name == 'i':
				text_list.append('\\textit{{{0}}}'.format(elem.text))
			# Unsorted list
			elif elem.name == 'ul':
				text_list.append(_ul_process(elem))
			# Table
			elif elem.name == 'table':
				text_list.append(htmltable2latex(elem))
			# Unknown tag
			else:
				warn("Found unknown tag '{0}' in Description.".format(elem.name))
				# Just apply plain text
				text_list.append(elem.text)
		else:
			# The other option is NavigableString
			text_list.append(str(elem))
	if not found_end:
		warn("Did not find h3 block after Description.")
	text = ''.join(text_list)
	text = texify(text)
	return text

def texify(text):
	# Converts problematic characters into TeX compatible ones.
	# Carriage returns should be removed.
	text = re.sub('\r', '', text)
	# Minus sign
	text = re.sub('\u2013', '$-$', text)
	# Dash
	text = re.sub('—', '--', text)
	# Apostrophe
	text = re.sub('\u2019', "'", text)
	# Double quotes
	text = re.sub('\u201c', "''", text)
	text = re.sub('\u201d', "''", text)
	# Percentage, only if not already escaped.
	text = re.sub(r'(?<!\\)%', r'\\%', text)
	# Newline should become linebreak
	text = text.replace('\n','\\\\')
	return text

def _ul_process(ul):
	# Process a <ul> environment for the description
	# While I could render this as an itemize environment, it would be
	# more compact to represent as items separated by newlines.
	item_list = []
	for item in ul.children:
		item_list.append(_parse_basic_text(item))
	# Join the elements of the list together.
	return '\n'+'\n'.join(item_list)+'\n'

def _parse_basic_text(item, warn_msg="Found unknown tag '{0}'."):
	# Parses an element which is just text with basic formatting
	# Italics, bold.
	text_list = []
	for elem in item.children:
		if isinstance(elem, Tag):
			# Found bold text
			if elem.name == 'b':
				text_list.append('\\textbf{{{0}}}'.format(elem.text))
			# Found italic text
			elif elem.name == 'i':
				text_list.append('\\textit{{{0}}}'.format(elem.text))
			# Unknown tag
			else:
				warn(warn_msg.format(elem.text))
				# Just apply plain text.
				text_list.append(elem.text)
		else:
			# If it isn't a Tag, it should be NavigableString
			text_list.append(str(elem))
	return ''.join(text_list)

def htmltable2latex(table):
	# Processes a HTML table tag to a LaTeX string
	text_list = []
	text_list.append('\\begin{tabular}')
	# Determine the number of columns
	ncols = len(table.tr.contents)
	text_list.append('{'+'c'*ncols+'}')
	# Go through the table row by row
	for row in table.children:
		if isinstance(row, Tag):
			row_list = []
			for entry in row.children:
				row_list.append(_parse_basic_text(entry))
			text_list.append('&'.join(row_list))
			text_list.append('\\\\')
	text_list.append('\\end{tabular}')
	return ''.join(text_list)

def _construction_from_span(span):
	# Returns a tuple of strings: (feat, spells, others)
	# The construction of an object has up to three sets of requirements.
	# 1) The Feats needed to craft it.
	# 2) The spells needed (which are always in italics).
	# 3) Any further requirements.
	# It also has a Cost/Price, but we're ignoring that.
	tag = span.find("h3", string="Construction")
	if tag is None:
		warn("Could not find Construction tag. Skipping.")
		return None
	# The next tag is expected to be <b>Requirements</b>
	tag = tag.next_sibling
	tag_list = []
	text_list = []
	# Grab all the of the requirements
	for elem in tag.next_siblings:
		if isinstance(elem, Tag):
			if elem.name == "b":
				# Found the end of the Requirements.
				break
			else:
				text_list.append(elem.text)
		else:
			text_list.append(str(elem))
		tag_list.append(elem)
	# Find the first and last italicised element
	italic_list = []
	for i in range(len(tag_list)):
		if isinstance(tag_list[i], Tag):
			italic_list.append(i)
	if not italic_list:
		# No italicised elements. No spells
		# Sort between crafting feats and other parts.
		text = ''.join(text_list)
		splittxt = text.split(', ')
		feat_list = []
		other_list = []
		for s in splittxt:
			if "Craft" in s or "Forge" in s:
				feat_list.append(s)
			else:
				other_list.append(s)
		feat = ', '.join(feat_list)
		others = ', '.join(other_list)
		spells = ''
	else:
		# There are spells
		# They sit in between the feat and other requirements
		feat = ''.join(text_list[0:min(italic_list)])
		spells = ''.join(text_list[min(italic_list):max(italic_list)+1])
		others = ''.join(text_list[max(italic_list)+1:])
	# Strip leading and trailing punctuation and whitespace
	punctuation = ' ,.;:'
	feat = feat.strip(punctuation)
	others = others.strip(punctuation)
	spells = spells.strip(punctuation)
	# Remove a trailing ' and'
	if feat[-4:] == " and":
		feat = feat[:-4]
	feat = texify(feat)
	spells = texify(spells)
	others = texify(others)
	# Set empty values to None
	if not feat: feat = None
	if not spells: spells = None
	if not others: others = None
	# Return a tuple
	return (feat, spells, others)
	

if __name__ == "__main__":
	# Set up the argument parser.
	descr = """
	Web scraper for turning Magic Item entries in Archives of Nethys into
	JSON files that can be parsed by LaTeX.
	"""
	parser = argparse.ArgumentParser(description=descr)
	help = "URL of page to read."
	parser.add_argument('-u', '--url', type=str, help=help)
	help = "Output filename. Defaults to printing to stdout."
	parser.add_argument('-o', '--output', type=str, help=help)
	# Parse arguments
	args = parser.parse_args()
	if args.url is None:
		raise TypeError("--url or -u is a required argument.")
	# Check if the URL points to the right website.
	if not (args.url.startswith("https://aonprd.com/")
	        or args.url.startswith("https://www.aonprd.com/")):
		raise ValueError("URL does not point to https://aonprd.com/")
	soup = url2soup(args.url)
	data = soup2dict(soup)
	# Store some metadata
	data["url"] = args.url
	# To JSON string
	json = json.dumps(data, indent=4)
	if args.output is None:
		print(json)
	else:
		with open(args.output, 'w') as f:
			f.write(json)
