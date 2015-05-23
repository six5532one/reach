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
A [Node.js server](https://github.com/six5532one/reach/tree/master/backend) deployed via Amazon Elastic Beanstalk communicates with the application server to processes requests for user analytics data. 

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
#####Twitter Streaming API => Apache Spark Streaming
We run two Spark Streaming jobs to continuously process all Twitter Statuses from the Twitter Streaming API. Each runs on a Spark cluster consisting of 8 Amazon EC2 instances with 218GB of memory.

[One Spark Streaming job](https://github.com/six5532one/reach/blob/master/trends_geo.scala) tracks the geo coordinates for each Twitter hashtag, each time the hashtag is used. It filters the streaming data source for Twitter Statuses that include geo coordinates and at least one hashtag, then groups timestamps and geo coordinates for each hashtag. By design, Spark Streaming bins data from a streaming source into batches, such that the data streamed in each time interval is used to create a Resilient Distributed Dataset (RDD). Hence, the computations specified in this job are repeated on an RDD constructed in every time interval and results written to Amazon S3 are named with a timestamp denoting the time interval at which that RDD was constructed.

#####Apache Spark Streaming => Application Server
We add a notification for "PUT" events in the S3 bucket containing these objects, adding events to an SQS queue. Our application server runs a thread pool that delegates one worker to read SQS messages for this notification type, to access the newest Spark Streaming output for this particular job.

A [second Spark Streaming job](https://github.com/six5532one/reach/blob/master/trend_influencers.scala) tracks the number of users who retweet each hashtag mentioned by a particular Twitter user. It filters the streaming data source for Statuses that are retweets and contain at least one hashtag, gets the Twitter user who posted the Status that was retweeted, and attributes a tally for the grouping of that hashtag and Twitter user. These tallies are aggregated into counts and the counts for each batch are written to another S3 bucket that also  triggers SQS notifications for "PUT" events. The application server delegates a separate thread for handling notifications for new output for this Spark job.

#####Application Server => User Interface
The background threads that process SQS notifications fetch the newest Spark output from S3, parse the S3 contents, and write them to Dynamo DB. When a user requests either the [hashtag geography trends](https://github.com/six5532one/reach/blob/master/app.py#L99) or [hashtag influencers](https://github.com/six5532one/reach/blob/master/app.py#L129) endpoints, the application server queries the DynamoDB instance, aggregates the result set in a meaningful way, and sends the result to the front end.

####Data Visualization
User analytics for visualized using the Highcharts JS charting framework. We use the Google Maps API to display geographic and temporal trends in hashtag usage. We also use the Python Flask-SocketIO library to implement the websockets protocol, enabling visualization of real-time updates of the hashtag geography trends.