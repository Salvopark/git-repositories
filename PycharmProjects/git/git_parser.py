"""
Ian Gilbert
improved python script using gitPython.
contains all current parsing scripts.
"""
import git                      #used for git operations (clone, pull, log)
import re                       #used for parsing log files
import os                       #used for file handling
from collections import Counter #used to count each author's commits in getAuthors() method
from datetime import date       #creates a shorthand for date (for start/end Date in 'history' methods)
import datetime                 #used for NOW global constant
import time                     #used to compare current time with a repository's age

#global constants
NOW = datetime.datetime.now()   #the current time this script is running.

def getPathName(url):
    """
    getPathName(url)
    Takes in a git url and returns a unique* pathname.
    *not necessarily 100% unique, but unique enough for now. It's possible that two
    users could upload the same github project name.
    url: the url link (should end with .git) to clone/pull from.
    """
    #gets directory from url
    d = url.rfind('github.com/')
    directory = url[d+11:-4]
    return directory    

def urlClone(url):
    """
    urlClone(url)
    Takes in a url from user and clones/pulls a repository for it.
    Creates a repo object (for git commands) and returns it to be used for other methods.
    url: the url link (should end with .git) to clone/pull from.
    """
    #typesafe: if url does not have .git at the end
    if ".git" not in url:
        url += ".git"
    #create repositories folder if it doesn't exist
    if not os.path.isdir('repositories'):
        os.mkdir('repositories')
    #get path name
    directory = 'repositories/'+getPathName(url)
    #if directory doesn't exist, clone
    if not os.path.isdir(directory):
        try:
            d = directory.rfind('/')
            os.makedirs(directory[:d])
            #accesses GitBash directly (not optimal - probably OK)
            git.Git(directory[:d]).clone(url)
        except:
            #invalid url.
            return
    #set repository
    try:
        repo = git.Repo(directory)
        assert not repo.bare
    except:
        print("Error: Invalid url.")
        return
    #if the repository is at least one day old, pull a new version.
    if (os.path.getmtime(directory)+86400 < time.time()):
        o = repo.remotes.origin
        o.pull()
    return repo
def getAuthorHistory(repo,author,startDate=date(1,1,1),endDate=NOW):
    """
    getAuthorHistory(repo,author,startDate,endDate)
    Gets an author's commit history (when they commited, why, changes)
    Commit Hash, Date/Time, Reason, Files Changed (if applicable)
    repo: the repository to parse.
    author: the name of the author who's commit history is to be found.
    startDate: the lower time bound to search, defaults to JAN 1, 0001
    endDate: the upper time bound to search, defaults to current day
    """
    outjson = open('static/authorHistory.json','w',encoding='utf8')
    #converting dates to something git bash understands
    startDate = '--since=' + startDate.strftime('%Y-%m-%d')
    endDate = '--until=' + endDate.strftime('%Y-%m-%d')
    author = '--author=' + str(author)
    try:
        log = repo.git.log(author,
                           '--date=format:%m-%d-%Y %H:%M:%S',
                           '--pretty=format:hash:%H%ndate:%cd%nreason:%f%n',
                           '--name-status',
                           startDate,endDate)
    except:
        print("Error: Author Not Found.")
        return
    #even if log doesn't crash, author data might still be absent for various reasons.
    if not log:
        #Error: No data.
        return
    log = iter(log.splitlines())
    outjson.write('[')
    for line in log:
        #if line starts with 'hash:' write the rest of the line
        if re.search('hash:',line):
            outjson.write('\n\t{')
            m = line[re.search('hash:',line).end():]
            outjson.write('\n\t\t"hash": "%s",'%m)
        #if line starts with a date, write the line as is
        elif re.search('date:',line):
             m = line[re.search('date:',line).end():]
             outjson.write('\n\t\t"date": "%s",'%m)
        #if line starts with 'reason:' write the rest of the line
        elif re.search('reason:',line):
            m = line[re.search('reason:',line).end():]
            m = m.replace('"',"'")
            outjson.write('\n\t\t"reason": "%s"\n\t},'%m)
        #if line starts with a single capital char + a tab, write the filename after
        elif re.search('^[A-Z]\t',line):
            #Note: -5 is hardcoded based on tab formatting and utf8 encoding.
            #Big changes to the JSON output format will break this.
            outjson.seek(outjson.tell()-5,os.SEEK_SET) 
            outjson.write(',\n\t\t"changes":[')
            #for each file found, write ',fileName'
            while True:
                m = re.search('^[A-Z]\t',line)
                if m == None:
                    break
                outjson.write('\n\t\t\t{"file": "%s"},'%line[m.end():])
                try: #read next line
                    line = next(log)
                except: #EoF
                    break
            #finish change block
            outjson.seek(outjson.tell()-1,os.SEEK_SET)
            outjson.write('\n\t\t]\n\t},')
    #moves back 1 char to overwrite the last ','
    outjson.seek(outjson.tell()-1,os.SEEK_SET)
    outjson.write('\n]')
