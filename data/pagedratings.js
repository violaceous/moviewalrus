
var links = [];
var stars = [];
var date = [];
var username = [];
var userID = [];
var nextLinks = [];
var url = '';
var casper = require('casper').create();
var x = require('casper').selectXPath;
var maxRatingsLoops = 200000;
var delay = 20000;
var filename = "";
var fs = require('fs');

casper.userAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36');

function getStars() {
   // stars = document.querySelectorAll('#productReviews > tbody > tr > td:nth-child(1) div:nth-child(2) > span:nth-child(1) > span > span');
    stars = __utils__.getElementsByXPath('//*[@id="productReviews"]/tbody/tr/td[1]/div/div/span[1]/span[@class!="tiny verifyWhatsThis"]/span');
    return Array.prototype.map.call(stars, function(e) {
	return e.innerHTML.substring(0, 3);
    });
}

function getDate() {
    // date = document.querySelectorAll('#productReviews > tbody > tr > td:nth-child(1)  div:nth-child(2) > span:nth-child(2):not(.crVotingButtons) > nobr');
    date = __utils__.getElementsByXPath('//*[@id="productReviews"]/tbody/tr/td[1]/div/div/span[2]/nobr');
    return Array.prototype.map.call(date, function(e) {
	return e.innerHTML;
    });
}

function getUsername() {
    // username = __utils__.getElementsByXPath('//*[@id="productReviews"]/tbody/tr/td[1]/div/div/div[1]/div[2]/a[1]/span');
    username = __utils__.getElementsByXPath('//*[@id="productReviews"]/tbody/tr/td[1]/div/div/div[1]/div[2]/a[1]/span | //*[@id="productReviews"]/tbody/tr/td[1]/div/div[3 and not (@class = "tiny")]/b');
    return Array.prototype.map.call(username, function(e) {
	return e.innerHTML;
    });
}

function getUserID() {
    // userID = __utils__.getElementsByXPath('//*[@id="productReviews"]/tbody/tr/td[1]/div/div/div[1]/div[2]/a[1 and not (@style) and not (text()="See all my reviews") and not (@target)]');
    userID = __utils__.getElementsByXPath('//*[@id="productReviews"]/tbody/tr/td[1]/div/div/div[1]/div[2]/a[1 and not (@style) and not (text()="See all my reviews") and not (@target)] | //*[@id="productReviews"]/tbody/tr/td[1]/div/div[3 and not (@class = "tiny")]/b');
    return Array.prototype.map.call(userID, function(e) {
	if(e.getAttribute('href')) {
	    return e.getAttribute('href').split('/')[4];
	}
	else {
	    return "undefined";
	}
    });
}

function getNextLink() {
    nextLinks = __utils__.getElementsByXPath('//a[text()="Next ›"]');
    return Array.prototype.map.call(nextLinks, function(e) {
	return e.getAttribute('href');
    });
}

function getRatings() {
    stars = casper.evaluate(getStars);
    date = casper.evaluate(getDate);
    username = casper.evaluate(getUsername);
    userID = casper.evaluate(getUserID);
    nextLinks = casper.evaluate(getNextLink);

    for(var i = 0; i < stars.length; i++) {
	casper.echo('#' + stars[i] + '#,#' + date[i] + '#,#' + username[i] + '#,#' + userID[i] + '#,#' + nextLinks[0] + '#'); 
	var toAppend = '#' + stars[i] + '#,#' + date[i] + '#,#' + username[i] + '#,#' + userID[i] + '#,#' + nextLinks[0] + '#\n';
	fs.write(filename,toAppend,'a');
    }
    casper.exit();
}

casper.start('www.google.com', function() {
    url = casper.cli.get(0).trim();
    casper.echo('passed URL is : ' + url);
    filename = './ratings/' + url.split('/')[5] + '.txt';
});

casper.then(function() {
    this.open(url);
    casper.wait(5000, function() {

	    getRatings();
    });
});

casper.run(function() {
});

