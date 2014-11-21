
var title, year, rating, length, description, imageLink, staring, genres, hidden;
var url = '';
var casper = require('casper').create();
var x = require('casper').selectXPath;

casper.userAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36');

function undetected() {
    var busted = __utils__.getElementsByXPath('//*[text() = "Enter the characters you see below"]');
    var toReturn = false;
    if(busted) {
	var image = __utils__.getElementsByXPath('/html/body/div/div[1]/div[3]/div/div/form/div[1]/div/div/div[1]/img');
	casper.echo('&&&&&&& captcha is at ' + image.src);
	this.download(image, image.split('/')[-1]);
	toReturn = image;
    }
    else {
	toReturn = true;
    }
    return busted;
}

function getTitle() {
    title = document.querySelectorAll('#aiv-content-title');
    return Array.prototype.map.call(title, function(e) {
	var toProcess = e.innerHTML.toString();
	var firstHTML = toProcess.indexOf('<');
	return toProcess.substring(0, firstHTML).trim();
    });
}

function getYear() {
    year = document.querySelectorAll('#aiv-content-title > span.release-year');
    return Array.prototype.map.call(year, function(e) {
	return e.innerHTML.trim();
    });
}

function getRating() {
    rating = document.querySelectorAll('#aiv-content-title > span:nth-child(2)');
    return Array.prototype.map.call(rating, function(e) {
	return e.innerHTML.trim();
    });
}

function getLength() {
    length = document.querySelectorAll('#dv-dp-left-content > div.dp-main-meta.js-hide-on-play > div > dl > dd:nth-child(4)');
    return Array.prototype.map.call(length, function(e) {
	return e.innerHTML.trim();
    });
}

function getDescription() {
    description = document.querySelectorAll('#dv-dp-left-content > div.dp-main-meta.js-hide-on-play > div > div > p');
    return Array.prototype.map.call(description, function(e) {
	return e.innerHTML.trim();
    });
}

function getImageLink() {
    imageLink = document.querySelectorAll('#dv-dp-left-content > div.dp-left-meta.js-hide-on-play > div > div > img');
    return Array.prototype.map.call(imageLink, function(e) {
	return e.src;
    });
}

function getStars() {
    staring = document.querySelectorAll('#dv-center-features > div:nth-child(1) > div > table > tbody > tr:nth-child(3) > td');
    return Array.prototype.map.call(staring, function(e) {
	return e.innerHTML;
    });
}

function getGenres() {
    genres = document.querySelectorAll('#dv-center-features > div:nth-child(1) > div > table > tbody > tr:nth-child(1) > td');
    return Array.prototype.map.call(genres, function(e) {
	return e.innerHTML;
    });
}

function getDetails() {
    hidden = casper.evaluate(undetected);
    if(hidden) {
	casper.echo('image: ' + hidden);
	title = casper.evaluate(getTitle);
	year = casper.evaluate(getYear);
	rating = casper.evaluate(getRating);
	length = casper.evaluate(getLength);
	description = casper.evaluate(getDescription);
	imageLink = casper.evaluate(getImageLink);

	casper.echo('#' + title + '#,#' + year + '#,#' + rating + '#,#' + length + '#,#' + description + '#,#' + imageLink + "#"); 

    }
    else {
	casper.echo('we got caaaaught' + hidden);
    }
}

casper.start('www.google.com', function() {
    url = casper.cli.get(0).trim();
});

casper.then(function() {
    this.open(url);
    casper.wait(6000, function() {


	getDetails();

    });
});

casper.then(function() {
    this.exit();
});


casper.run(function() {
});

