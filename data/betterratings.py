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
import threading
from threading import Thread
from datetime import datetime
from py2neo import cypher
from Queue import Queue

RATINGS_FILE = open("ratings.txt","a")
DATABASE_ERRORS = open("ratings_database_errors.txt","a")
NUM_THREADS = 5

threads = [None] * NUM_THREADS
q = Queue(maxsize=NUM_THREADS)




class Stats(object):
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

def set_last_updated(movieid):
    session = cypher.Session("http://localhost:7474")
    tx = session.create_transaction()
    now = datetime.now()
    tx.append("MATCH (movie:MOVIE {amazon_id: '" + str(movieid) + "'} ) SET movie.last_updated = '" + str(now) + "'")
    movies = tx.commit()

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

def get_movies(q, pause):
    session = cypher.Session("http://localhost:7474")
    tx = session.create_transaction()
    # tx.append("MATCH (movie:MOVIE) WITH toInt(REPLACE(toString(movie.ratings), ',', '')) as ratings, movie WHERE movie.last_updated IS NULL AND ratings > -1 RETURN movie.amazon_link, movie.amazon_id, ratings ORDER BY ratings DESC LIMIT " + str(NUM_THREADS*50))
    tx.append("MATCH (movie:MOVIE) WITH toInt(REPLACE(toString(movie.ratings), ',', '')) as ratings, movie WHERE movie.last_updated IS NULL AND ratings > -1 AND 500 > ratings RETURN movie.amazon_link, movie.amazon_id, ratings ORDER BY ratings DESC LIMIT " + str(NUM_THREADS*50))
    movies = tx.commit()
    for i in range(NUM_THREADS):
        to_put = []
        to_put.append(movies[0][i].values[0])
        to_put.append(movies[0][i].values[1])
        to_put.append(movies[0][i].values[2])
        to_put.append(pause)
        q.put(to_put)

def write_ratings(queued_ratings, movieid, ratings_file, error_file):
    for rating in queued_ratings:
        saveUser(rating[3], rating[2], ratings_file, error_file)
        saveRating(rating[3], movieid, rating[0], rating[1], ratings_file, error_file)

def processRating(rating, queued_ratings):
    valid_row = False
    if len(rating) == 5:
        queued_ratings.append(rating)
        valid_row = True 
    return valid_row

def saveUser(userid, nickname, ratings_file, error_file):
    if userid != 'undefined' and nickname != 'undefined':
        session = cypher.Session("http://localhost:7474")
        tx = session.create_transaction()
        try:
            ratings_file.write("CREATE (amazon_user:AMAZON_USER {id:'" + userid + "',nickname:'" + nickname + "'})\n")
            tx.append("CREATE (amazon_user:AMAZON_USER {id:'" + userid + "',nickname:'" + nickname + "'})")
            tx.commit()
        except cypher.TransactionError as e:
            error_file.write(e.message + "\n")

def saveRating(userid, movie, stars, date, ratings_file, error_file):
    if userid != 'undefined': 
        session = cypher.Session("http://localhost:7474")
        tx = session.create_transaction()
        try:
            statement = "MATCH (amazon_user:AMAZON_USER { id:{userid}}) MATCH (movie:MOVIE { amazon_id:{movieid}}) CREATE UNIQUE (amazon_user)-[r:RATING {date:{date}, stars:{stars}}]->(movie) RETURN r;\n"
            ratings_file.write("MATCH (amazon_user:AMAZON_USER { id:'" + userid + "') MATCH (movie:MOVIE { amazon_id:'" + movie + "'}) CREATE UNIQUE (amazon_user)-[r:RATING {date: '" + date + "', stars: '" + stars + "' }]->(movie) RETURN r;") 
            tx.append(statement, {"userid": userid, "movieid": movie, "date": date, "stars": stars})
            tx.commit()
        except cypher.TransactionError as e:
            error_file.write(e.message + "\n")

class MovieThread(object): 
    def __init__(self, url, movieid, ratings, pause, i):
        self._url = url
        self._movieid = movieid
        self._ratings = ratings
        self._stats = Stats()
        self._pause = pause
        self._thread_number = i
        self._complete = False
        self.begin_scraping()

    @property
    def url(self):
        return str(self._url)
    @url.setter
    def url(self, value):
        self._url = value

    @property
    def movieid(self):
        return self._movieid
    @movieid.setter
    def movieid(self, value):
        self._movieid = value

    @property
    def ratings(self):
        return self._ratings
    @ratings.setter
    def ratings(self, value):
        self._ratings = value

    @property
    def stats(self):
        return self._stats
    @stats.setter
    def stats(self, value):
        self._stats = value

    @property
    def complete(self):
        return self._complete

    def begin_scraping(self):
        range_start = 1
        range_finish = int(math.ceil(self.ratings/10))
        queued_ratings = []
        for i in range(range_start, range_finish):
            # note that the &s are escaped with \ or else this shits the bed in bash
            url = str.replace(self.url,"/dp/","/product-reviews/") + "/ref=cm_cr_pr_btm_link_2?ie=UTF8\&showViewpoints=1\&sortBy=helpful\&reviewerType=all_reviews\&formatType=all_formats\&filterByStar=all_stars\&pageNumber=" + str(i)
            command_string = "proxychains casperjs --web-security=false pagedratings.js " + url
            success = False
            valid_result = False

            while not success and not valid_result:
                success, output, error = run_popen_with_timeout(command_string, 60, "blah")
                output = StringIO.StringIO(output)
                csvreader = csv.reader(output, delimiter=',', quotechar='#')
                for row in csvreader:
                    result = processRating(row, queued_ratings)
                    if not valid_result and result:
                        valid_result = True
                if not success or not valid_result:
                    time.sleep(60)
                    self.stats.dead_threads += 1

            self.stats.finished_pages += 1
            time.sleep(self._pause)
            self.stats.ellapsed_time = time.clock()
            print("Stats for " + self.url + " " + str(self.stats) + " at " +  str(datetime.now()))
            time_per_page = ((self.stats.ellapsed_time - self.stats.start_time) * 1000) / self.stats.finished_pages
            time_left = math.floor(time_per_page * ((range_finish - range_start) - self.stats.finished_pages)/60)
            print str(self._thread_number) + ": " + str(time_per_page) + " average seconds per page and " + str(time_left) + " minutes estimated until completion"
        ratings_file = open("./ratings/" + self.movieid + ".txt","a")
        errors_file = open("./ratings/" + self.movieid + "_database_errors.txt","a")
        write_ratings(queued_ratings, self.movieid, ratings_file, errors_file)
        ratings_file.close()
        errors_file.close()
        set_last_updated(self.movieid)
        print("Completed " + self.url)
   

def startThread(q, i):
    while True:
        to_pass = q.get()
        MovieThread(to_pass[0], to_pass[1], to_pass[2], to_pass[3], i)
        q.task_done()
     
# start the threads
for i in range(NUM_THREADS):
    worker = Thread(target=startThread, args=(q, i,))
    worker.setDaemon(True)
    worker.start()

while True:
    print("FILLED UP A NEW QUEUE!!!!!!!!!!!!")
    get_movies(q, 15)
    q.join()
