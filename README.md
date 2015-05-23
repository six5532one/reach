# REACH

REACH is a comprehensive analytics suite currently serving Twitter users.

Features
---------
* User analytics
* Visualization of how trends on Twitter propagate geographically in real time
* Identification of Twitter users who are influencers for any given trend

Architecture
-------------
Our web application uses the Python Flask framework to process user requests for each of the available analytics. In order to provide analytics about a particular Twitter user, the web application requests the data from a Node.js service that computes these metrics.

To allow our web application to serve geographic and temporal patterns of all trending topics on Twitter and provide information about the Twitter users who are most influential for each topic, we run two Spark Streaming jobs that continuously process data from the Twitter Stream, leveraging Databricks Cloud to launch Spark clusters via Amazon Web Services.

####User Analytics Component
This [Node.js server](https://github.com/six5532one/reach/tree/master/backend) communicates with the application server to processes requests for user analytics data. 

##### Implementation: 
First, the user/front-end sends a request with a username and a status number = 0. The node server then fetches data from the Twitter API using that username and behind processing for 6 metrics. During the processing time, if the user sends a request of the same username with status=1, then the server will respond with "Not enough time to process data". During this time if the user resends another username with status=0, the analytics processing for the previous username is aborted. This part of the code currently processes 600 tweets. 

#####API:
Five user analytics metrics are returned in JSON format:

* the requested user's spread/virality factor
* all of the user's hashtags and their frequencies
* Twitter users that this user directly mentions most in their tweets
* Twitter users that this user replies to most in their tweets
* the most popular locations from where this user has tweeted

####Data Processing Pipeline
TODO

