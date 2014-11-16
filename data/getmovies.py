import subprocess
from py2neo import cypher

def splitLinks(links):
    links = links.split('\n')
    for link in links:
        if len(link) > 0:
            processLink(link)

def processLink(link):
    splitLink = link.split('/')
    # this is pretty awful looking - should be a better way to do this although it works
    if len(splitLink) >= 6:
        link = splitLink[0] + '/' + splitLink[1] + '/' + splitLink[2] + '/' + splitLink[3] + '/' + splitLink[4] + '/' + splitLink[5]
        saveMovie(splitLink[5], link)

def saveMovie(movieid, link):
    session = cypher.Session("http://localhost:7474")
    tx = session.create_transaction()
    # would look better to do it propper like with the variables instead of a string
    tx.append("CREATE (MOVIE {amazon_link:'" + link + "',amazon_id:'" + movieid + "'})")
    tx.commit()

output = subprocess.check_output(['proxychains','casperjs','movies.js'])
print output
splitLinks(output)
