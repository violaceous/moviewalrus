
var casper = require('casper').create({
});

casper.start("www.google.com", function() {

});

casper.then(function() {
    casper.page.injectJs('jquery.js');
    casper.echo('injected jquery');
    var result = casper.evaluate(function() {
	var toReturn = "aaa";
	$.ajax({
	    type:"POST",
	    url: "http://localhost:7474/db/data/transaction/commit",
	    accept: "application/json; charset=UTF-8",
	    contentType:"application/json",
	    headers: { 
		"X-Stream": "true"    
	    },
	    data: JSON.stringify({

		"statements" : [ {
		    "statement" : "CREATE (n) RETURN id(n)"
		} ]

	    }),
	    success: function(data, textStatus, jqXHR){
		toReturn = "success:" + textStatus;
	    },
	    error: function(jqXHR, textStatus, errorThrown){
		toReturn =  "error:" + textStatus;
	    }
	});//end of ajax


	return setTimeout(function(){return toReturn}, 5000);

    });
    casper.echo("result: " + result);
});

casper.run(function() {
});

