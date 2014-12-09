import subprocess
from subprocess import Popen, STDOUT, PIPE
import csv
import StringIO
import time
import threading
import signal
import os
import time
import math
from py2neo import cypher

RATINGS_FILE = open("ratings.txt","a")
DATABASE_ERRORS = open("ratings_database_errors.txt","a")
NUM_THREADS = 3

class Stats:
    def __init__(self, dead_threads = 0, finished_pages = 0):
        self._dead_threads = dead_threads
        self._finished_pages = finished_pages
        self._start_time = time.clock()
        self._ellapsed_time = time.clock()

    @property
    def dead_threads(self):
        return self._dead_threads

    @dead_threads.setter
    def dead_threads(self, value):
        self._dead_threads = value
    
    @property
    def finished_pages(self):
        return self._finished_pages

    @finished_pages.setter
    def finished_pages(self, value):
        self._finished_pages = value

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        self._start_time = value

    @property
    def ellapsed_time(self):
        return self._ellapsed_time
        
    @ellapsed_time.setter
    def ellapsed_time(self, value):
        self._ellapsed_time = value

    def __str__(self):
        toReturn = ""
        total_time = math.floor((self.ellapsed_time - self.start_time) * 1000)
        unit_of_time = " seconds"
        if total_time > 300:
            unit_of_time = " minutes"
            total_time = math.floor(total_time / 60)
        toReturn+= str(self.finished_pages) + " finished pages "
        toReturn+= "with " + str(self.dead_threads) + " thread restarts "
        toReturn+= "in " + str(total_time) + unit_of_time  
        
        return toReturn
        

def run_popen_with_timeout(command_string, timeout, input_data):
    """
    Run a sub-program in subprocess.Popen, pass it the input_data,
    kill it if the specified timeout has passed.
    returns a tuple of success, stdout, stderr
    """
    kill_check = threading.Event()
    def _kill_process_after_a_timeout(pid):
        os.kill(pid, signal.SIGTERM)
        kill_check.set() # tell the main routine that we had to kill
        # use SIGKILL if hard to kill...
        return
    p = Popen(command_string, shell=True, stdout=PIPE, stderr=PIPE)
    pid = p.pid
    watchdog = threading.Timer(timeout, _kill_process_after_a_timeout, args=(pid, ))
    watchdog.start()
    (stdout, stderr) = p.communicate(input_data)
    watchdog.cancel() # if it's still waiting to run
    success = not kill_check.isSet()
    kill_check.clear()
    return (success, stdout, stderr)


def write_ratings(queued_ratings, movieid):
    for rating in queued_ratings:
        saveUser(rating[3], rating[2])
        saveRating(rating[3], movieid, rating[0], rating[1])
    #update the last_updated date on the movie here

def processRating(rating, queued_ratings):
    valid_row = False
    if len(rating) == 5:
        queued_ratings.append(rating)
        valid_row = True 
    return valid_row

def saveUser(userid, nickname):
    if userid != 'undefined' and nickname != 'undefined':
        session = cypher.Session("http://localhost:7474")
        tx = session.create_transaction()
        try:
            RATINGS_FILE.write("CREATE (amazon_user:AMAZON_USER {id:'" + userid + "',nickname:'" + nickname + "'})\n")
            tx.append("CREATE (amazon_user:AMAZON_USER {id:'" + userid + "',nickname:'" + nickname + "'})")
            tx.commit()
        except cypher.TransactionError as e:
            DATABASE_ERRORS.write(e.message + "\n")

def saveRating(userid, movie, stars, date):
    if userid != 'undefined': 
        session = cypher.Session("http://localhost:7474")
        tx = session.create_transaction()
        try:
            statement = "MATCH (amazon_user:AMAZON_USER { id:{userid}}) MATCH (movie:MOVIE { amazon_id:{movieid}}) CREATE UNIQUE (amazon_user)-[r:RATING {date:{date}, stars:{stars}}]->(movie) RETURN r;\n"
            RATINGS_FILE.write("MATCH (amazon_user:AMAZON_USER { id:'" + userid + "') MATCH (movie:MOVIE { amazon_id:'" + movieid + "'}) CREATE UNIQUE (amazon_user)-[r:RATING {date: '" + date + "', stars: '" + stars + "' }]->(movie) RETURN r;") 
            tx.append(statement, {"userid": userid, "movieid": movie, "date": date, "stars": stars})
            tx.commit()
        except cypher.TransactionError as e:
            DATABASE_ERRORS.write(e.message + "\n")


# this would be the start of a movie based thread. There needs to be a per movie level stats
# object as well as a global object. These ones should be renamed
# we need to loop around this based on logic to get movies with the most ratings that
# haven't been updated recently
# for i in range(0, NUM_THREADS):
#
#


range_start = 1
range_finish = 5
queued_ratings = []
movieid = "B00AOQ8MOQ"
global_stats = Stats()
global_stats.start_time = time.clock()

for i in range(range_start, range_finish):
    local_stats = Stats()
    local_stats.start_time = time.clock()
    url = "\'http://smile.amazon.com/product-reviews/B00AOQ8MOQ/ref=cm_cr_pr_btm_link_2?ie=UTF8&showViewpoints=1&sortBy=helpful&reviewerType=all_reviews&formatType=all_formats&filterByStar=all_stars&pageNumber=" + str(i) + "\'"
    timeout = 60
    command_string = "proxychains casperjs --web-security=false pagedratings.js " + url
    success = False
    valid_result = False

    while not success and not valid_result:
        success, output, error = run_popen_with_timeout(command_string, timeout, "blah")
        output = StringIO.StringIO(output)
        csvreader = csv.reader(output, delimiter=',', quotechar='#')
        for row in csvreader:
            result = processRating(row, queued_ratings)
            if not valid_result and result:
                valid_result = True
        if not success and not valid_result:
            time.sleep(60)
            local_stats.dead_threads += 1
            global_stats.dead_threads += 1

    local_stats.finished_pages += 1
    global_stats.finished_pages += 1
    time.sleep(15)
    local_stats.ellapsed_time = time.clock()
    global_stats.ellapsed_time = time.clock()
    print("The most recent page " + str(local_stats))
    print("All of the pages so far " + str(global_stats))
    time_per_page = ((global_stats.ellapsed_time - global_stats.start_time) * 1000) / global_stats.finished_pages
    time_left = math.floor(time_per_page * ((range_finish - range_start) - global_stats.finished_pages)/60)
    print str(time_per_page) + " average seconds per page and " + str(time_left) + " minutes estimated until completion" 
    
write_ratings(queued_ratings, movieid)


# this would be the end of a movie based thread

RATINGS_FILE.close()
DATABASE_ERRORS.close()


 
