---
name: agentic-latex
description: Use this skill when asked to help edit or write scientific papers in LaTeX using agentic commands. Use it when \acite, \awrite, \afill, \atable, or \afigure are mentioned.
---

# Writing and editing LaTeX papers with agentic commands

## What this skill does

It allows users to mark parts of the paper that you can help write. These parts are marked with LaTeX macros that normally reduce to placeholder text (e.g., \ldots). When prompted, you will replace occurrences of these macros with your own text. Sometimes more precise instructions are given, but not always. You should always read enough surrounding text to understand what needs to be written.

Before writing text, scan the entire document to understand the paper's context and structure. You should also read the abstract and introduction to understand the paper's goals and contributions. If conclusions are present, read them to understand what the authors think they have accomplished. Then work on the \atable and \afigure commands first, if they are present, before attempting other commands, so that figures and tables are available for reference while writing text.

If at any point you are unsure what to write or at what level of detail, stop and ask for further instructions.

After you have written the text, you should re-read it for the flow. You should also check that it is consistent with the rest of the paper, the abstract and introduction. If you find any inconsistencies, you should ask for further instructions.

The macros are described in sections below.

## \acite
\acite - Add a citation to a paper. Given the context surrounding the \acite command, you will find a relevant paper and add a citation to it. Once you have identified the citation, you will add it by following the adstex-references skill. You should never write your own BibTeX entry; using adstex-references ensures that the paper exists.

## \afill
\afill{description} - Fill in a placeholder, i.e., a small piece of text such as an equation or a number. You should not hallucinate content. For example, if the text says "We show that error bars are improved by \afill \%", you should not make up a number. The number should be supported by one of the following: 1) the context of the paper (i.e., an existing figure or table), 2) code that you have executed (or whose output you can access), or 3) a reference to a paper that you have read. If the description is missing, it should be obvious from the context.


## \awrite
\awrite{description} - Write a new larger section, a paragraph, or a few paragraphs. You should write the text based on your knowledge and available context. You should also make sure that the text is consistent with the rest of the paper, including the abstract and introduction. If you find any inconsistencies, you should ask for further instructions. If the description is missing, it should be obvious from the context.

If there are tables or figures in the same section, you should reference them in the text appropriately. 


## \atable
\atable{description} - Create a table. The table should follow this standard LaTeX outline:
```
\begin{table}
\centering
%% To reproduce: <provide instructions or code to reproduce the table>
\begin{tabular}{<column specifiers>}
<table contents>
\end{tabular}
\caption{...}
\label{tab:identifier} 
\end{table}
```
This outline does not have to be followed word for word. If you need longtable, another environment, or extra packages for column descriptors, you should use them.

The label should be unique, short, descriptive, and always preceded by "tab:". The caption should be a short description of the table. The contents of the table should be based on your knowledge and available context. You should also make sure that the table is consistent with the rest of the paper, including the abstract and introduction. If you find any inconsistencies, you should ask for further instructions. If the description is missing, it should be obvious from the context.

If the table is not copied directly from a referenced source such as a Markdown file, you should create a simple Python script, either in the relevant project directory or in latex/tables/, that can be used to generate the table. In either case, the information required to reproduce the table should be included in the commented "%% To reproduce: ..." section of the table.

## \afigure
\afigure{description} - Create a figure. The figure should follow this standard LaTeX outline:
```
\begin{figure}
\centering  
%% To reproduce: <provide instructions or code to reproduce the figure>
\includegraphics[width=\linewidth]{<path to figure>}
\caption{...}
\label{fig:identifier}
\end{figure}
```
This outline does not have to be followed word for word. If you need subfigures, another environment, or extra packages, you should use them.

The label should be unique, short, descriptive, and always preceded by "fig:". The caption should be a short description of the figure. The contents of the figure should be based on your knowledge and available context. You should also make sure that the figure is consistent with the rest of the paper, including the abstract and introduction. If you find any inconsistencies, you should ask for further instructions. If the description is missing, it should be obvious from the context.

Vector formats (PDF) are always preferred over raster formats (PNG, JPG), unless it makes sense to use a raster format (e.g., for images or Mollweide figures).

If you have created the figure, you should always provide instructions to reproduce it. If you need to create a script to generate the figure, you should create a simple Python script, either in the relevant project directory or in latex/figures/, that can be used to generate the figure. In either case, the information required to reproduce the figure should be included in the commented "%% To reproduce: ..." section of the figure.
