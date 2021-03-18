import sqlite3

import logging

import re

#This class is used to store data associated with a piece of media.
class Media:
    def __init__(self, data, mimetype, name, id):
        #Data must be a file-like object.
        self.data = data
        self.mimetype = mimetype
        self.name = name
        self.id = id

#This is a base class that any bot will inherit from. Contains functions for downloading from drive, and interacting with that database.
class Bot:

    #Within this init function, we connect to various APIs and set user defined variables for the methods.
    def __init__(self, configfile = None,  **kwargs):

        #These are the default values for our Bot.
        defaults = {"name":"OpenMediaBot","db":"media.db"}
        
        #Update the attributes defaults dictionary with any kwargs provided by the user.
        #Since a dictionary does not allow duplicate keys, kwargs provided by the user that were previously set in the default dict will override thier default values.
        defaults.update(kwargs)

        self.__dict__.update(defaults)

        #If a configfile is provided, we will use the values in this file to override any default values or kwargs provided in the attributes dict.
        if configfile is not None:
            
            with open(configfile) as jsonfile:
                
                import json
                
                self.__dict__.update(json.load(jsonfile))

        #We use the bot name as the name for our SQL table, this allows us to house multiple bots in the same databse file.
        #We have to  make sure we sanitize th name of the bot in order to prevent SQL inquection attacks.
        if re.search("[\";\+=()\']", self.name) is not None:
            raise ValueError("The characters [\";\+=()\'] are not allowed in bot names, as they leave you vulnerable to SQL injection attacks.")
        #Set up the bot's logger

        #Create a logger with the bot's name, and set the level to INFO.
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)

        #Format our logs.
        formatter = logging.Formatter("%(name)s:%(asctime)s:%(levelname)s:%(message)s")

        #Create a stream handler which logs to the console.
        stream_handler = logging.StreamHandler()

        stream_handler.setFormatter(formatter)

        self.logger.addHandler(stream_handler)

        #If a path is supplied, create the specified filehandler to print to the log file.
        if self.__dict__.get("logpath") is not None:

            file_handler = logging.FileHandler(filename=self.logpath)

            file_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)

        #If Google Drive folders are provided, create an autheticated PyDrive object.
        if self.__dict__.get("drive_folders") is not None:

            self.logger.info("Connecting to Google Drive...")
            
            #Used for Google Drive.
            from pydrive2.auth import GoogleAuth
            from pydrive2.drive import GoogleDrive

            self.drive = GoogleDrive(GoogleAuth())

        #Connect to our SQLite DB.
        self.connection = sqlite3.connect(self.db)

        #Create a cursor to execute commands within the database.
        self.cursor = self.connection.cursor()

    #This function updates and/or initializes our database.
    def updatedb(self):

        self.logger.info("Updating database...")

        #Create our database table if it doesn't exist.
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS '{}' (
        ID text PRIMARY KEY,
        NAME text NOT NULL,
        LOCATION text NOT NULL,
        POSTED BOOLEAN NOT NULL);""".format(self.name))
       
        #Query a list of IDs from the database.
        self.cursor.execute("SELECT ID FROM '{}'".format(self.name))

        #Get the result of the query.
        db = [row[0] for row in self.cursor.fetchall()]

        #Iterate through all the files in the Google Drive folder.

        with self.connection:

            #If we provide Google Drive folders, scan for changes.
            if self.__dict__.get("drive_folders") is not None:

                for folder_id in self.drive_folders:

                    self.logger.info("Updating Drive folder {}...".format(folder_id))

                    #Get a list of files in the folder.
                    drive_files = self.drive.ListFile({'q': "'{}' in parents and trashed=false".format(folder_id)}).GetList()

                    for file in drive_files:

                        #If the file EXISTS in our database.
                        if (file['id'] in db):
                        
                            #Make sure that the correct filename is reflected in our database.
                            
                            self.cursor.execute("SELECT NAME FROM '{}' WHERE ID=:ID".format(self.name),
                            {"ID":file['id']})

                            #The above query should only return one result, so we canuse fetchone.
                            name = self.cursor.fetchone()[0]

                            #If the name has been changed, update our database.
                            if file['title'] != name:
                                self.cursor.execute("UPDATE '{}' SET NAME=:NAME WHERE ID=:ID".format(self.name),
                                {"NAME":file['title'],"ID":file['id']})
                                self.logger.info("RENAMED: {} TO {}".format(name, file['title']))
                    
                            #If the file exists in our database, remove it from the queried list.
                            #By doing this, we will list of files that are in our database but not in the Google Drive folder.
                            db.remove(file['id'])
                        
                        #If the file DOES NOT exist in our database, update the database with information for the new file.
                        else:

                            self.cursor.execute("INSERT INTO '{}' VALUES (:ID, :NAME, 'DRIVE', 'POSTED'=False)".format(self.name),
                            {"ID":file['id'], "NAME":file['title']})

                            #Output some useful information for logging purposes.
                            self.logger.info("ADDED: {} ({})".format(file['title'], file['id']))
                            
            #If we provide local folders, scan them for changes.
            if self.__dict__.get("local_folders") is not None:

                import os

                for folder in self.local_folders:

                    for file in os.listdir(folder):

                        #The itelligantly joins the folder path and the file name into a filepath. It will use the right structure based on the OS the bot is running on.
                        id = os.path.join(folder,file)

                        #If the file exists in our database, remove it from the queried list.
                        #By doing this, we will list of files that are in our database but not in the local folder.
                        if id in db:

                            db.remove(id)

                        else:

                            #If the file is not in our database, we add it to the database
                            #We use the file path as the ID for local files as the file path must be unique.
                            self.cursor.execute("INSERT INTO '{}' VALUES (:ID, :NAME, 'LOCAL', 'POSTED'=False)".format(self.name),
                            {"ID":id, "NAME":file})

                            self.logger.info("ADDED: {} ({})".format(file, id))

            #The remainder of the entires in the db array are files that exist in our database, but do not exist in any of the provided folders.
            #We will remove these entries from our database.
            for file in db:

                #Grab the name of the file we are about to delete, we want this for logging purposes.
                self.cursor.execute("SELECT NAME FROM '{}' WHERE ID=:ID".format(self.name),
                {"ID":file})
                
                name = self.cursor.fetchone()

                self.cursor.execute("DELETE FROM '{}' WHERE ID=:ID".format(self.name),
                {"ID":file})
            
                self.logger.info("DELETED: {} ({})".format(name, file))

        self.logger.info("Database is up to date!")

    #This function sets the "Posted" value to false for all memebers in our database.
    def resetdb(self):

        #Set the posted on all entries to FALSE
            with self.connection:
                self.logger.info("Restting database...")
                self.cursor.execute("UPDATE '{}' SET POSTED=FALSE".format(self.name))
                self.logger.info("Database Reset!")

    #This function downloads an image from Google Drive and returns a BytesIO object whith some special fields added.
    def DownloadFromDrive(self, id):
        
        from io import BytesIO

        self.logger.info("Fetching data from Google Drive...")

        #Create a Google Drive file object of the media.
        file = self.drive.CreateFile({'id': id})
        
        self.logger.info("DOWNLOADING: {} ({})".format(file['title'],file['id']))

        #We will now write the data from the media to a buffer (BytesIO).
        self.logger.info("Writing data to buffer...")
        
        io = BytesIO()

        #GetContentIOBuffer() returns a interable which we write a chunk of data at a time to a buffer.
        for chunk in file.GetContentIOBuffer():
           io.write(chunk)

        #Make sure that we set the seek to the beginning so our progrma starts reading the buffer from the front.
        io.seek(0)
        
        media= Media(io,file['mimeType'],file['title'],id)
        #Add some useful information to the object

        #Return the media object.
        return media

    #The function downloads a random file from our database.
    def GetRandom(self,no_repeat=True):
        
        import random
    
        self.logger.info("Selecting media from database...")

        #If we don't care about repeats, then just grab an entry.
        if no_repeat == False:
             self.cursor.execute("SELECT * FROM '{}'".format(self.name))
             db = self.cursor.fetchall()

        else:
            #Grab a list of files that haven't been posted from the database.
            self.cursor.execute("SELECT * FROM '{}' WHERE POSTED=FALSE".format(self.name))
            db = self.cursor.fetchall()
        
            #If all the files have been posted, reset the database.
            if db == []:
                self.logger.info("Have posted all photos!")
                
                self.resetdb()
                
                #Get an array of all members of the database.
                self.cursor.execute("SELECT * FROM '{}' WHERE POSTED=FALSE".format(self.name))
                db = self.cursor.fetchall()
                self.logger.info("Selecting media from database...")

        #Choose a random row in our database.
        row = random.choice(db)
        self.logger.info("Selected {} ({})!".format(row[1], row[0]))

        #return a media object downloaded from Drive.
        if row[2] == "DRIVE":
            return self.DownloadFromDrive(row[0])

        #If it is a local file, then return a media object made out of the file.
        elif row[2] == "LOCAL":
            import mimetypes
            return Media(open(row[0],"rb"), mimetypes.guess_type(row[0])[0],row[1],row[0])