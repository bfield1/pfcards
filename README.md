# pfcards
### Reference cards for Pathfinder 1e, with web scraping and LaTeX formatting.

Copyright (C) 2021 Bernard Field

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.


Content of example reference cards included in this repository are copyright
Paizo Publishing and are used under the Open Game License v1.0a.

## Introduction

When playing Pathfinder, I like to have reference cards for things like spells
and magic items. This allows me to refer to the details of a spell without
having to hunt down which book it comes from and finding it within the book.

To achieve consistent formatting, I used LaTeX.

Since virtually all content for Pathfinder is available freely online via
websites such as the Archives of Nethys <https://www.aonprd.com/>, I built
some automated Python scripts to scrape data from the Archives of Nethys to
populate a JSON file, which I can then read using LaTeX, usually with a minimum
of manual editing.

## Requirements

The web scraping script was written in Python 3. It relies on the Beautiful
Soup 4 library for performing the web scraping.

The LaTeX class requires LuaLaTex or similar, because it uses Lua to read the
JSON files.

The web scraper and the LaTeX class are independent. You can generate JSON
files by hand for LaTeX, or you can build your own formatter to read the JSON
files you generate. The web scraper assumes the output goes into LaTeX and
formats the description accordingly, but you can edit that manually if that
doesn't work.

## Usage

### web\_scrape.py

I have a separate web scraping script for magic items and for spells, although
their usage is the same.

(In principle I could merge them, but there is no urgency for me to do so.)

web\_scrape.py is intended to be run from the command line.

```
./web_scrape.py -u https://aonprd.com/<pathtopage> -o <output file.json>
```
Two arguments are provided.

- -u, --url, The URL of the page containing the relevant information. This URL
must start with "https://aonprd.com/" or "https://www.aonprd.com/".

- -o, --output, Filename to save the JSON file to. If not provided, prints to
stdout.

A limitation: This script only reads the first entry on a page. This can be
problematic when a page has multiple entries. In such a situation, you will
need to populate/modify fields manually in a text editor.

### pfcards

A LaTeX document class dedicated to typesetting reference cards.

The preamble should contain:

```TeX
\documentclass{pfcards}

\setspelldir{<spellJSON_directory>}
\setitemdir{<itemJSON_directory>}
```
The commands `\setspelldir` and `\setitemdir` set the directory to the files.
The `\spellfromjson` and \itemfromjson` commands prepend the directories
specified in these respective commands to any files specified in them.
Omitting these commands defaults to the current directory.

Within the document, there are two commands you should use.
```TeX
\spellfromjson{<file>}
```
This generates a spell card from a JSON file.
```TeX
\itemfromjson{<file>}
```
This generates a magic item card from a JSON file.

The JSON file for spells contains an object with the following name/value pairs:

- name : string (spell name)
- school : string (school of magic)
- level : string (spell level(s))
- time : string or int (casting time)
- components : string (components to cast the spell)
- range : string (range of the spell)
- area : string or null
- target : string or null
- effect : string or null (should have one of area, target, or effect. If multiple
	provided, prints one of them. I may change this in future.)
- duration : string (spell duration)
- save : string (whether the spell allows a saving throw)
- sr : string (whether the spell allows Spell Resistance)
- description : string (body text, spell description)
- source : string (abbreviated source reference)

The JSON file for items contains an object with the following name/value pairs:
- name : string (item name)
- aura : string (school of magic and strength of item aura)
- cl : string or int (caster level of item)
- slot : string (magic item slot)
- price : string (price of magic item)
- weight : string (weight of magic item)
- description : string (body text, item description)
- source : string (abbreviated source reference)
- spells : string or null (spells requires to craft the item)
- feat : string or null (feats requires to craft the item)
- other_requirements : string or null (other requirements for crafting the
	item. Expect at least one of these three to be non-null.)

Strings should be LaTeX-compatible. Backslashes need to be escaped with
another backslash.

The document fits two rows of four cards per page. For optimal formatting,
place each fromjson command on a separate line, but do not include any blank
lines between them (except optionally where there would be a linebreak).

If you are really keen you can use lower level macros to generate cards without
reading JSON files. However, I don't guarantee that interface will stay
consistent, so I won't write documentation here. If you want, dig around in
pfcards.cls, looking at `\spellblock`, `\spellcard`, and `\itemcard`.
