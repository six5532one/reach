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
var user_name;		//This will be kept as a null string while we are waiting for the first request, but will maintain the value till next request
var resp_ready = false;
var data_rcvd_count = 0;
var debug_str = "";
var resp_object = {
	'an1': null,
	'an2': null,
	'an3': null,
	'an4': null,
	'an5': null
};

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
				console.log("GET request is with name " + user_name + " and stat value : " + stat_val);
				twit_client.get('statuses/user_timeline', {
					'include_rts': true,
					'contributor_details': true,
					'exclude_replies': false,
					'count': 200,
					'screen_name': user_name
				}, twit_resp);
				response.writeHead(200, {'Content-Type': 'text/plain'});
				response.end("Registered user name : " + user_name + " : OK");
				return;
			} else if (stat_val === "1") {	//we have been asked to get the statistics of the username uname
				//We do two checks, one we reconfirm that the username is indeed the same, and second we check if the data is ready
				if (user_name_val !== user_name) {
					//The user name provided has got changed.. to respect Data Privacy act, we return an invalid user					
					response.writeHead(400, {'Content-Type': 'text/plain'});
					response.end('Invalid User Name provided...orig : ' + user_name + ' and now sent : ' + user_name_val);
					console.log("Debug : received invalid user name orig : " + user_name + " and now sent : " + user_name_val);
					return;
				}
				if (resp_ready === false) {
					//The request for stat has come too soon we respond as server not ready
					response.writeHead(502, {'Content-Type': 'text/plain'});
					response.end('Need more time to finish data processing for this user...');
					console.log("Debug : Received stat request too early... ");
					return;
				}
				//Since at this stage resp_ready is set, we return the resp_str
				response.writeHead(200, {'Content-Type': 'application/json'});
				response.end(resp_object);
				//We now clear the fields of the previous user...
				resp_ready = false;
				resp_str = "";
				tweets = [];
				data_rcvd_count = 0;
				user_name = "";
				resp_object.an1 = null;
				resp_object.an2 = null;
				resp_object.an3 = null;
				resp_object.an4 = null;
				resp_object.an5 = null;
				return;
			} else if (stat_val === "-1") {
				//This is an abort request, so we re initialize all arrays and wait for next request
				resp_ready = false;
				resp_str = "";
				tweets = [];
				data_rcvd_count = 0;
				user_name = "";
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
			//Analytics... as we have received all three sets .. the var data_rcvd is reset by the http[ handler when it sends the response back
			var num_retweets = 0;		//Used by the Analytics 1 : Average number of retweets
			var array_of_tags = [];
			var array_of_locations = [];
			var people_user_replies_to = [];
			var people_user_mentions = [];

			var is_found = false;
			var location_exists = false;
			var responsee_exists = false;

			//if (tweets.length > 3) tweets.splice(3);	//knock off all but 0,1 and 2

			for (var i = 0; i < tweets.length; i++) {
				//Metric number 1: Average number of retweets

				//We process the numerator for average number of retweeters in the loop
				num_retweets += tweets[i].retweet_count;

				//Metric number 2: Track hashtags
				if (tweets[i].entities.hashtags.length !== 0) {
					//We first check if it already exists in the array of tags					
					for (var m = 0; m < tweets[i].entities.hashtags.length; m++) {	//for each hashtag in the entities list
						is_found = false;
						for (var k = 0; k < array_of_tags.length; k++) {			//against each hashtag in the array_of_hashtags array
							if (array_of_tags[k].hashtag === tweets[i].entities.hashtags[m].text) {
								array_of_tags[k].count += 1;
								is_found = true;
								break;
							}
						} //end of for every existing tag
						if (is_found === false) {
							//Not found we add
							var new_obj = {'hashtag': tweets[i].entities.hashtags[m].text, 'count': 1};
							array_of_tags.push(new_obj);
						}
					} //(m) end of for every hashtag in the entry
				} //end of if a hash tag is in the entities list

				//Metric number 3: Who do you mention the most?
				if (tweets[i].entities.user_mentions.length !== 0) {
					for (var m = 0; m < tweets[i].entities.user_mentions.length; m++) {
						responsee_exists = false;
						for (var k = 0; k < people_user_mentions.length; k++) {
							if (people_user_mentions[k].person === tweets[i].entities.user_mentions[m].screen_name) {
								people_user_mentions[k].count += 1;
								responsee_exists = true;
								break;
							}
						}	//end of for
						if (responsee_exists === false) {
							//Never seen this before, so we add them to array of locations
							var new_person = {'person': tweets[i].entities.user_mentions[m].screen_name, 'count': 1};
							people_user_mentions.push(new_person);
						}
					}
				}

				//Metric number 4: Who do you reply to the most?
				if (tweets[i].in_reply_to_screen_name !== null) {
					responsee_exists = false;
					for (var k = 0; k < people_user_replies_to.length; k++) {
						if (people_user_replies_to[k].screen_name === tweets[i].in_reply_to_screen_name.trim()) {
							people_user_replies_to[k].count += 1;
							responsee_exists = true;
							break;
						}
					}//end of for
					if (responsee_exists === false) {
						//Never seen this before, so we add them to array of reply persons
						var new_person = {'screen_name': tweets[i].in_reply_to_screen_name.trim(), 'count': 1};
						people_user_replies_to.push(new_person);
					}
				}

				//Metric number 5: Where do you tweet from the most?

				if (tweets[i].place !== null) {
					location_exists = false;
					for (var k = 0; k < array_of_locations.length; k++) {
						if (array_of_locations[k].location === tweets[i].place.full_name) {
							array_of_locations[k].count += 1;
							location_exists = true;
							break;
						}
					}//end of for
					if (location_exists === false) {
						//Never seen this before, so we add them to array of locations
						var new_location = {'location': tweets[i].place.full_name, 'count': 1};
						array_of_locations.push(new_location);
					}
				}


				/*Metric number 6: Who do you retweet the most?
				 if ((tweets[i].text.indexOf("RT") > -1) && (tweets[i].text.indexOf("@") > -1)) {
				 
				 }
				 */

			}//end of large tweet cycle processing
			//Now we do the final analysis of the data extracted
			var avg_retweets = num_retweets / tweets.length;

			resp_object.an1 = avg_retweets;
			resp_object.an2 = array_of_tags;
			resp_object.an3 = people_user_mentions;
			resp_object.an4 = people_user_replies_to;
			resp_object.an5 = array_of_locations;
			//resp_str = "First object :\n"+JSON.stringify(tweets[0],null,4)+"\nSecond object :\n"+JSON.stringify(tweets[1],null,4)+"\n";//Third object :\n"+JSON.stringify(tweets[2],null,4)+"\n";
			//resp_str = "Debug str :\n"+
			resp_str = JSON.stringify(resp_object);//+"\n"+debug_str;
			resp_ready = true;

		}
		; //end of else
		console.log("Debug tweet data pushed : " + tweets.length + " and chunk count : " + data_rcvd_count);
	}
	;
	if (resp)
		console.log("Debug resp also rcvd ");
	return;
}; //end of twit_resp call back funtion