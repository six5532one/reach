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
            obj.debug_output();
    }
    
    public void GetUserTimeline() throws TwitterException {
            
            /** ResponseList<Status> statuses = twitter.getHomeTimeline(new Paging((current_page++),current_page_content));
             * Could work since it uses authenticated user to access their data. 
             * Does not make a distinction between retweets and the user's original
             * content. Hence getUserTimeline is better and more flexible. 
             */
            
            int tweets_per_page = 50;
            int current_page = 1;
            ResponseList<Status> statuses = twitter.getUserTimeline("banunu_dog", new Paging(current_page++, tweets_per_page));
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
    
    public String fetchUsername(String status){
        if(status.contains("@")){
                //This selection filters out direct mentions as well as retweets
                String influencer_username = "";
                for(int x = (status.indexOf('@')+1); x < status.indexOf(' '); x++){
                    influencer_username += status.charAt(x);
                }
            }    
            else if(status.contains("RT") && (status.contains("@"))){
                    //This selection filters out retweets only
                }
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
            
            }
        
        
    }
    
    public void debug_output() {
        System.out.println("User's timeline collected is as follows:");
        for (int count_of_statuses = 0; count_of_statuses < user_original_timeline.size(); count_of_statuses++) {
            System.out.println("Debug: " + (count_of_statuses + 1) + ": " + user_original_timeline.get(count_of_statuses));
        }
    }
}
