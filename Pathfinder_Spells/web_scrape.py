#!/usr/bin/python3

"""
Scrapes spell data from a given Archives of Nethys url.
Saves it as a json file for my TeX spellcards.
"""

from urllib.request import urlopen
import re
import argparse
from warnings import warn
import json
from collections import Counter

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
        "Adventurer's Guide": "PF Adventurer Guide",
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
	Gives a dictionary from HTML data on spells.
	
	Takes a BeautifulSoup from Archives of Nethys.
	Dictionary is able to be turned into a JSON.
	Dictionary has strings which are TeX compatible.
	Output fields are name, school, classes, level, time, components, range,
	area, target, effect, duraction, save, sr, source, description.
	'classes' is itself a dictionary of numbers.
	"""
	# My dictionary to return
	json = {}
	# I only expect one table, and it has one span,
	# and that is where the data of interest is.
	span = soup.table.span
	# There is a rare case that the first span is empty.
	# In that case, find the next span.
	i = 1
	while not span.contents:
		try:
			span = soup.table.find_all("span")[i]
		except IndexError:
			raise ValueError("Could not find non-empty span within the first table.")
		i += 1
	name = _name_from_span(span)
	if name is not None:
		json['name'] = name
	source = _source_from_span(span)
	if source is not None:
		json['source'] = source
	school = _school_from_span(span)
	if school is not None:
		json['school'] = school
	classes = _classes_from_span(span)
	if classes is not None:
		json['classes'] = classes
		json['level'] = _level_from_classes(classes)
	time = _time_from_span(span)
	if time is not None:
		json['time'] = time
	components = _components_from_span(span)
	if components is not None:
		json['components'] = components
	range = _range_from_span(span)
	if range is not None:
		json['range'] = range
	area = _area_from_span(span)
	json['area'] = area
	target = _target_from_span(span)
	json['target'] = target
	effect = _effect_from_span(span)
	json['effect'] = effect
	if area is None and target is None and effect is None:
		warn("No Area, Target or Effect found.")
	duration = _duration_from_span(span)
	if duration is not None:
		json['duration'] = duration
	save = _save_from_span(span)
	if save is not None:
		json['save'] = save
	sr = _sr_from_span(span)
	if sr is not None:
		json['sr'] = sr
	description = _description_from_span(span)
	if description is not None:
		json['description'] = description
	return json
	
def _name_from_span(span):
	# The name is easy. It is in the h1 header.
	# Strip leading and trailing whitespace
	return span.h1.text.strip()

def _source_from_span(span):
	# Find the Source tag. It is <b>Source</b>
	sourcetag = span.find("b", string="Source")
	if sourcetag is None:
		warn("Could not find Source tag. Skipping element 'source'")
		return None
	# Iterate through the sources.
	sources_raw = []
	for elem in sourcetag.next_siblings:
		if isinstance(elem, Tag):
			# Bold, probably School. We've exhausted the sources.
			if elem.name == "b":
				break
			if elem.name == "a":
				# A link. All sources are linked.
				sources_raw.append(elem.text)
		# Strings of commas separate elements.
	if not sources_raw:
		warn("No sources detected. Skipping element 'source'.")
		return None
	# Top priority is PF Core.
	if "PRPG Core Rulebook" in ''.join(sources_raw):
		return "PF Core"
	# In the end, I only want to show one source.
	# As a brief heuristic, we'll take the first one, but later
	# I'd probably want to build a ranking of sources to pick.
	source = sources_raw[0]
	# Remove the page number, which is at the end
	ind = source.find(" pg. ")
	source = source[:ind]
	# Convert the full name to an acceptable abbreviation
	return abbreviate(source)

def _school_from_span(span):
	tag = span.find("b", string="School")
	if tag is None:
		warn("Could not find School tag. Skipping element 'school'.")
		return None
	# Grab all strings up to the next bold part
	text_list = []
	for elem in tag.next_siblings:
		if isinstance(elem, Tag):
			if elem.name == "b":
				break
			else:
				text_list.append(elem.text)
		else:
			# NavigableString
			text_list.append(str(elem))
	# Join the elements together.
	school = ''.join(text_list).strip(' ;').replace(' ','')
	# Strip out trailing space and semicolons
	# Remove internal spaces as well (they aren't needed)
	# Space removal is slightly overzealous, though.
	school = school.replace('seetext','see text')
	school = school.replace(',',', ')
	return school

def _get_text_from_simple_tag(span, string, warnname=None):
	"""
	Returns the plain text immediately following a bold tag 'string' in span
	
	Throws warning if nothing found is warnname is given.
	"""
	tag = span.find("b", string=string)
	if tag is None:
		if warnname is not None:
			warn("Could not find {0} tag. Skipping element '{1}'.".format(string,warnname))
		return None
	return str(tag.next_sibling)

def _classes_from_span(span):
	# We parse the Level entry and determine what classes can cast this spell
	# and at what levels. Return a dictionary.
	text = _get_text_from_simple_tag(span, "Level", 'classes')
	if text is None:
		return None
	# Split the string into the comma separated values.
	text_list = text.split(',')
	# Go through the list and process each element.
	class_dict = {}
	for item in text_list:
		# Get the level number.
		level = int(item[-1])
		# Get the class name
		cls = item[0:-1].strip()
		class_dict[cls] = level
	return class_dict

def _level_from_classes(classes):
	"""
	Takes the dictionary given by _classes_from_span, and abbreviates the 
	spell level information. For the sake of the spell cards, we shall only
	cover classes who can cast the spell.
	If it is all the same level, just have a single number.
	If there are a small number of exceptions, note them.
	If exceptions are extensive, will need to be explicit.
	"""
	# Count the occurrence of each level.
	# Calling most_common has a list of tuples sorts by frequency.
	level_counter = Counter(classes.values()).most_common()
	# There is only one level. This is the easy case.
	if len(level_counter) == 1:
		return level_counter[0][0]
	# Check if there is an entry with a majority.
	counts = [n[1] for n in level_counter]
	# Also get the unique levels.
	levels = [n[0] for n in level_counter]
	if counts[0] >= sum(counts)/2 and counts[0] > counts[1]:
		main_level = levels.pop(0)
	else:
		main_level = None
	# Go through all the other levels and group their classes together.
	# Essentially, transposing the dictionary classes.
	levellist = []
	for L in levels:
		# e.g. if sorcerer and wizard both cast this spell at 1,
		# then append 'sor/wiz 1' to the list.
		class_list = []
		for key in classes:
			if classes[key] == L:
				class_list.append(abbreviate(key))
		levellist.append('{0} {1}'.format('/'.join(sorted(class_list)),L))
	# Bring it all together.
	leveltxt = ', '.join(levellist)
	if main_level is not None:
		return '{0} ({1})'.format(main_level, leveltxt)
	else:
		return leveltxt	

def _time_from_span(span):
	time = _get_text_from_simple_tag(span, "Casting Time", "time")
	if time is None:
		return None
	time = texify(time.strip(' ;.'))
	return time

def _components_from_span(span):
	comp = _get_text_from_simple_tag(span, "Components", "components")
	if comp is None:
		return None
	comp = texify(comp.strip(' ;.'))
	# We want to compact it a little. The spaces between V, S, M can be removed.
	comp = re.sub(r'([VSMF)]), ',r'\1,',comp)
	# Also remove the leading space before parentheses.
	comp = re.sub(r'([MF]) \(', r'\1(', comp)
	# Compress lbs and gp
	comp = re.sub(r' gp', 'gp', comp)
	comp = re.sub(r' lbs\.', 'lb', comp)
	return comp

def _range_from_span(span):
	range = _get_text_from_simple_tag(span, "Range", 'range')
	if range is None:
		return None
	range = texify(range.strip(' ;.'))
	# Check special cases
	for opt in ["close", "medium", "long"]:
		if range.startswith(opt):
			return opt
	# Compress ft.
	range = re.sub(r' ft.', 'ft', range)
	range = re.sub(' ft', 'ft', range)
	return range

def _ATE_from_span(span, ATE):
	# ATE is "Area", "Target" or "Effect"
	text = _get_text_from_simple_tag(span, ATE)
	if text is None:
		return None
	text = texify(text.strip(' ;.'))
	text = re.sub(r"levels?", "lvl", text)
	text = text.replace(" per ", "/")
	text = re.sub(r'[ -]ft\.', 'ft', text)
	text = re.sub(r' lbs.', 'lb', text)
	return text

def _area_from_span(span):
	return _ATE_from_span(span, "Area")

def _target_from_span(span):
	target = _ATE_from_span(span, "Target")
	if target is None:
		# Check a synonymn
		target = _ATE_from_span(span, "Targets")
	return target

def _effect_from_span(span):
	return _ATE_from_span(span, "Effect")

def _duration_from_span(span):
	# ATE has some nice formatting I'd like to copy.
	duration = _ATE_from_span(span, "Duration")
	if duration is None:
		warn("Could not find Duration tag. Skipping element 'duration'.")
	duration = duration.replace("min.", "min")
	duration = re.sub("minutes?", "min", duration)
	return duration

def _save_from_span(span):
	save = _get_text_from_simple_tag(span, "Saving Throw")
	if save is None:
		# Personal spells don't list the save, because it is always none.
		return "none"
	save = save.strip(' ;.')
	# Abbreviate save names
	save = save.replace("Reflex", "Ref")
	save = save.replace("Fortitude", "Fort")
	return save

def _sr_from_span(span):
	sr = _get_text_from_simple_tag(span, "Spell Resistance")
	if sr is None:
		# Personal spells don't list the SR, because it is always no"
		return "no"
	sr = sr.strip(' ;.')
	return sr

def _description_from_span(span):
	# The description is one or more paragraphs of text which may
	# contain some formatting.
	# It resides between the h3 tag "Description" and the next header tag.
	tag = span.find("h3", string="Description")
	if tag is None:
		warn("Could not find Description tag. Skipping element 'description'")
		return None
	text_list = []
	# Step through each element until we reach the end of the description
	for elem in tag.next_siblings:
		if isinstance(elem, Tag):
			# Found end of Description
			if elem.name == 'h3' or elem.name == 'h2' or elem.name == 'h1':
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
