% Copyright (c) 2021 Bernard Field, GNU GPL-v3.0
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{pfcards}[2021/07/11 Pathfinder TTRPG Reference Cards]

\LoadClass[8pt,a4paper]{extarticle}
\RequirePackage[margin=1cm,landscape]{geometry}

\pagestyle{empty}
\setlength\tabcolsep{.5pt}
\setlength{\parindent}{0pt}

% Commands for setting the directories in which the JSON files live.
\newcommand{\spelldir}{./}
\newcommand{\setspelldir}[1]{\renewcommand{\spelldir}{#1}}
\newcommand{\itemdir}{./}
\newcommand{\setitemdir}[1]{\renewcommand{\itemdir}{#1}}

% For debugging Lua code.
\newwrite\luadebug
\immediate\openout\luadebug luadebug.lua
\AtEndDocument{\immediate\closeout\luadebug}
\newcommand\directluadebug{\immediate\write\luadebug}

% Commands for generating spellcards.
\newcommand{\spellblock}[9]{\textit{School}: #1. \textit{Level}: #2. \textit{Casting Time}: #3. \textit{Components}: #4. \textit{Range}: #5. \textit{Area/Target/Effect}: #6. \textit{Duration}: #7. \textit{Save?}: #8. \textit{SR?}: #9.}

\newcommand{\spellcard}[4]{\fbox{\begin{minipage}[c][0.48\textheight][t]{0.24\textwidth}
			\textbf{\underline{#1}} \hfill #4
			
			#2
			\vspace{2pt}
			\hrule
			\vspace{2pt}
			#3
	\end{minipage}}
}

\newcommand{\get}[1]{\directlua{tex.sprint(tab["#1"])}}
\newcommand{\getATE}[0]{\directlua{
	if not (tab.area == nil) then
	tex.sprint(tab.area)
	elseif not (tab.target == nil) then
	tex.sprint(tab.target)
	elseif not (tab.effect == nil) then
	tex.sprint(tab.effect)
	end
	}}
\newcommand{\spellfromjson}[1]{\directlua{
	require("lualibs.lua")
	tab = nil
	local f = io.open('\spelldir #1', 'r')
	local s = f:read('*a')
	f:close()
	tab = utilities.json.tolua(s)}%
	\spellcard{\get{name}}
	{\spellblock{\get{school}}{\get{level}}{\get{time}}{\get{components}}{\get{range}}{\getATE{}}{\get{duration}}{\get{save}}{\get{sr}}}
	{\get{description}}{\get{source}}}


% Commands for generating magic item cards.
\newcommand{\itemcard}[5]{\fbox{\begin{minipage}[c][0.48\textheight][t]{0.24\textwidth}
			\textbf{\underline{#1}} \hfill #5
			
			#2
			\vspace{2pt}
			\hrule
			\vspace{2pt}
			#3
			\vfill
			\hrule
			\vspace{2pt}
			#4
	\end{minipage}}
}

\newcommand{\itemfromjson}[1]{\directlua{
	require("lualibs.lua")
	tab = nil
	local f = io.open('\itemdir #1', 'r')
	local s = f:read('*a')
	f:close()
	tab = utilities.json.tolua(s)}%
	\itemcard{\get{name}}
	{\textit{Aura:} \get{aura}. \textit{CL:} \get{cl}. \textit{Slot:} \get{slot}. \textit{Price:} \get{price}. \textit{Weight:} \get{weight}.}
	{\get{description}}
	{\underline{Crafting:} \printcrafting{}}
	{\get{source}}}

\newcommand{\printcrafting}[0]{\directlua{
	if tab.spells == nil and not (tab.other_requirements == nil) then
	tex.sprint(tab.feat .. ", " .. tab.other_requirements .. ".")
	elseif tab.spells == nil and tab.other_requirements == nil then
	tex.sprint(tab.feat .. ".")
	elseif not (tab.spells == nil) and tab.other_requirements == nil then
	tex.sprint(tab.feat .. ", \string\\textit{" .. tab.spells .. "}.")
	else
	tex.sprint(tab.feat .. ", \string\\textit{" .. tab.spells .. "}, " .. tab.other_requirements .. ".")
	end
}}
