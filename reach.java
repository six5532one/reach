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
    static ArrayList<String> user_original_content = new ArrayList<String>();

    public static void main(String[] args) throws TwitterException {
        // TODO code application logic here
        Reach obj = new Reach();
        obj.GetHomeTimeline();
        obj.debug_output();
    }
    
    public void GetHomeTimeline() throws TwitterException {
        try {
            ConfigurationBuilder cb = new ConfigurationBuilder();
            cb.setDebugEnabled(true)
                    .setOAuthConsumerKey("***")
                    .setOAuthConsumerSecret("***")
                    .setOAuthAccessToken("***")
                    .setOAuthAccessTokenSecret("***");

            TwitterFactory twitter_factory = new TwitterFactory(cb.build());
            Twitter twitter = twitter_factory.getInstance();
            //User me = twitter.verifyCredentials();
            //ResponseList<Status> statuses = twitter.getHomeTimeline(new Paging((current_page++),current_page_content));
            /**
             * This method is better than getHomeTimeline() because it provides
             * only original tweets
             */
            
            int tweets_per_page = 50;
            int current_page = 1;
            ResponseList<Status> statuses = twitter.getUserTimeline("banunu_dog", new Paging(current_page++, tweets_per_page));
            for (Status whatIsaid : statuses) { 
                user_original_content.add(whatIsaid.getText());
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
            
        } catch (TwitterException e) {
            e.printStackTrace();
            System.err.println("Sorry but failed to get timeline! :(" + e.getErrorMessage());
            System.exit(-1);
        }

    }

    public void debug_output() {
        System.out.println("User's timeline collected is as follows:");
        for (int count_of_statuses = 0; count_of_statuses < user_original_content.size(); count_of_statuses++) {
            System.out.println("Debug: " + (count_of_statuses + 1) + ": " + user_original_content.get(count_of_statuses));
        }
    }
}
