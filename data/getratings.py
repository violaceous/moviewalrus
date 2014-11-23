import subprocess
from subprocess import Popen
import csv
import StringIO
import thread
import time
from datetime import datetime
from py2neo import cypher
timeout = 60000 # should be able to override this default at launch
loops = 10
concurrent = 5
nextMovies = []
processes = []

def getNextMovies():
    del nextMovies[:]
    session = cypher.Session("http://localhost:7474")
    tx = session.create_transaction()
    tx.append("MATCH (movie:MOVIE) RETURN movie.amazon_link, movie.amazon_id ORDER BY movie.last_updated DESC LIMIT " + str(concurrent))
    movies = tx.commit()
    for i in range(concurrent):
        nextMovies.append(movies[0][i])

def saveMovieDetails(row, movieid):
    now = datetime.now()
    session = cypher.Session("http://localhost:7474")
    tx = session.create_transaction()
    statement = 'MATCH (movie:MOVIE { amazon_id: {movieid} }) SET movie.title = {title}, movie.release_year = {releaseYear}, movie.rating = {rating}, movie.length = {length}, movie.description = {description}, movie.image_link = {imageLink}, movie.last_updated = {now} RETURN movie;'
    tx.append(statement, {'movieid': movieid, 'title': row[0], 'releaseYear': row[1], 'rating': row[2], 'length': row[3], 'description': row[4], 'imageLink': row[5], 'now': now})
    movie = tx.commit()

def processRating(rating, movieid):
    if len(rating) == 4:
        saveUser(rating[3], rating[2])
        saveRating(rating[3], movieid, rating[0], rating[1])

def saveUser(userid, nickname):
    if userid != 'undefined' and nickname != 'undefined':
        session = cypher.Session("http://localhost:7474")
        tx = session.create_transaction()
        try:
            tx.append("CREATE (amazon_user:AMAZON_USER {id:'" + userid + "',nickname:'" + nickname + "'})")
            tx.commit()
        except cypher.TransactionError:
            # user already existed and couldn't be created again. All is well, fail silently.
            bob = 1

def saveRating(userid, movie, stars, date):
    if userid != 'undefined': 
        session = cypher.Session("http://localhost:7474")
        tx = session.create_transaction()
        statement = "MATCH (amazon_user:AMAZON_USER { id:{userid}}) MATCH (movie:MOVIE { amazon_id:{movieid}}) CREATE UNIQUE (amazon_user)-[r:RATING {date:{date}, stars:{stars}}]->(movie) RETURN r;"
        tx.append(statement, {"userid": userid, "movieid": movie, "date": date, "stars": stars})
        tx.commit()

# while loops > 0:
#     loops = loops -1
#     nextMovie = getNextMovie()
#     movieurl = nextMovie.values[0]
#     movieid = nextMovie.values[1]
#     print 'starting processing of ' + movieurl

#     output = subprocess.check_output(['proxychains','casperjs','moviedetails.js',movieurl])
#     print output
#     output = StringIO.StringIO(output)    
#     csvreader = csv.reader(output, delimiter=',', quotechar='#')
#     for row in csvreader:
#         if len(row) == 6:
#             saveMovieDetails(row, movieid)

#     movieurl = movieurl.replace('/dp/', '/product-reviews/')

#     output = subprocess.check_output(['proxychains','casperjs','ratings.js',movieurl])
#     print output
#     output = StringIO.StringIO(output)
#     csvreader = csv.reader(output, delimiter=',', quotechar='#')
#     for row in csvreader:
#         processRating(row, movieid)

def startScrapeMovie(url):
    print "Calling moviedetails.js with " + url
    return Popen(['proxychains','casperjs','--web-security=false','moviedetails.js',url], stdout=subprocess.PIPE)

def startScrapeRatings(url):
    print "Calling ratings.js with " + url
    return Popen(['proxychains','casperjs','--web-security=false','ratings.js',url], stdout=subprocess.PIPE)

def mainThread():
    while True:
        for i in range(concurrent):
            url = nextMovies[i].values[0]
            movieid = nextMovies[i].values[1]
            print "starting the processing for process " + url

            if processes[i]['movie'] is None:
                print 'starting processing of ' + url
                processes[i]['movie'] = startScrapeMovie(url)

            elif processes[i]['movie'].poll() is not None:
                if processes[i]['ratings'] is None:
                    # I should move this to when ratings are back too so it only saves with ratings
                    output = processes[i]['movie'].communicate()[0]
                    print "output from moviedetails.js: " + output 
                    output = StringIO.StringIO(output)
                    csvreader = csv.reader(output, delimiter=',', quotechar='#')
                    for row in csvreader:
                        if len(row) == 6:
                            saveMovieDetails(row, movieid)
                    url = url.replace('/dp/', '/product-reviews/')
                    processes[i]['ratings'] = startScrapeRatings(url)

                elif processes[i]['ratings'].poll() is not None:
                    output = processes[i]['ratings'].communicate()[0]
                    print "output from ratings.js: " + output
                    output = StringIO.StringIO(output)
                    csvreader = csv.reader(output, delimiter=',', quotechar='#')
                    for row in csvreader:
                        processRating(row, movieid)
                    processes[i]['movie'] = None
                    processes[i]['ratings'] = None
                    getNextMovies()
            else:
                print "process " + str(i) + " is waiting for something to finish"

        time.sleep(60)


getNextMovies()

for i in range(concurrent):
    processes.append({'movie':None,'ratings':None})

thread.start_new_thread(mainThread, ())

while 1:
    pass

# This is for testing from a file, unlikely to be needed in the future but still here for now
#with open('someRatings.txt', 'r') as csvfile:
#    csvreader = csv.reader(csvfile, delimiter=',', quotechar='#')
#    for row in csvreader:
#        processRating(row)




