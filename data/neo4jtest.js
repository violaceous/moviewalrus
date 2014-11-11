
var casper = require('casper').create();


casper.userAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36');

function getMovieDetails() {
    casper.echo('movie details go here');
}


casper.start("www.google.com", function() {
});

casper.then(function () {
    getMovieDetails();
});



casper.run(function() {
});

