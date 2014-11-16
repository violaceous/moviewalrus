
var links = [];
var stars = [];
var date = [];
var username = [];
var userID = [];
var url = '';
var casper = require('casper').create();
var maxRatingsLoops = 5;
var delay = 60000;

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

function getRatings() {
    stars = casper.evaluate(getStars);
    date = casper.evaluate(getDate);
    username = casper.evaluate(getUsername);
    userID = casper.evaluate(getUserID);

    for(var i = 0; i < stars.length; i++) {
	casper.echo('***' + stars[i] + '***,***' + date[i] + '***,***' + username[i] + '***,***' + userID[i] + '***'); 
    }

    var x = require('casper').selectXPath;
    var nextLinkXPath = "//a[text()='Next ›']";

    if (casper.visible(x(nextLinkXPath)) && maxRatingsLoops > 0) {
	maxRatingsLoops = maxRatingsLoops - 1;
	casper.wait(delay, function() {
	    casper.thenClick(x(nextLinkXPath));
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
    }
}

casper.start('www.google.com', function() {
    url = casper.cli.get(0).trim();
});

casper.then(function() {
    this.open(url);
    casper.wait(6000, function() {
	getRatings();
    });
});

casper.then(function() {
    this.exit();
});


casper.run(function() {
});

