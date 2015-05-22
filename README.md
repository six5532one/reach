# reach

####More Amazing stuff to come here

#### [User Analytics Side] (reach-backend.elasticbeanstalk.com)
The second component of this app is when the user enters a twitter user handle to the textbox. The back-of-back end part of this code is a Node.js server which receives the data from the front end with a GET() request. 

##### How it works: 
First, the user/front-end sends a request with a username and a status number = 0. The node server then goes on to fetch data from the Twitter API using that username and behind processing for 6 metrics. During the processing time, if the user sends a request of the same username with status=1, then the server will respond with "Not enough time to process data". During this time if the user resends another username with status=0, the analytics processing for the previous username is aborted. This part of the code currently processes 600 tweets. 

There are five metrics which have been implemented in terms of user analytics. They are: a float value of the requested user's spread/virality factor, all of the user's hashtags and their frequencies (in order to construct an overall pie-chart of how the data looks like), the top five people that the user directly mentions most in their tweets, the top five people that the user replies to most in their tweets  and the top five most popular locations from where a user has tweeted. This list is not comprehensive and obviously, future versions may have even smarter versions of them. These metrics are calculated mostly by looping through all 600 tweets and adding only unknown members to a globally maintained list of properties we want to track. 

#####What is returned to the front end: A JSON object containing the required fields in a format previously determined by the front-end writer (Jessica Fan + Emily Chen) and me. 
