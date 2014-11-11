
var links = [];
var stars = [];
var date = [];
var username = [];
var userID = [];
var url = 'http://smile.amazon.com/Hunger-Games-Catching-Fire/dp/B00I2TW0UO/ref=sr_1_1?s=instant-video&ie=UTF8&qid=1415560244&sr=1-1';
var casper = require('casper').create();
var maxRatingsLoops = 10;

casper.userAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36');

function getStars() {
    stars = document.querySelectorAll('#productReviews > tbody > tr > td:nth-child(1) div:nth-child(2) > span:nth-child(1) > span > span');
    return Array.prototype.map.call(stars, function(e) {
	return e.innerHTML.substring(0, 3);
    });
}

function getDate() {
    date = document.querySelectorAll('#productReviews > tbody > tr > td:nth-child(1)  div:nth-child(2) > span:nth-child(2):not(.crVotingButtons) > nobr');
    return Array.prototype.map.call(date, function(e) {
	return e.innerHTML;
    });
}

function getUsername() {
    username = document.querySelectorAll('#productReviews > tbody > tr > td:nth-child(1) div:nth-child(3) > div:nth-child(1) > div:nth-child(2) > a:nth-child(1) > span');
    return Array.prototype.map.call(username, function(e) {
	return e.innerHTML;
    });
}

function getUserID() {
    userID = document.querySelectorAll('#productReviews > tbody > tr > td:nth-child(1) div:nth-child(3) > div:nth-child(1) > div:nth-child(2) > a:nth-child(1)');
    return Array.prototype.map.call(userID, function(e) {
	return e.getAttribute('href').split('/')[4];
    });
}

function getMovieDetails() {
    casper.echo('movie details go here');
}

function getRatings() {
    stars = casper.evaluate(getStars);
    date = casper.evaluate(getDate);
    username = casper.evaluate(getUsername);
    userID = casper.evaluate(getUserID);

    for(var i = 0; i < stars.length; i++) {
	casper.echo('***' + stars[i] + '***,***' + date[i] + '***,***' + username[i] + '***,***' + userID[i] + '***\n'); 
    }

    var nextLink = 'body > table > tbody > tr > td:nth-child(1) > table:nth-child(9) > tbody > tr > td:nth-child(1) > div > span > a:nth-child(4)'; // this fails once you leave the first page - the child part is wrong - need to rethink

    if (casper.visible(nextLink) && maxRatingsLoops > 0) {
	maxRatingsLoops = maxRatingsLoops - 1;
	casper.wait(180000, function() {
	    casper.thenClick(nextLink);
	    casper.wait(10000, function() {
		casper.then(getRatings);
	    });
	});
    } else {
	if(maxRatingsLoops > 0) {
	    var js = casper.evaluate(function() {
		return document; 
	    });	
	    casper.echo(js.all[0].outerHTML); 
	}
        casper.echo("END");
    }
}

casper.start(url, function() {
});

casper.then(function () {
    getMovieDetails();
});

casper.then(function() {
    casper.wait(6000, function () {
	casper.click('#revSum > div > div > div.a-fixed-left-grid-col.a-col-left > div > a');
    });
});

casper.then(function() {
    casper.wait(6000, function() {
	getRatings();
    });
});

casper.run(function() {
});

