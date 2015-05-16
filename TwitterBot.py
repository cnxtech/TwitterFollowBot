# -*- coding: utf-8 -*-

"""
Copyright 2015 Randal S. Olson

This file is part of the Twitter Bot library.

The Twitter Bot library is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option)
any later version.

The Twitter Bot library is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
the Twitter Bot library. If not, see http://www.gnu.org/licenses/.
"""

from twitter import Twitter, OAuth, TwitterHTTPError
import os
import time

class TwitterBot:
    """
        Bot that automates several actions on Twitter, such as following users
        and favoriting tweets.
    """

    def __init__(self, config_file="config.txt"):
        # this variable contains the configuration for the bot
        self.BOT_CONFIG = {}
        
        # this variable contains the authorized connection to the Twitter API
        self.TWITTER_CONNECTION = None
        
        self.bot_setup(config_file)


    def bot_setup(self, config_file="config.txt"):
        """
            Reads in the bot configuration file and sets up the bot.

            Defaults to config.txt if no configuration file is specified.

            If you want to modify the bot configuration, edit your config.txt.
        """

        with open(config_file, "rb") as in_file:
            for line in in_file:
                line = line.split(":")
                parameter = line[0].strip()
                value = line[1].strip()
                self.BOT_CONFIG[parameter] = value
        
        # make sure that the config file specifies all requires parameters
        required_parameters = ["OAUTH_TOKEN", "OAUTH_SECRET", "CONSUMER_KEY",
                               "CONSUMER_SECRET", "TWITTER_HANDLE",
                               "ALREADY_FOLLOWED_FILE",
                               "FOLLOWERS_FILE", "FOLLOWS_FILE"]

        missing_parameters = False

        for required_parameter in required_parameters:
            if required_parameter not in self.BOT_CONFIG or self.BOT_CONFIG[required_parameter] == "":
                missing_parameters = True
                print("Missing config parameter: %s" % (required_parameter))
        
        if missing_parameters:
            print("\nPlease edit %s to include the parameters listed above and run bot_setup() again.\n" % (config_file))
            self.BOT_CONFIG = {}
            return
        
        # make sure all of the sync files exist locally
        for sync_file in [self.BOT_CONFIG["ALREADY_FOLLOWED_FILE"],
                          self.BOT_CONFIG["FOLLOWS_FILE"],
                          self.BOT_CONFIG["FOLLOWERS_FILE"]]:
            if not os.path.isfile(sync_file):
                with open(sync_file, "wb") as out_file:
                    out_file.write("")
                    
        # check how old the follower sync files are and recommend updating them if they are old
        if (time.time() - os.path.getmtime(self.BOT_CONFIG["FOLLOWS_FILE"]) > 86400 or
            time.time() - os.path.getmtime(self.BOT_CONFIG["FOLLOWERS_FILE"]) > 86400):
            print("Warning: Your Twitter follower sync files are more than a day old. "
                  "It is highly recommended that you sync them by calling sync_follows().")
                
        # create an authorized connection to the Twitter API
        self.TWITTER_CONNECTION = Twitter(auth=OAuth(self.BOT_CONFIG["OAUTH_TOKEN"],
                                                     self.BOT_CONFIG["OAUTH_SECRET"],
                                                     self.BOT_CONFIG["CONSUMER_KEY"],
                                                     self.BOT_CONFIG["CONSUMER_SECRET"]))


    def sync_follows(self):
        """
            Syncs the user's followers and follows locally so it isn't necessary
            to repeatedly look them up via the Twitter API.

            It is important to run this method at least daily so the bot is working
            with a relatively up-to-date version of the user's follows.
            
            Do not run this method too often, however, or it will quickly cause your
            bot to get rate limited by the Twitter API.
        """
    
        # make sure the bot has been set up first
        if self.BOT_CONFIG == {}:
            print("The bot has not been set up yet. Please run bot_setup() first.")
            return

        # sync the user's followers (accounts following the user)
        followers_status = self.TWITTER_CONNECTION.followers.ids(screen_name=self.BOT_CONFIG["TWITTER_HANDLE"])
        followers = set(followers_status["ids"])
        next_cursor = followers_status["next_cursor"]

        with open(self.BOT_CONFIG["FOLLOWERS_FILE"], "wb") as out_file:
            for follower in followers:
                out_file.write("%s\n" % (follower))

        while next_cursor != 0:
            followers_status = self.TWITTER_CONNECTION.followers.ids(screen_name=self.BOT_CONFIG["TWITTER_HANDLE"], cursor=next_cursor)
            followers = set(followers_status["ids"])
            next_cursor = followers_status["next_cursor"]

            with open(self.BOT_CONFIG["FOLLOWERS_FILE"], "ab") as out_file:
                for follower in followers:
                    out_file.write("%s\n" % (follower))

        # sync the user's follows (accounts the user is following)
        following_status = self.TWITTER_CONNECTION.friends.ids(screen_name=self.BOT_CONFIG["TWITTER_HANDLE"])
        following = set(following_status["ids"])
        next_cursor = following_status["next_cursor"]

        with open(self.BOT_CONFIG["FOLLOWS_FILE"], "wb") as out_file:
            for follow in following:
                out_file.write("%s\n" % (follow))

        while next_cursor != 0:
            following_status = self.TWITTER_CONNECTION.friends.ids(screen_name=self.BOT_CONFIG["TWITTER_HANDLE"], cursor=next_cursor)
            following = set(following_status["ids"])
            next_cursor = following_status["next_cursor"]

            with open(self.BOT_CONFIG["FOLLOWS_FILE"], "ab") as out_file:
                for follow in following:
                    out_file.write("%s\n" % (follow))


    def get_do_not_follow_list(self):
        """
            Returns the set of users the bot has already followed in the past.
        """
        
        # make sure the bot has been set up first
        if self.BOT_CONFIG == {}:
            print("The bot has not been set up yet. Please run bot_setup() first.")
            return

        dnf_list = []
        with open(self.BOT_CONFIG["ALREADY_FOLLOWED_FILE"], "rb") as in_file:
            for line in in_file:
                dnf_list.append(int(line))

        return set(dnf_list)


    def get_followers_list(self):
        """
            Returns the set of users that are currently following the user.
        """
        
        # make sure the bot has been set up first
        if self.BOT_CONFIG == {}:
            print("The bot has not been set up yet. Please run bot_setup() first.")
            return

        followers_list = []
        with open(self.BOT_CONFIG["FOLLOWERS_FILE"], "rb") as in_file:
            for line in in_file:
                followers_list.append(int(line))

        return set(followers_list)


    def get_follows_list(self):
        """
            Returns the set of users that the user is currently following.
        """
        
        # make sure the bot has been set up first
        if self.BOT_CONFIG == {}:
            print("The bot has not been set up yet. Please run bot_setup() first.")
            return

        follows_list = []
        with open(self.BOT_CONFIG["FOLLOWS_FILE"], "rb") as in_file:
            for line in in_file:
                follows_list.append(int(line))

        return set(follows_list)


    def search_tweets(self, q, count=100, result_type="recent"):
        """
            Returns a list of tweets matching a phrase (hashtag, word, etc.).
        """
        
        # make sure the bot has been set up first
        if self.BOT_CONFIG == {}:
            print("The bot has not been set up yet. Please run bot_setup() first.")
            return

        return self.TWITTER_CONNECTION.search.tweets(q=q, result_type=result_type, count=count)


    def auto_fav(self, q, count=100, result_type="recent"):
        """
            Favorites tweets that match a phrase (hashtag, word, etc.).
        """
        
        # make sure the bot has been set up first
        if self.BOT_CONFIG == {}:
            print("The bot has not been set up yet. Please run bot_setup() first.")
            return

        result = self.search_tweets(q, count, result_type)

        for tweet in result["statuses"]:
            try:
                # don't favorite your own tweets
                if tweet["user"]["screen_name"] == self.BOT_CONFIG["TWITTER_HANDLE"]:
                    continue

                result = self.TWITTER_CONNECTION.favorites.create(_id=tweet["id"])
                print("favorited: %s" % (result["text"].encode("utf-8")))

            # when you have already favorited a tweet, this error is thrown
            except TwitterHTTPError as e:
                if "you have already favorited this status" not in str(e).lower():
                    print("error: %s" % (str(e)))


    def auto_rt(self, q, count=100, result_type="recent"):
        """
            Retweets tweets that match a phrase (hashtag, word, etc.).
        """
        
        # make sure the bot has been set up first
        if self.BOT_CONFIG == {}:
            print("The bot has not been set up yet. Please run bot_setup() first.")
            return

        result = self.search_tweets(q, count, result_type)

        for tweet in result["statuses"]:
            try:
                # don't retweet your own tweets
                if tweet["user"]["screen_name"] == self.BOT_CONFIG["TWITTER_HANDLE"]:
                    continue

                result = self.TWITTER_CONNECTION.statuses.retweet(id=tweet["id"])
                print("retweeted: %s" % (result["text"].encode("utf-8")))

            # when you have already retweeted a tweet, this error is thrown
            except TwitterHTTPError as e:
                print("error: %s" % (str(e)))


    def auto_follow(self, q, count=100, result_type="recent"):
        """
            Follows anyone who tweets about a phrase (hashtag, word, etc.).
        """
        
        # make sure the bot has been set up first
        if self.BOT_CONFIG == {}:
            print("The bot has not been set up yet. Please run bot_setup() first.")
            return

        result = self.search_tweets(q, count, result_type)
        following = self.get_follows_list()
        do_not_follow = self.get_do_not_follow_list()

        for tweet in result["statuses"]:
            try:
                if (tweet["user"]["screen_name"] != self.BOT_CONFIG["TWITTER_HANDLE"] and
                        tweet["user"]["id"] not in following and
                        tweet["user"]["id"] not in do_not_follow):

                    self.TWITTER_CONNECTION.friendships.create(user_id=tweet["user"]["id"], follow=False)
                    following.update(set([tweet["user"]["id"]]))

                    print("followed %s" % (tweet["user"]["screen_name"]))

            except TwitterHTTPError as e:
                print("error: %s" % (str(e)))

                # quit on error unless it's because someone blocked me
                if "blocked" not in str(e).lower():
                    quit()


    def auto_follow_followers(self):
        """
            Follows back everyone who's followed you.
        """
        
        # make sure the bot has been set up first
        if self.BOT_CONFIG == {}:
            print("The bot has not been set up yet. Please run bot_setup() first.")
            return

        following = self.get_follows_list()
        followers = self.get_followers_list()

        not_following_back = followers - following

        for user_id in not_following_back:
            try:
                self.TWITTER_CONNECTION.friendships.create(user_id=user_id, follow=False)
            except Exception as e:
                print("error: %s" % (str(e)))


    def auto_follow_followers_of_user(self, user_screen_name, count=100):
        """
            Follows the followers of a specified user.
        """
        
        # make sure the bot has been set up first
        if self.BOT_CONFIG == {}:
            print("The bot has not been set up yet. Please run bot_setup() first.")
            return
        
        following = self.get_follows_list()
        followers_of_user = set(self.TWITTER_CONNECTION.followers.ids(screen_name=user_screen_name)["ids"][:count])
        do_not_follow = self.get_do_not_follow_list()

        for user_id in followers_of_user:
            try:
                if (user_id not in following and
                    user_id not in do_not_follow):

                    self.TWITTER_CONNECTION.friendships.create(user_id=user_id, follow=False)
                    print("followed %s" % user_id)

            except TwitterHTTPError as e:
                print("error: %s" % (str(e)))


    def auto_unfollow_nonfollowers(self):
        """
            Unfollows everyone who hasn't followed you back.
        """
        
        # make sure the bot has been set up first
        if self.BOT_CONFIG == {}:
            print("The bot has not been set up yet. Please run bot_setup() first.")
            return

        following = self.get_follows_list()
        followers = self.get_followers_list()

        # put user IDs here that you want to keep following even if they don't
        # follow you back
        # you can look up Twitter account IDs here: http://gettwitterid.com
        users_keep_following = set([])

        not_following_back = following - followers

        # update the "already followed" file with users who didn't follow back
        already_followed = set(not_following_back)
        already_followed_list = []
        with open(self.BOT_CONFIG["ALREADY_FOLLOWED_FILE"]) as in_file:
            for line in in_file:
                already_followed_list.append(int(line))

        already_followed.update(set(already_followed_list))

        with open(self.BOT_CONFIG["ALREADY_FOLLOWED_FILE"], "wb") as out_file:
            for val in already_followed:
                out_file.write(str(val) + "\n")

        for user_id in not_following_back:
            if user_id not in users_keep_following:
                self.TWITTER_CONNECTION.friendships.destroy(user_id=user_id)
                print("unfollowed %d" % (user_id))


    def auto_mute_following(self):
        """
            Mutes everyone that you are following.
        """
        
        # make sure the bot has been set up first
        if self.BOT_CONFIG == {}:
            print("The bot has not been set up yet. Please run bot_setup() first.")
            return
        
        following = self.get_follows_list()
        muted = set(self.TWITTER_CONNECTION.mutes.users.ids(screen_name=self.BOT_CONFIG["TWITTER_HANDLE"])["ids"])

        not_muted = following - muted

        # put user IDs of people you do not want to mute here
        # you can look up Twitter account IDs here: http://gettwitterid.com
        users_keep_unmuted = set([])

        for user_id in not_muted:
            if user_id not in users_keep_unmuted:
                self.TWITTER_CONNECTION.mutes.users.create(user_id=user_id)
                print("muted %d" % (user_id))


    def auto_unmute(self):
        """
            Unmutes everyone that you have muted.
        """
        
        # make sure the bot has been set up first
        if self.BOT_CONFIG == {}:
            print("The bot has not been set up yet. Please run bot_setup() first.")
            return
        
        muted = set(self.TWITTER_CONNECTION.mutes.users.ids(screen_name=self.BOT_CONFIG["TWITTER_HANDLE"])["ids"])

        # put user IDs of people you want to remain muted here
        # you can look up Twitter account IDs here: http://gettwitterid.com
        users_keep_muted = set([])

        for user_id in muted:
            if user_id not in users_keep_muted:
                self.TWITTER_CONNECTION.mutes.users.destroy(user_id=user_id)
                print("unmuted %d" % (user_id))