def getAuthors(repo,limit=0):
    """
    getAuthors(repo,limit)
    Gets a list of authors and the # of commits they've done.
    Author Name, Number of Commits
    repo: the repository to parse.
    sortType: how to sort data.'A'/'a' is alphabetical, otherwise it sorts by # of commits.
    limit: how many authors should be listed.
    """
    if limit < 0:
        limit = 0 #error check: no negatives please.
    log = repo.git.log('--format=%aN')
    loglist = []
    #putting all names into a list
    for line in log.splitlines():
        loglist.append(line)
    #creating counters for each name
    c = Counter(loglist)
    outjson = open('static/authors.json','w',encoding='utf8')
    #start JSON
    outjson.write('[')
    #temporary list to hold values based on sortType
    temp = []
    total = 0 #adds up all commits while iterating
    c = c.most_common()
    for key in c:
        temp.append([key[0],key[1]])
        total += key[1]
    #write to file
    for entry in temp:
        outjson.write('\n\t{\n\t\t"author": "%s",\n\t\t"commits": %s,\n\t\t"percent": %s\n\t},'% (entry[0],entry[1],round(entry[1]/total,4)))
        #limiter
        limit -= 1
        if limit == 0:
            break
    #overwrite last ',' and finish
    outjson.seek(outjson.tell()-1,os.SEEK_SET)
    outjson.write('\n]')

def getTotalCommits(repo,limit=0,sort=True):
    """
    getTotalCommits(repo,limit)
    Gets file change info from a repo.
    Specifically: filename, numberOfCommits, percent of total commits
    repo: the repository to parse.
    limit: how many entries to return.
    sort: sort in ascending or descending order (based on commits). True = descending, False = ascending.
    """
    
    if limit < 0:
        limit = 0 #error check: no negatives please.
    log = repo.git.log('--name-status')
    fileDict =  {}
    #parse out file changes
    for line in log.splitlines():
        print(line)
        #gets the changed files and save in a dictionary
        m = re.search('^[A-Z]\t',line)
        if m:
            #track filenames + # of times they've been changed
            fileDict[line[m.end():]] = fileDict.get(line[m.end():],0) + 1
    #sort files from highest number of changes to lowest
    data = sorted(fileDict.items(),key=lambda x: x[1],reverse=sort)
    #find total commits
    c = 0
    for i in data:
        c += i[1]
    outjson = open('static/commitInfo.json','w',encoding='utf8')
    outjson.write('[')
    #get working directory of repository
    d = repo.working_tree_dir.rfind('repositories')
    d = 'repositories/'+repo.working_tree_dir[d+13:] + '/'
    d = d.replace('\\','/')
    for key,value in data:
        try:
            #find size of file
            size = os.stat(d+key).st_size
        except:
            print("Error: File no longer exists.")
            size = 0
        #handle non-english characters:
        #Not currently working. This workaround keeps a vaild .json in most cases, but the
        #characters show up as "suzeyu\323\2345\122\232android\334" etc. this has to do with
        #the path name itself not playing well in Python data formats; data pulled straight
        #from git log doesn't have the same issue.
        #Perhaps the solution lies there (pulling data straight from git log, somehow).
        #key = key.encode('utf-8')
        key = key.replace('"',"")
        outjson.write('\n\t{\n\t\t"name": "%s",\n\t\t"commits":%s,\n\t\t"percent":%s,\n\t\t"size":%s\n\t},'%(key,value,round(value/c,4),size))
        #limiter
        limit -= 1
        if limit == 0:
            break
    #overwrite last ',' and finish
    outjson.seek(outjson.tell()-1,os.SEEK_SET)
    outjson.write('\n]')
def getFileHistory(repo,file,startDate=date(1,1,1),endDate=NOW):
    """
    getFileHistory(repo,file,startDate,endDate)
    Gets the full commit history for a given file.
    Commit Hash, Date/Time, Commiter, Reason
    repo: the repository to parse.
    file: the name of the file who's commit history is to be found.
    startDate: the lower time bound to search, defaults to JAN 1, 0001
    endDate: the upper time bound to search, defaults to current day
    """
    outjson = open('static/fileHistory.json','w',encoding='utf8')
    #setup start/end dates
    startDate = '--since=' + startDate.strftime('%Y-%m-%d')
    endDate = '--until=' + endDate.strftime('%Y-%m-%d')
    try:
        log = repo.git.log('--pretty=format:\t{\n\t\t"hash": "%H",\n\t\t"date": "%cd",\n\t\t"author": "%aN",\n\t\t"reason": "%f"\n\t},',
                           '--date=format:%m-%d-%Y %H:%M:%S',
                           startDate, endDate, file)
    except:
        print("Error: File Not Found.")
        return
    outjson.write('[\n')
    outjson.write(log)
    #moves back 1 char to overwrite the last ','
    outjson.seek(outjson.tell()-1,os.SEEK_SET)
    outjson.write('\n]')
"""      
Testing Block
"""
# print(getPathName("https://github.com/bitcoin/bitcoin.git"))
#repo = urlClone("https://github.com/bitcoin/bitcoin.git")
#getAuthorHistory(repo, "MarcoFalke", date(1, 1, 1), NOW)
#print(getPathName("https://github.com/bitcoin/bitcoin.git"))

#Foreign Characters Test
#repo = urlClone("https://github.com/suzeyu1992/repo.git")
#getTotalCommits(repo,20)
#getAuthors(repo,20)
#getFileHistory(repo,"README.md",date(2016,9,17),date(2020,1,1))
#getAuthorHistory(repo,"suzeyu",date(2016,9,17),date(2020,1,1))
