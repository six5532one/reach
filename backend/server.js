"use strict";
console.log("\nHello reach version ... ");
process.title = 'reach_backend'; // this name appears in 'ps' command
//Declarations for the http servers
var http_req = require('request');
// Port where we'll run the server
var http_port = 2678;
var http = require('http'), fs = require('fs'), qs = require('querystring'), url = require('url');
//Declarations for the AWS
var AWS = require('aws-sdk');
AWS.config.apiVersions = {
	ec2: 'latest',
	sqs: 'latest',
	sns: 'latest'
};
//Declarations for the Tweeter part
var twitter = require('twit');
var twit_client = new twitter({'consumer_key': process.env.TWITTER_CONSUMER_KEY, //KEY
	'consumer_secret': process.env.TWITTER_CONSUMER_SECRET,
	'access_token': process.env.TWITTER_ACCESS_TOKEN_KEY,
	'access_token_secret': process.env.TWITTER_ACCESS_TOKEN_SECRET});
var resp_str = "";
var tweets = [];
var user_name;
var resp_ready = false;
var data_rcvd_count = 0;
//HTTP server
var http_server = http.createServer(function (request, response) {
	//console.log("Debug : HTTP server called asking URL " + request.url + " by method : " + request.method + " at : " + (new Date()));
	if (request.method === "GET") {
		var u_r_l = url.parse(request.url, true);	//This true breaks the query string into JSON object
		console.log("Debug : u_r_l.query is : ", u_r_l.query);
		if (u_r_l.pathname === '/data') {	//This is a request from the frontend to set up the tweet feed
			var user_name_val = u_r_l.query.uname;
			var stat_val = u_r_l.query.stat;
			if (stat_val === "0") {
				user_name = user_name_val;		//Set the username for further processing
				if (user_name.charAt(0) === '@')
					user_name = user_name.substring(1); //knock off the starting at symbol if sent
				//console.log("GET request is with name " + user_name);
				twit_client.get('statuses/user_timeline', {
					'include_rts': true,
					'contributor_details': true,
					'exclude_replies': false,
					'count': 200,
					'screen_name': user_name
				}, twit_resp);
				response.writeHead(200, {'Content-Type': 'text/plain'});
				response.end("OK");
				return;
			} else if (stat_val === "1") {	//we have been asked to get the statistics of the username uname
				//We do two checks, one we reconfirm that the username is indeed the same, and second we check if the data is ready
				if (user_name_val !== user_name) {
					//The user name provided has got changed.. to respect Data provacy act, we return an invalid user
					response.writeHead(400, {'Content-Type': 'text/plain'});
					response.end('Invalid User Name provided...');
					console.log("received invalid user name ");
					return;
				}
				if (resp_ready === false) {
					//The request for stat has come too soon we respond as server not ready
					response.writeHead(502, {'Content-Type': 'text/plain'});
					response.end('Need more time to finish data processing for this user...');
					console.log("received stat request too early... ");
					return;
				}
				//Since at this stage resp_ready is set, we return the resp_str
				response.writeHead(200, {'Content-Type': 'text/plain'});
				response.end(resp_str);
				//We now clear the fields of the previous user...
				resp_ready = false;
				resp_str = "";
				tweets = [];
				data_rcvd_count = 0;
				return;
			} else if (stat_val === "-1") {
				//This is an abort request, so we re initialize all arrays and wait for next request
				resp_ready = false;
				resp_str = "";
				tweets = [];
				data_rcvd_count = 0;
				response.writeHead(200, {'Content-Type': 'text/plain'});
				response.end("Stats compilation aborted...");
			}
		} //end of data
	} //end of GET
	else {
		response.writeHead(404, {'Content-Type': 'text/plain'});
		response.end('Sorry, unknown message type');
		console.log("received unknown or no message type ");
	} //unknown type (like POST)
}); //end of http server
http_server.listen(http_port, function () {
	console.log("Server is listening on port " + http_port + " at : " + (new Date()));
});

//The call back functions for the twitter stream
var twit_resp = function (err, data, resp) {
	if (err)
		console.log("Debug tweet error : ", err);
	if (data) {
		for (var i = 0; i < data.length; i++) {
			tweets.push(data[i]);
		}
		data_rcvd_count++;		//Increment the number of chunks received
		//If we still need more chunks, we call this function again
		if (data_rcvd_count < 3) {
			var min_id = Number.MAX_VALUE;
			for (var i = 0; i < data.length; i++) {
				if (data[i].id < min_id)
					min_id = data[i].id;
			}
			min_id--;
			twit_client.get('statuses/user_timeline', {
				'max_id': min_id,
				'include_rts': true,
				'contributor_details': true,
				'exclude_replies': false,
				'count': 200,
				'screen_name': user_name
			}, twit_resp);
			return;
		} else {
			//Analytics...
			resp_str =  "The total count of tweets received is : "+tweets.length+"\n"+"The first element is :"+"\n"+JSON.stringify(tweets[0],null,4);
			resp_ready =  true;
		};
		console.log("Debug tweet data pushed : " + tweets.length + " and chunk count : " + data_rcvd_count);
	}
	if (resp)
		console.log("Debug resp also rcvd ");
	return;
};