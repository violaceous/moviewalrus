var delay = 6000; // timeout between pages
var links = [];
var title = [];
var year = [];
var image = [];
var ratings = [];
var rating = [];
var movies = [];

// use this one to keep up to date
// var url = 'http://smile.amazon.com/s/ref=sr_st_date-desc-rank?qid=1416059713&rh=n%3A7589478011%2Cn%3A7589479011&sort=date-desc-rank';
var url = 'http://smile.amazon.com/s/ref=sr_pg_3?rh=n%3A7589478011%2Cn%3A7589479011&page=5&sort=date-desc-rank&ie=UTF8';
var fs = require('fs');
var x = require('casper').selectXPath;
var pages = "";
var casper = require('casper').create();
var maxLoops = 0; // used to limit number of repeats for testing the script

casper.userAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36');

function getMovies() {
    var elements = __utils__.getElementsByXPath('//*[@class="s-item-container"]');
    return Array.prototype.map.call(elements, function(element) {
        return element.innerHTML;
    });
}

function getMoviesAndWrite(){

    /* to get the html
     var js = casper.evaluate(function() {
     return document; 
     });	
     pages = pages + js.all[0].outerHTML;
    */
    
    movies = casper.evaluate(getMovies);

    for (var i = 0; i < movies.length; i++) {
	var movie = document.createElement('div');
	movie.innerHTML = movies[i];

	links[i] = movie.querySelectorAll('div > div.a-row.a-spacing-none > div:nth-child(1) > a')[0].getAttribute('href');
	title[i] = movie.querySelectorAll('div > div.a-row.a-spacing-none > div:nth-child(1) > a > h2')[0].innerHTML;

	var curRatings = movie.querySelectorAll('div > div.a-row.a-spacing-none > div.a-row.a-spacing-top-mini.a-spacing-none > a')[0];
	if(typeof(curRatings) !== 'undefined') {
	    ratings[i] = curRatings.innerHTML;
	} else {
	    ratings[i] = "";
	}

	var curYear = movie.querySelectorAll('div > div.a-row.a-spacing-none > div:nth-child(1) > span.a-size-small.a-color-secondary')[0];
	if(typeof(curYear) !== 'undefined') {
	    year[i] = curYear.innerHTML;
	} else {
	    year[i] = "";
	}

	var curImage = movie.querySelectorAll('div > div.a-row.a-spacing-base > div > a > img')[0];
	if(typeof(curImage) !== 'undefined') {
	    image[i] = curImage.getAttribute('src');
	} else {
	    image[i] = "";
	}
	var curRating = movie.querySelectorAll('div > div.a-row.a-spacing-none > div:nth-child(1) > div:nth-child(5) > div > span.a-size-small.a-color-secondary')[0];
	if(typeof(curRating) !== 'undefined' && curRating.innerHTML != 'CC') {
	    rating[i] = curRating.innerHTML;
	} else {
	    rating[i] = "";
	}

    }



    for (var i = 0; i < links.length; i++) {
	casper.echo('#' + links[i] + '#,#' + title[i] + '#,#' + ratings[i] + '#,#' + year[i] + '#,#' + image[i] + '#,#' + rating[i] + '#');
    }


    var nextLink = "#pagnNextLink";

    if (casper.visible(nextLink) && maxLoops > 0) {
	maxLoops = maxLoops - 1;
	self.wait(6000, function() {
	    casper.thenClick(nextLink);
	    self.wait(10000, function() {
		casper.then(getMoviesAndWrite);
	    });
	});
    } else {
	this.exit();
    }
}


casper.start('www.google.com', function() {
    url = casper.cli.get(0).trim();
});

casper.then(function() {
    casper.wait(6000, function() {
	this.open(url);
    });
});

casper.then(function() {
    getMoviesAndWrite();
});

casper.run(function() {
});

