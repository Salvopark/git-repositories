Git Repositories
Ian Gilbert, Aaron Salvo, Babita Thapa, Ryan Groves

For epic.py

Requirements:
import sqlite3, urllib, json, os
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from passlib.hash import pbkdf2_sha256
import gc.

Summary: This is the work horse of the web application, it creates the application and then pulls in the settings from config.py as well as create the database. Then it creates a set up and tear down for each HTTP request. This means that this function will be called before a request is routed, and app.teardown request is called after everything is finished. This is followed by each route in which we have added the need to be logged in to access, if the conditions for the accessing the routes are not met the application will tell you what you need to do, when conditions are met it will let you know that you were successful. The routes correspond with templates for each page or part of the application, the templates all extend layout.html which impose html onto the pages, it just seems more convenient to package it this way to streamline the project. 
        •	The routes include:
            o	index(): which renders index.html, the home page.
            o	add_entry(): Not currently used, but could be used to add entries to a table, renders table.html
            o	form(): Used as input for creating the graphs, asks for title ,description, graph type, and what you features of the repository you would like to check.
            o	graph(): renders the graph.htm template, used to show the graph you have chosen.
            o	percentage_graph(): renders the percentage_graph.html.
            o	authhistory_graph(): renders the authhistory_graph.htm.
            o	login(): renders login.html, used to log into the web application for use.
            o	logout(): logs you out of the session.
            o	register(): renders redister.html, used to create new users. Must provide a username, email address, and password.
            o	page_not_found(): renders 404.html, used as an errorhandler. When a page can not be found it shows a trendy photo of storefronts when 404 as signs.
            
Templates folder: holds the html templates that are used in the application.
Static: holds the .json files used to create the graphs as well as the 404 and style.css.

For config.py
Summary: Allows for a quick configuration of Admin settings for the web application, simply designate what you would prefer for each option before running epic.py and it will be pulled in and set as is. Currently there are seven options that may or may not be needed for the application, was more of a convenience thing.

for git_parser.py:
Summary: script takes in a GIT URL (from GitHub, for instance) from the user and loads it into a “repo” object. It then can use other methods to parse that repo object for info and saves that info into JSON objects. Currently, only git-based repositories work, and there are no plans to change this.
        •	5 separate methods:
            o	urlClone(url)
                Takes in a url from user and, if the repository is not on file yet, clones it to a “repositories” folder. If the repository exist, pulls a new version every 24h.
            o	getAuthorHistory(repo,author,startDate,endDate)
                Gets a single author’s commit history (timestamps of their commits, reasons why, what files they changed). This history defaults to all commits but can be limited to a specific time period (denoted by start/endDate).
                Creates an “authorHistory.json” file in “static” containing the parsed data.
            o	getFileHistory(repo,filename,startDate,endDate)
                Tracks the changes to a single filename throughout the repository’s history (timestamps of a change, author changing it, reason why). Just like getAuthorHistory, this can be limited to a specific time period.
                Creates an “authorHistory.json” file in “static” containing the parsed data.
            o	getAuthors(repo,limit)
                gets a list of all authors on the repository and the number of commits each one is responsible for. They are organized by whoever has committed the most and can be limited to “top X” (top 10, top 50, etc.).
                Creates an “authorHistory.json” file in “static” containing the parsed data.
            o	getTotalCommits(repo,limit)
                gets a list of all files in the repository, each file’s size, and the number of times each one has been committed/updated. They are organized from most to least and can be limited to “top X” (top 10, top 50, etc.).
                Creates an “authorHistory.json” file in “static” containing the parsed data.
                Each “.json” file produced by its given method is visualized by a graph written using d3.

Requirements:
    •	imports:
        o	re, os, datetime, time
        o	from collections import Counter
        o	git (external library, use: pip install gitpython)
    •	WebApp: the script has no way of receiving user input by design and requires another program to give each method its parameters.
    •	Database: the database stores the “repo” object created by urlClone(). This object is critical for running the other methods.


Dependencies:
    •	WebApp: the WebApp needs this script’s methods in order to parse data from the git repository given by the user.
    •	Graphs: Each graph runs by parsing a JSON object for data, and this script’s methods are what create those JSON objects.

Known Issues:
    •	nonASCII names in a repository directory can cause broken/unreadable .json files. This has to do with how python interprets the OS’s directory, which is language dependent. This is easily reproduced by cloning a repository in a language with non-English characters (such as Chinese) and attempting to run getTotalCommits() with it.
    •	Rare and unreproducible: After first cloning a brand-new repository, the script can crash if you attempt to call a method using that repository right after. This bug has not been fixed, but almost never happens in normal use. The cause remains unknown.
    •	Server is unable to connect to original GitLab repository (it can’t use the Parkside VPN because the VM lacks core requirements) and must be updated manually. This isn’t a problem for users but is for the development team.
    •	getTotalCommit()’s file size portion doesn’t work correctly if the file no longer exists in the repository. It defaults to printing “0 bytes” but a better option in the future is to find the last commit the file existed on and use that file’s size instead.

Future Work:
    •	Complete getAuthor/FileHistory graphs.
    •	Work in a “limit” option into the user form, so the user can choose how many pieces of data to show (i.e. top 5 busiest authors in a repository).
    •	The “Reason” given by getAuthor/FileHistory is heavily sanitized in order to prevent bugs in the resulting JSON object, however it also hurts the readability for the end user.
        o	In low-level terms, git log uses %f as opposed to %s to sanitize the subject, but %s COULD be used if that specific line was parsed and handled separately for special characters. This would be easy to do with getAuthorHistory, difficult for getFileHistory.
    •	In the user form, change the “Graph” dropdown to a simpler toggle form (like bullet points) so it’s quicker for the user to choose what they wish to do.
    •	Add in an option to “always pull” the repository when parsing it. 
    •	User should only need to type in a GitHub URL once. Once a repository has been cloned into the machine, the user should be able to select it somehow. A search function could become necessary in the future, if many repositories are saved.
    •	Find a way to see how often a file is accessed in the repository.
    •	Gitbase:
        o	This is a Go-powered open source project that runs SQL queries on GIT repositories. It’s function is largely the same as our own scripts but could simplify the process by a lot. In the future, we could try researching and swapping the project to using Gitbase instead of python for parsing. Some links:
                    https://opensource.com/article/18/11/gitbase
                    https://github.com/src-d/gitbase

Database:

Dependencies: SQLAlchemy, wtforms, passlib

Database creation:
    Create a new database model as previously demonstrated. From terminal, into the directory where epic.py is contained.Open a python shell in that location. From there, 'from epic import db', and 'db.create_all()' to create all database models into the database.

    Currently, the scripts save a local copy of the repository onto the server and update a single set of json files. Ideally, the local repository is temporarily cloned, the scripts are run to create the json files, then the json files are saved into a database with a key of the repository link and possibly a datetime for update purposes. The cloned repo would then be removed off the system, leaving only that repo's version of its json files behind. That would optimize space in the future.

Graphs:
    The graphs were created using D3, which is one of the most commonly utilized libraries for construction of advanced dynamic graphs. They were written as .html pages and extend the layout.html page, if not written in this way they will not render correctly on the web application. Also, it should be noted that the graph.html is not located in the same directory as the .json files so they will need to be written with the correct calls for the application or they will not work correctly. Many examples of different graphs and their uses and applications can be found at https://github.com/d3/d3/wiki. This is D3’s repository on GitHub and is an absolute wealth of knowledge.


