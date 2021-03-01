#Import our bot baseclass.
from OMB.bot import Bot

import json

#Used for Twitter.
from twython import Twython
from twython import TwythonError

class TwitterBot(Bot):

    #The **kwargs here allows us to define keyword args in the bot class init function.
    def __init__(self, twitter_credfile="creds/twitter_creds.json", **kwargs):
        
        #This dictionary contains the default values for our Twitter bot's attributes.
        defaults = {'dm_errors':True}

        #Update the attributes dictionary with the default values.
        #When we call the init of the base class, this will override the default values if specified in the kwargs.
        self.__dict__.update(defaults)

        #We call the init function of our base class, and pass it any arguments. 
        super().__init__(**kwargs)

        self.logger.info("Connecting to Twitter...")
        
        #Create an authenticated Twitter object.
        with open(twitter_credfile) as jsonfile:
            creds = json.load(jsonfile)

        self.twitter = Twython(creds['CONSUMER_KEY'], creds['CONSUMER_SECRET'],
                        creds['ACCESS_TOKEN'], creds['ACCESS_TOKEN_SECRET'])

    #The function posts a peice of media from Drive to Twitter.
    def post(self,media="random", status=None, updatedb=True):

        #Set this variable to "True" to update the database on each run.
        #This is the default behavior.
        if updatedb == True:
            self.updatedb()

        #If we just want to post a random piece of media, grab a random one.
        #This is the default behavior.
        if media == "random":
            media=self.GetRandom()

        try:
            #If the media is a video, special action must be taken.
            if ("video" in media.mimetype) == True:
                #I owe this next snipped of code to Sidney Chieng. Check it out here.                
                #https://sidneyochieng.co.ke/2019/05/uploading-videos-longer-that-30-seconds-to-twitter-using-twython/
                
                self.logger.info("Uploading video to Twitter...")

                #The kwargs here allow us to upload a large video to Twitter in chunks.
                response = self.twitter.upload_video(media.data, media_type=media.mimetype, check_progress=True, media_category='tweet_video')

                processing_info = response['processing_info']
                
                state = processing_info['state']
                
                wait = processing_info.get('check_after_secs', 1)
                
                #We need to check and see if the video is ready to be posted.
                if (state == 'pending' or state == 'in_progress'):

                    import time

                    #If the video isn't ready to be posted, wait the specified amount of time.
                    self.logger.info('Waiting ' + wait + 's to post.')
                    time.sleep(wait)

            #If it's not a video, it must be a photo, so we treat it as such.
            else:
                self.logger.info("Uploading photo to Twitter...")
                try:
                    #Upload the media to twitter for posting.
                    response=self.twitter.upload_media(media=media.data)

                #A TywthonError may indicate the image is too large to be posted.
                #Generally, we can combat this by reducing the image's color depth, which normally doesn't have an effect on image quality in my cases (anime images).
                except TwythonError:
                    from PIL import Image
                    from io import BytesIO
                    #By just running the image through PIL, it converts it to 8-bit color depth automatically.
                    with Image.open(media.data) as im:
                        with BytesIO() as image:
                            im.save(image, format=im.format)

                            #Make sure the image is being read from the beginning.
                            image.seek(0)

                            #Upload the media to twitter for posting.
                            response=self.twitter.upload_media(media=image)

            self.logger.info("Posting to Twitter...")
            
            #Post the tweet!
            tweet = self.twitter.update_status(status=status, media_ids=[response['media_id']])
            
            self.logger.info("POSTED: {} ({}), TWEETID: {}".format(media.name, media.id,tweet['id']))

            #Good practice to close media objects after we are done with them.
            media.data.close()

            #Now, we set the posted value to True, since we have posted the image.
            with self.connection:
                self.logger.info("Updating database...")
                self.cursor.execute("UPDATE media SET POSTED=TRUE WHERE ID=:ID",
                {"ID":media.id})
                self.logger.info("Database Updated!")
        
        #Error handling!
        except Exception as e:
            #If specified, DM errors to admin account(s)
            #This is the default behavior.
            if self.dm_errors:

                #When handling errors, we try to send the most detailed report to the admin(s) on Twitter.
                for admin in self.admin_ids:
                    #Try to send the most detailed report.
                    try:
                        message = "An error has occured:\n File: {}\n ID: {}\n Error: {}\n Twitter HTTP Response: {}".format(media.name, media.id, str(e), response)
                        self.twitter.send_direct_message(event= {"type": "message_create", "message_create": {"target": {"recipient_id": admin}, "message_data": {"text": message}}})                
                    
                    #An UnboundLocalError would indicate that "response" as not been set, so we exclude it from our message.
                    except UnboundLocalError:
                        message = "An error has occured:\n File: {}\n ID: {}\n Error: {}".format(media.name, media.id, str(e))
                        self.twitter.send_direct_message(event= {"type": "message_create", "message_create": {"target": {"recipient_id": admin}, "message_data": {"text": message}}})                
                    
                    #Any other errors, and we try to send the most basic message.
                    except:
                        
                        #Try to send basic message.
                        try:
                            self.twitter.send_direct_message(event= {"type": "message_create", "message_create": {"target": {"recipient_id": admin}, "message_data": {"text": str(e)}}})

                        #If we can't do that, log that we can't DM.
                        except:
                            self.logger.error("Unable to DM admin(s)!")
                
            #Log errors no matter what.
            self.logger.exception("An error has occured!")

            #Make sure we close the media object.    
            media.data.close()