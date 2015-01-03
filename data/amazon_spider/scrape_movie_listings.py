import subprocess
from subprocess import Popen, STDOUT, PIPE
import csv
import StringIO
import time
import threading
import signal
import os
import time
import redis

movie_file = "./csvs/movie_listng.csv"
movies = []

# global stats object
global_stats = dict()
global_stats['name'] = 'global_stats'
global_stats['total_movies'] = 0
global_stats['unadded_movies'] = 0
global_stats['total_ratings'] = 0
global_stats['unadded_ratings'] = 0
global_stats['ratings_per_minute'] = 0
global_stats['estimated_time_to_completion'] = 0

def read_movie_listing_csv():
    to_read = open(movie_file, "r")
    reader = csv.reader(to_read)
    for rows in reader:
        movies.append({'id': rows[0], 'url': rows[1], 'image': rows[2], 'rating': rows[3], 'times_rated': rows[4], 'scraped_ratings': rows[5], 'title': rows[6], 'year': rows[7], 'last_updated': rows[8]})

def run_popen_with_timeout(command_string, timeout, input_data):
    """
    Run a sub-program in subprocess.Popen, pass it the input_data,
    kill it if the specified timeout has passed.
    returns a tuple of success, stdout, stderr
    """
    restarts = 0
    kill_check = threading.Event()
    def _kill_process_after_a_timeout(pid):
        os.kill(pid, signal.SIGTERM)
        kill_check.set() # tell the main routine that we had to kill
        # use SIGKILL if hard to kill...
        global restarts
        restarts = restarts + 1
        return
    p = Popen(command_string, shell=True, stdout=PIPE, stderr=PIPE)
    pid = p.pid
    watchdog = threading.Timer(timeout, _kill_process_after_a_timeout, args=(pid, ))
    watchdog.start()
    (stdout, stderr) = p.communicate(input_data)
    watchdog.cancel() # if it's still waiting to run
    success = not kill_check.isSet()
    kill_check.clear()
    return (success, stdout, stderr, restarts)

"""
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
"""

"""
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
"""

def process_movie(row):
    valid_movie = False
    if len(row) == 6:
        valid_movie = True
        to_add = dict()
        to_add['url'] = row[0]
        to_add['title'] = row[1]
        to_add['times_rated'] = row[2]
        if(to_add['times_rated']):
            to_add['times_rated'] = to_add['times_rated'].replace(',','')
        to_add['year'] = row[3]
        to_add['image'] = row[4]
        to_add['rating'] = row[5]
        link = row[0].split('/')
        to_add['id'] = link[5]
        to_add['last_updated'] = None
        to_add['scraped_ratings'] = None
        movies.append(to_add)
    return valid_movie

def update_global_stats():
    total_movies = 0
    unadded_movies = 0
    total_ratings = 0
    unadded_ratings = 0
    for movie in movies:
        total_movies = total_movies + 1
        if not movie['last_updated']:
            unadded_movies = unadded_movies + 1
        total_ratings = int(movie['times_rated']) + total_ratings
        if not movie['scraped_ratings']:
            unadded_ratings = int(movie['times_rated']) + unadded_ratings
    global_stats['total_movies'] = total_movies
    global_stats['unadded_movies'] = unadded_ratings
    global_stats['total_ratings'] = total_ratings
    global_stats['unadded_ratings'] = unadded_ratings

def scrape_popular_movies():
    popular_scrape = dict()
    popular_scrape['name'] = 'popular_scrape'
    popular_scrape['start_time'] = time.clock()
    popular_scrape['last_thread_start'] = time.clock()
    popular_scrape['last_thread_finish'] = time.clock()
    popular_scrape['last_thread_restarts'] = 0
    popular_scrape['total_restarts'] = 0
    popular_scrape['remaining_pages'] = 400
    popular_scrape['time_per_page'] = 0
    popular_scrape['estimated_time_reamining'] = 0

    #for i in range(1, 400):
    for i in range(1, 4):
        popular_scrape['last_thread_start'] = time.clock()
        popular_scrape['last_thread_restarts'] = 0
        url = "\'http://smile.amazon.com/s/ref=sr_pg_3?rh=n%3A7589478011%2Cn%3A7589479011&page=" + str(i) + "&sort=popularity-rank&ie=UTF8\'"    
        command_string = "proxychains casperjs --web-security=false movie_listings.js " + url
        success = False
        valid_result = False
        while not success and not valid_result:
            success, output, error, restarts = run_popen_with_timeout(command_string, 60, '')
            output = StringIO.StringIO(output)
            csvreader = csv.reader(output, delimiter=',', quotechar='#')
            for row in csvreader:
                result = process_movie(row)
                if not valid_result and result:
                    valid_result = True
            if not success and not valid_result:
                time.sleep(60)
            popular_scrape['last_thread_restarts'] = popular_scrape['last_thread_restarts'] + restarts
            popular_scrape['total_restarts'] = popular_scrape['total_restarts'] + restarts
        time.sleep(15)
        
        r = redis.Redis()
        update_global_stats()
        popular_scrape['last_thread_time'] = (time.clock() - popular_scrape['last_thread_start']) *1000 
        popular_scrape['remaining_pages'] = popular_scrape['remaining_pages'] - 1
        popular_scrape['time_per_page'] = ((time.clock() - popular_scrape['start_time']) * 1000)/i
        popular_scrape['estimated_time_remaining'] = (popular_scrape['time_per_page'] * ((popular_scrape['remaining_pages']) - i))/60
        r.publish('amazon_spider', global_stats)
        r.publish('amazon_spider', popular_scrape)

# load movies into memory
read_movie_listing_csv()

# if never run before, scrape all the movies, else scrape new ones 
if len(movies) == 0:
    scrape_popular_movies()
    # scrape other movies
    # sort by totall # of ratings
    # write to csv
else:
    pass

# scrape ratings and information for each movie
