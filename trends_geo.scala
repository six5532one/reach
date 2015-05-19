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


import sqlContext._ 
import org.apache.spark.sql.Row;
import org.apache.spark.sql.types.{StructType,StructField,StringType,DoubleType,TimestampType};

val MountName = "learningscala"
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

val ssc = new StreamingContext(sc, Seconds(120))
// Create a input stream that returns tweets received from Twitter.
// filter for tweets that have at least one hashtag
val tweets = TwitterUtils.createStream(ssc, atwitter).filter(status => (status.getPlace() != null)).map((status:Status) => {
  val text = status.getText
  val lat = status.getPlace().getBoundingBoxCoordinates().apply(0).apply(0).getLatitude()
  val lng = status.getPlace().getBoundingBoxCoordinates().apply(0).apply(0).getLongitude()
  val date = status.getCreatedAt()
  var htags = List[String]()
  val allWords = status.getText.split(" ")
  
  for(i <- 0 until allWords.length) {
    if (allWords(i).startsWith("#")) {
      htags = allWords(i).drop(1) :: htags
    }
  }
  (htags, date, lat, lng)
}).filter(fields => (fields._1.length > 0))

// Create distributed map to associate each hashtag with the time it was first encountered
val rdd = sc.parallelize(Seq("ec2805")).map(x => (x.hashCode.toLong, new java.util.Date()))
// Construct an IndexedRDD from the pairs, hash-partitioning and indexing
// the entries.
var indexed = IndexedRDD(rdd).cache()

val withSingleHashtags = tweets.map((fields:(List[String], java.util.Date, Double, Double)) => {
  val hashtags = fields._1
  val ts = fields._2
  val lat = fields._3
  val lng = fields._4
  var results = List[(String,java.util.Date,Double,Double)]()
  for(i <- 0 until hashtags.length) {
    results = (hashtags(i),ts,lat,lng) :: results
  }
  results
}).flatMap(records => {for (rec <- records) yield rec})
val groupedByHashtag = withSingleHashtags.map((fields:(String, java.util.Date, Double, Double)) => {
  val hashtag = fields._1
  val ts = fields._2
  val lat = fields._3
  val lng = fields._4
  (hashtag, (ts, lat, lng))
}).groupByKey()
groupedByHashtag.saveAsTextFiles(s"/mnt/$MountName/", s"testTwStream")

ssc.start()