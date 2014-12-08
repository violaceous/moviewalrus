import subprocess
from subprocess import Popen, STDOUT, PIPE
import csv
import StringIO
import time
import threading
import signal
import os
import time
from py2neo import cypher

count = 0;
movie_file = open("movies.txt","a")
database_errors = open("movies_database_errors.txt","a")
dead_threads = 0
finished_pages = 0

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
        global dead_threads
        dead_threads = dead_threads + 1
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

def createMovie(movieid):
    statement = "CREATE (movie:MOVIE {amazon_id:{movieid}})"
    movie_file.write("CREATE (movie:MOVIE {amazon_id: '" + movieid + "')\n")
    session = cypher.Session("http://localhost:7474")
    tx = session.create_transaction()
    try:
        tx.append(statement, {"movieid": movieid})
        tx.commit()
    except cypher.TransactionError as e:
        pass
        database_errors.write(e.message + "\n")

def processMovie(row):
    valid_movie = False
    if len(row) == 6:
        valid_movie = True
        link = row[0]
        title = row[1]
        ratings = row[2]
        year = row[3]
        image = row[4]
        rating = row[5]
        link = link.split('/')
        movieid = link[5]
        link = link[0] + '/' + link[1] + '/' + link[2] + '/' + link[3] + '/' + link[4] + '/' + link[5]
        createMovie(movieid)

        statement = "MATCH (movie:MOVIE {amazon_id:{movieid}}) SET movie += {amazon_link:{link}, title:{title}, year:{year}, image:{image}, rating:{rating}, ratings:{ratings}}"
        session = cypher.Session("http://localhost:7474")
        tx = session.create_transaction()
        movie_file.write("MATCH (movie:MOVIE {amazon_id:'" + movieid + "') SET movie += {amazon_link: '" + link + "', title: '" + title + "', year: '" + year + "', image: '" + image + "', rating: '" + rating + "', ratings: '" + ratings + "'})\n")
        try:
            tx.append(statement, {"link": link, "movieid": movieid, "title": title, "year": year, "image": image, "rating": rating, "ratings": ratings})
            tx.commit()
        except cypher.TransactionError as e:
            pass
            database_errors.write(e.message + "\n")
    return valid_movie

start_time = time.clock() 
start_dead_threads = 0
elapsed_time = time.clock()
# should be 1 through 400
range_start = 1
range_finish = 400
for i in range(range_start, range_finish):
    # this is just by newest
    #url = "\'http://smile.amazon.com/s/ref=sr_pg_3?rh=n%3A7589478011%2Cn%3A7589479011&page=" + str(i) + "&sort=date-desc-rank&ie=UTF8\'"
    # this is by new and popular
    url = "\'http://smile.amazon.com/s/ref=sr_pg_3?rh=n%3A7589478011%2Cn%3A7589479011&page=" + str(i) + "&sort=popularity-rank&ie=UTF8\'"
    print "Last paged finished in " + str((time.clock() - start_time) * 1000) + " seconds and restarted " + str(dead_threads - start_dead_threads) + " times"
    print "Finished total of " + str(finished_pages) + ", " + str(dead_threads) + " threads restarted"
    if finished_pages > 0:
        time_per_page = ((time.clock() - elapsed_time) * 1000)/finished_pages
    else:
        time_per_page = 180
    time_left = time_per_page * ((range_finish - range_start) - finished_pages)
    print str(time_per_page) + " average seconds per page and " + str(time_left/60) + " minutes estimated until completion"
    global start_time
    start_time = time.clock()
    global start_dead_threads
    start_dead_threads = dead_threads
    timeout = 60
    command_string = "proxychains casperjs --web-security=false movies.js " + url
    success = False
    valid_result = False
    while not success and not valid_result:
        success, output, error = run_popen_with_timeout(command_string, timeout, "blah")
        output = StringIO.StringIO(output)
        csvreader = csv.reader(output, delimiter=',', quotechar='#')
        for row in csvreader:
            result = processMovie(row)
            if not valid_result and result:
                valid_result = True
        if not success and not valid_result:
            time.sleep(60)
    finished_pages = finished_pages + 1
    time.sleep(15)

movie_file.close()
database_errors.close()


 
