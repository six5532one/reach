import org.apache.spark.streaming._
import org.apache.spark.streaming.twitter._

import org.apache.spark.streaming.StreamingContext._
import twitter4j.auth.Authorization
import twitter4j.Status
import twitter4j.auth.AuthorizationFactory
import twitter4j.conf.ConfigurationBuilder
import twitter4j.TwitterFactory
import org.apache.spark.streaming.api.java.JavaStreamingContext
import org.apache.spark.api.java.JavaSparkContext
import org.apache.spark.streaming.api.java.JavaDStream
import org.apache.spark.streaming.api.java.JavaReceiverInputDStream
import org.apache.hadoop.mapred.lib.MultipleTextOutputFormat
import org.apache.hadoop.io.NullWritable

import sqlContext._ 
import org.apache.spark.sql.Row;
import org.apache.spark.sql.types.{StructType,StructField,StringType,DoubleType,TimestampType};

val MountName = "trendinfluencers"
// Twitter credentials
val consumerKey = ""
val consumerSecret = ""
val accessToken = ""
val accessTokenSecret = ""

object auth{
  val config = new ConfigurationBuilder()
    .setOAuthConsumerKey(consumerKey)
    .setOAuthConsumerSecret(consumerSecret)
    .setOAuthAccessToken(accessToken)
    .setOAuthAccessTokenSecret(accessTokenSecret)
    .build
}
val twitter_auth = new TwitterFactory(auth.config)
val a = new twitter4j.auth.OAuthAuthorization(auth.config)
val atwitter : Option[twitter4j.auth.Authorization] =  Some(twitter_auth.getInstance(a).getAuthorization())

val ssc = new StreamingContext(sc, Seconds(60*15))
// Create a input stream that returns tweets received from Twitter.
// filter for tweets that are retweets and have at least one hashtag
val tweets = TwitterUtils.createStream(ssc, atwitter).filter(status => status.isRetweet()).map((status:Status) => {
  // get handle of user whom this status is retweeting
  val origStatus = status.getRetweetedStatus();
  val user_who_posted_orig = origStatus.getUser();
  // extract hashtags
  val text = status.getText
  var htags = List[String]()
  val allWords = status.getText.split(" ")

  for(i <- 0 until allWords.length) {
    if (allWords(i).startsWith("#")) {
      htags = allWords(i).drop(1) :: htags
    }
  }
  (htags, user_who_posted_orig.getScreenName())
}).filter(fields => (fields._1.length > 0))

val withSingleHashtags = tweets.map((fields:(List[String], String)) => {
  val hashtags = fields._1
  val origUserHandle = fields._2
  
  var results = List[(String,String)]()
  for(i <- 0 until hashtags.length) {
    results = (hashtags(i),origUserHandle) :: results
  }
  results
}).flatMap(records => {for (rec <- records) yield rec})

val numRetweetsPerHashtagPerUser = withSingleHashtags.map((fields:(String, String)) => {
  val hashtag = fields._1
  val origUserHandle = fields._2
  ((hashtag,origUserHandle), 1)
}).reduceByKey((x, y) => x + y).saveAsTextFiles(s"/mnt/$MountName/", s"reachTrendInfluencers")