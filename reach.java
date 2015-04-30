/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package reach;

import twitter4j.Status;
import twitter4j.TwitterException;
import twitter4j.conf.ConfigurationBuilder;
import twitter4j.*;
import java.util.*;

/**
 *
 * @author Piyali
 */
public class Reach {

    /**
     * @param args the command line arguments
     */
    static ArrayList<String> user_original_timeline = new ArrayList<String>();
    static ArrayList<String> humans_retweet_me = new ArrayList<String>();
    static ArrayList<String> humans_directlymention_me = new ArrayList<String>();
    static ConfigurationBuilder cb = new ConfigurationBuilder();
    static TwitterFactory twitter_factory;
    static Twitter twitter;
    static String current_user = "ambient_memory";

    public static void main(String[] args) throws TwitterException {
            cb.setDebugEnabled(true)
                    .setOAuthConsumerKey("0fAuoIn3FSkptsdzlLIrg4MDm")
                    .setOAuthConsumerSecret("F3CDyV0VGbeofhk87svXuLCZ0CJOryzuAa3Jgj1Z2P9iBPoTFq")
                    .setOAuthAccessToken("2875358986-Xjv7ks8AL1X0cu0TVXbjryjxw52bNMZacJIQddW")
                    .setOAuthAccessTokenSecret("hmHjTGWux0eYHIGb3YHX34C8f5eQZ81u0QDHkhVIPi9ua");
            twitter_factory = new TwitterFactory(cb.build());
            twitter = twitter_factory.getInstance();

            Reach obj = new Reach();
            obj.GetUserTimeline();
            for( String x: user_original_timeline){
                obj.fetchUsername(x);
            }
            //obj.GetInfluencers();
            obj.debug_output();
    }
    
    public void GetUserTimeline() throws TwitterException {
            
            /** ResponseList<Status> statuses = twitter.getHomeTimeline(new Paging((current_page++),current_page_content));
             * Could work since it uses authenticated user to access their data. 
             * Does not make a distinction between retweets and the user's original
             * content. Hence getUserTimeline is better and more flexible. 
             */
            
            int tweets_per_page = 5;
            int current_page = 1;
            ResponseList<Status> statuses = twitter.getUserTimeline(current_user, new Paging(current_page++, tweets_per_page));
            for (Status whatIsaid : statuses) { 
                user_original_timeline.add(whatIsaid.getText());
            }
            
            /**
             * TODO: Figure out how to bypass the rate limit because
             * we can't fetch all the tweets from the user. 
             */
            
            /**while(true){
                try{
                    int size = statuses.size();
                    for (Status whatIsaid : statuses) { 
                        user_original_content.add(whatIsaid.getText());
                    }
                    current_page++;
                    statuses = twitter.getUserTimeline("banunu_dog", new Paging(current_page, tweets_per_page));
                    if(statuses.size() == size) break;
                }catch(TwitterException e){
                    e.printStackTrace();
                }
            }**/
           
    }
    
    public void fetchUsername(String status){
        String influencer_username = "";
        if(status.contains("@")){
            System.out.println("Debug: Currently processing status: "+status);
                //This selection filters out direct mentions as well as retweets
                //Too tired to debug this right now tbh
                for(int x = status.indexOf('@'); x < status.indexOf(' '); x++){
                    influencer_username = influencer_username + status.charAt(x);
                    System.out.println("Debug: username construction is: "+influencer_username);
                }
            }    
         //return influencer_username;   
        System.out.println("Username found in status is:"+influencer_username);
    }
    
    public void GetInfluencers() throws TwitterException{
        /**
         * TODO: Figure out how this fits in with authentication 
         * applications. This has been demoed on ambient_memory and
         * not on banunu_dog. 
         */
        /**
         * This method processes the user's timeline to fetch who the user
         * retweets the most and who the suer directly mentions the most.  
         */
        for(String status: user_original_timeline){
            if(status.contains("RT")){
                //humans_retweet_me.add(fetchUsername(status));
            }
        }
        
        
    }
    
    public void debug_output() {
        System.out.println("User's timeline collected is as follows:");
        for (int count_of_statuses = 0; count_of_statuses < user_original_timeline.size(); count_of_statuses++) {
            System.out.println("Debug: " + (count_of_statuses + 1) + ": " + user_original_timeline.get(count_of_statuses));
        }
        System.out.println("@ambient_memory's favorite retweeters are as follows");
        for( int x = 0; x < humans_retweet_me.size(); x++){
            System.out.println("Debug: "+(x+1)+": "+humans_retweet_me.get(x));
        }
    }
}
