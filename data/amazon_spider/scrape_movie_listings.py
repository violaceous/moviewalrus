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
import json

movie_file = "./csvs/movie_listing.csv"
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
    reader = csv.reader(to_read, delimiter=',', quotechar='#')
    for row in reader:
        movies.append({'title': row[0], 'url': row[1], 'image': row[2], 'rating': row[3], 'times_rated': row[4], 'scraped_ratings': row[5], 'id': row[6], 'year': row[7], 'last_updated': row[8]})
    to_read.close()

def write_movie_listing_csv():
    to_write = open(movie_file, "w")
    writer = csv.writer(to_write, delimiter=',', quotechar='#')
    for row in movies:
        writer.writerow([row['title'], row['url'], row['image'], row['rating'], row['times_rated'], row['scraped_ratings'], row['id'], row['year'], row['last_updated']])
    to_write.close()
    

def run_popen_with_timeout(command_string, timeout, input_data):
    """
    Run a sub-program in subprocess.Popen, pass it the input_data,
    kill it if the specified timeout has passed.
    returns a tuple of success, stdout, stderr
    """
    restarts = {'value': 0} #getting around lack of nonlocal in 2.7
    kill_check = threading.Event()
    def _kill_process_after_a_timeout(pid):
        os.kill(pid, signal.SIGTERM)
        kill_check.set() # tell the main routine that we had to kill
        # use SIGKILL if hard to kill...
        restarts['value'] += 1
        return
    p = Popen(command_string, shell=True, stdout=PIPE, stderr=PIPE)
    pid = p.pid
    watchdog = threading.Timer(timeout, _kill_process_after_a_timeout, args=(pid, ))
    watchdog.start()
    (stdout, stderr) = p.communicate(input_data)
    watchdog.cancel() # if it's still waiting to run
    success = not kill_check.isSet()
    kill_check.clear()
    return (success, stdout, stderr, restarts['value'])

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

        if not any(movie['id'] == to_add['id'] for movie in movies): 
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
    global_stats['unadded_movies'] = unadded_movies
    global_stats['total_ratings'] = total_ratings
    global_stats['unadded_ratings'] = unadded_ratings

def scrape_popular_movies():
    popular_scrape = dict()
    popular_scrape['name'] = 'popular_scrape'
    popular_scrape['start_time'] = time.clock()
    popular_scrape['last_thread_start'] = time.clock()
    popular_scrape['last_thread_restarts'] = 0
    popular_scrape['total_restarts'] = 0
    popular_scrape['remaining_pages'] = 400
    popular_scrape['time_per_page'] = 0
    popular_scrape['thread_status'] = 'Just starting'
    r = redis.Redis()

    for i in range(1, 400):
        popular_scrape['last_thread_start'] = time.clock()
        popular_scrape['last_thread_restarts'] = 0
        url = "\'http://smile.amazon.com/s/ref=sr_pg_3?rh=n%3A7589478011%2Cn%3A7589479011&page=" + str(i) + "&sort=popularity-rank&ie=UTF8\'"    
        command_string = "proxychains casperjs --web-security=false movie_listings.js " + url
        success = False
        valid_result = False
        while not success and not valid_result:
            popular_scrape['thread_status'] = 'about to run external command'
            r.publish('amazon_spider', json.dumps(popular_scrape, ensure_ascii=False))
            success, output, error, restarts = run_popen_with_timeout(command_string, 60, '')
            popular_scrape['thread_status'] = 'returned from running external command'
            r.publish('amazon_spider', json.dumps(popular_scrape, ensure_ascii=False))
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
        
        update_global_stats()
        popular_scrape['last_thread_time'] = (time.clock() - popular_scrape['last_thread_start']) *1000 
        popular_scrape['remaining_pages'] = popular_scrape['remaining_pages'] - 1
        popular_scrape['time_per_page'] = ((time.clock() - popular_scrape['start_time']) * 1000)/i
        popular_scrape['estimated_time_remaining'] = int((popular_scrape['time_per_page'] * ((popular_scrape['remaining_pages']) - i))/60)
        r.publish('amazon_spider', json.dumps(global_stats, ensure_ascii=False))
        r.publish('amazon_spider', json.dumps(popular_scrape, ensure_ascii=False))

# I HAVE to refactor this somehow.
def scrape_recent_movies():
    popular_scrape = dict()
    popular_scrape['name'] = 'recent_scrape'
    popular_scrape['start_time'] = time.clock()
    popular_scrape['last_thread_start'] = time.clock()
    popular_scrape['last_thread_restarts'] = 0
    popular_scrape['total_restarts'] = 0
    popular_scrape['remaining_pages'] = 400
    popular_scrape['time_per_page'] = 0
    popular_scrape['thread_status'] = 'just_starting'
    r = redis.Redis()

    for i in range(1, 400):
        popular_scrape['last_thread_start'] = time.clock()
        popular_scrape['last_thread_restarts'] = 0
        url = "\'http://smile.amazon.com/s/ref=sr_pg_3?rh=n%3A7589478011%2Cn%3A7589479011&page=" + str(i) + "&sort=date-desc-rank&ie=UTF8\'"  
        command_string = "proxychains casperjs --web-security=false movie_listings.js " + url
        success = False
        valid_result = False
        while not success and not valid_result:
            popular_scrape['thread_status'] = 'about to run external command'
            r.publish('amazon_spider', json.dumps(popular_scrape, ensure_ascii=False))
            success, output, error, restarts = run_popen_with_timeout(command_string, 60, '')
            popular_scrape['thread_status'] = 'returned from running external command'
            r.publish('amazon_spider', json.dumps(popular_scrape, ensure_ascii=False))
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
        
        update_global_stats()
        popular_scrape['last_thread_time'] = (time.clock() - popular_scrape['last_thread_start']) *1000 
        popular_scrape['remaining_pages'] = popular_scrape['remaining_pages'] - 1
        popular_scrape['time_per_page'] = ((time.clock() - popular_scrape['start_time']) * 1000)/i
        popular_scrape['estimated_time_remaining'] = int((popular_scrape['time_per_page'] * ((popular_scrape['remaining_pages']) - i))/60)
        r.publish('amazon_spider', json.dumps(global_stats, ensure_ascii=False))
        r.publish('amazon_spider', json.dumps(popular_scrape, ensure_ascii=False))

# load movies into memory
read_movie_listing_csv()

# if never run before, scrape all the movies, else scrape new ones 
if len(movies) == 0:
    scrape_popular_movies()
    scrape_recent_movies()
    write_movie_listing_csv()
else:
    pass

# scrape ratings and information for each movie
