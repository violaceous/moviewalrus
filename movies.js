
var links = [];
var url = 'http://smile.amazon.com/s/ref=s9_hps_bw_clnk_a_v?node=2858778011,7613704011&search-alias=prime-instant-video&sort=csrank&pf_rd_m=ATVPDKIKX0DER&pf_rd_s=center-6&pf_rd_r=03D83JJV25XQ8CDPQVCW&pf_rd_t=101&pf_rd_p=1959989462&pf_rd_i=2858778011&pf_rd_p=1959989462&pf_rd_s=center-10&pf_rd_t=101&pf_rd_i=2858778011&pf_rd_m=ATVPDKIKX0DER&pf_rd_r=03D83JJV25XQ8CDPQVCW';
var casper = require('casper').create();
var maxLoops = 5;

casper.userAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36');

function getLinks() {
    var links = document.querySelectorAll('div > div.a-row.a-spacing-none > div:nth-child(1) > a');
    return Array.prototype.map.call(links, function(e) {
	return e.getAttribute('href');
    });
}

function getMoviesAndWrite(){
    casper.echo('in getMovies');

    /*
     var js = casper.evaluate(function() {
     return document; 
     });	
     casper.echo(js.all[0].outerHTML); 
     */


    links = casper.evaluate(getLinks);

    links = links.join("\n");

    casper.echo(links);

    var nextLink = "#pagnNextLink";

    if (casper.visible(nextLink) && maxLoops > 0) {
	maxLoops = maxLoops - 1;
	casper.wait(180000, function() {
	    casper.echo('passed a wait, about to call thenClick');
	    casper.thenClick(nextLink);
	    casper.wait(10000, function() {
		casper.echo('passed a wait, about to call getMoviesAndWrite');
		casper.then(getMoviesAndWrite);
	    });
	});
    } else {
        casper.echo("END");
    }
}

casper.start(url, function() {
});

casper.then(function () {
    getMoviesAndWrite();
});

casper.run(function() {
});

