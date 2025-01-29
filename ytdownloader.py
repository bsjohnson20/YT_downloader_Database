import os
import re
import sqlite3
from yt_dlp import YoutubeDL
# env file
import dotenv as dot
import csv
import asyncio
# Downloading background
from threading import Thread



class Log:
    def debug(self, msg):
        pass#print(msg)
    def warning(self, msg):
        pass#print(msg)
    def error(self, msg):
        print(msg)

class YoutubeNDatabaseDownloader:
    def __init__(self, user_path='./videos/', database='./videos.db',cookie_file="./cookies",manual=False) -> None:
        # method to check if .env file exists
        self.user_path = user_path
        self.database = database
        self.cookie_file = cookie_file
        self.manual = manual
        self.check_env()
        self.create_database()
        
        self.status = 'idle'
        
        
        # print(self.user_path)
    def check_env(self):
        if self.user_path != './videos/':
            return
        # read from dotenv
        dot.load_dotenv()
        user_path = os.getenv('VIDEOS_PATH')
        if user_path != './videos/' and user_path != None:
            user_path = './videos/'
            os.environ['VIDEOS_PATH'] = user_path
            print("Default path set to ./videos/")
            self.database = r"./videos.db"
        else:
            print(f"Default path set to {user_path}")
            self.user_path = user_path
            self.database = f"{user_path}/videos.db"
            
    def hook(self,d):
        if d['status'] == 'downloading':
            print(d['filename'], d['_percent_str'])
        if d['status'] == 'finished':
            self.status = 'finished'



    async def download_video(self, url, hook=None):
        if hook == None:
            hook = self.hook
        print(f"Hook is {hook}")
        if not os.path.exists(self.user_path):
            os.makedirs(self.user_path)

        ydl_opts = {
            "format": "mp4[height<=720]",
            'outtmpl': f'{self.user_path}/YouTube/%(uploader)s/%(title)s.%(ext)s',
            'cookiesfrombrowser': ('firefox', None, None, None),
            'verbose' : 'True',
            'logger': Log()
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl._progress_hooks.append(hook)
            ydl.download([url])
            
            while self.status == 'downloading':
                await asyncio.sleep(1)
    
    async def download_audio(self, url,hook=None):
        if hook == None:
            hook = self.hook
        ydl_opts = {'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': f'{self.user_path}/YouTube/%(uploader)s/%(title)s.%(ext)s',
                    'cookiesfrombrowser': ('firefox', None, None, None)}
        # try:
        with YoutubeDL(ydl_opts) as ydl:
           ydl._progress_hooks.append(hook)
           ydl.download([url])
            
           while self.status == 'downloading':
               await asyncio.sleep(1)
            
        # except Exception as e:
        #     # temp catchall error handler
        #     print(f"Error downloading audio: {e}, likely missing ffmpeg")

    def get_video_info(self, url):
        # fetch name, channel, URL
        ydl_opts = {'skip_download': True,
                    'cookiesfrombrowser': ('firefox', None, None, None)}
        with YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url, download=False)
            name = meta['title']
            channel = meta['uploader']
            url = meta['webpage_url']
            length = meta['duration']
            return name, channel, url, length

    # create database
    def create_database(self):
        # recursively create folder path if it doesn't exist
        if not os.path.exists(self.user_path):
            os.makedirs(self.user_path)
            print(f"Created {self.user_path} directory")
        
        
        conn = sqlite3.connect(self.database)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS videos
                    (name text, channel text, url text, length int)''')
        conn.commit()
        conn.close()
        
    def fetchall(self):
        conn = sqlite3.connect(self.database)
        c = conn.cursor()
        c.execute("SELECT * FROM videos")
        rows = c.fetchall()
        return rows
    
    def add_db(self,name,channel,url,length):
        # add to db, check for duplicates 
        conn = sqlite3.connect(self.database)
        c = conn.cursor()
        c.execute("SELECT * FROM videos WHERE url = ?",(url,))
        rows = c.fetchall()
        results = len(rows)
        
        if results:
            print(f"{url} already exists in database")
            return False
        
        c.execute("INSERT INTO videos VALUES (?,?,?,?)",(name, channel, url, length))
        conn.commit()
        conn.close()
        return True
        
    
    def download_videos(self,urls=[],audio=False,hook=None):
        print(f"Downloading, audio: {audio}")
        # get video/videos list of urls separated by space
        # update this to be class variable
        if self.manual:
            urls = input("Enter video URL(s): ").split()
        for url in urls:
            # download 
            self.status = 'downloading'
            if audio:
                
                asyncio.run(self.download_audio(url,hook=hook))
                while self.status == 'downloading':
                    pass
            else:
                asyncio.run(self.download_video(url,hook=hook))
                # self.download_video(url)
                while self.status == 'downloading':
                    pass
            
            name, channel, url, length = self.get_video_info(url)
            self.add_db(name,channel,url,length)
          
    def output_database_as_csv(self):
        # export to csv within the same directory as py
        conn = sqlite3.connect(self.database)
        c = conn.cursor()
        c.execute("SELECT * FROM videos")
        rows = c.fetchall()
        with open('videos.csv','w') as f:
            writer = csv.writer(f)
            writer.writerow(['name','channel','url','length'])
            writer.writerows(rows)
        conn.close()
        print("Exported to videos.csv")
        
    def change_download_path(self):
        # set working directory
        os.chdir(input("Enter path: "))
        self.user_path = os.getcwd()
        print(f"Working directory set to {self.user_path}")

    def download_videos_from_text_file(self):
        # download videos from text file
        with open('urls.txt','r') as f:
            for url in f.readlines():
                url = url.strip()
                self.download_video(url)
                name, channel, url, length = self.get_video_info(url)
                success = self.add_db(name,channel,url,length)
                if success:
                    print(f"Added {url} to database")
                else:
                    print(f"Failed to add {url} to database")
                
        print("Videos added to database")

    def only_add_to_database(self,urls=[]):
        # add video/videos to database
        # support multiple videos separated by space
        if self.manual:
            urls = input("Enter video URL(s): ").split()
        for url in urls:
            name, channel, url, length = self.get_video_info(url)
            sucess = self.add_db(name,channel,url,length)
            if sucess:
                print(f"Added {url} to database")
            else:
                print(f"Failed to add {url} to database")
            

            

    def set_default_path(self):
        # ask for default path
        path = input("Enter default path: ")
        os.environ['VIDEOS_PATH'] = path
        print(f"Default path set to {path}")

        # save to .env file
        with open('.env','w') as f:
            f.write(f"VIDEOS_PATH={path}")
        
        # update database path
        self.database = f"{path}/videos.db"
        self.user_path = path

    
            

    def print_database(self):
        conn = sqlite3.connect(self.database)
        c = conn.cursor()
        c.execute("SELECT * FROM videos")
        rows = c.fetchall()
        for row in rows:
            print(row)
        conn.close()

    # check database for duplicates
    def check_database_for_duplicates(self):
        conn = sqlite3.connect(self.database)
        c = conn.cursor()
        c.execute("SELECT * FROM videos")
        rows = c.fetchall()
        conn.close()
        
        # check for duplicates using url
        rows = [row[2] for row in rows]
        if len(rows) != len(set(rows)):
            print("Duplicates found in database")
            # remove duplicates
            conn = sqlite3.connect(self.database)
            c = conn.cursor()
            c.execute("DELETE FROM videos WHERE rowid NOT IN (SELECT MIN(rowid) FROM videos GROUP BY url)")
            conn.commit()
            conn.close()
            print("Duplicates removed")
        else:
            print("No duplicates found in database")

    # find videos in storage that are not in database
    def missingDBvideos(self):
        # using recursive search
        videos = []
        print(self.user_path)
        for root, dirs, files in os.walk(self.user_path):
            for file in files:
                if file.endswith(".mp4"):
                    # strip video name of all special characters
                    file = re.sub(r'[^\w\s]', '', file)
                    videos.append(file.strip('mp4'))
        # get all videos in database
        
        # test file path is correct for self.database
        if not os.path.exists(self.database):
            print("Database path is incorrect")
            input()
        
        # remove duplicate / special characters
        self.database = re.sub(r"\/\/+","/",self.database)
        
        # test if folder exists
        if not os.path.exists(self.user_path):
            os.makedirs(self.user_path)
            print(f"Created {self.user_path} directory")
        
        conn = sqlite3.connect(self.database)
        c = conn.cursor()
        c.execute("SELECT * FROM videos")
        rows = c.fetchall()
        conn.close()
        # strip rows of all special characters
        rows = [re.sub(r'[^\w\s]', '', row[0]) for row in rows]
        videos = [re.sub(r'[^\w\s]', '', video) for video in videos]
        # find missing videos
        missing = []
        for video in videos:
            if video not in rows:
                print(video, "not in database",rows)
                missing.append(video)

        if missing:
            print("\n################Missing videos##########\n")
            for row in missing:
                print(row)
            print("\n########################################\n")
            return missing
        else:
            return []

    def init(self):
         # create database
        self.create_database()
        # check for duplicates
        self.check_database_for_duplicates()
        # find missing videos
        self.missingDBvideos()
    def choices(self):
        
        while True:
            choice = input("1 - Download video/videos \n"
                        "2 - Change download path \n"
                        "3 - output database as csv \n"
                        "4 - download videos from text file \n"
                        "5 - only add to database\n"
                        "6 - set default path\n"
                        "7 - print database\n"
                        "8 - exit \n"
                        "9 - download audio\n"
                        "Choice: ")

            if choice == '1':
                self.download_videos(audio=False)

            elif choice == '2':
                self.change_download_path()

            elif choice == '3':
                self.output_database_as_csv()

            elif choice == '4':
                self.download_videos_from_text_file()

            elif choice == '5':
                self.only_add_to_database()

            elif choice == '6':
                self.set_default_path()

            elif choice == '7':
                self.print_database()

            elif choice == '8':
                break
            elif choice == '9':
                self.download_videos([input("Enter video URL: ")],audio=True)
            else:
                print("Invalid choice")
                
                
if __name__ == "__main__":
    y = YoutubeNDatabaseDownloader('./',manual=True)
    y.choices()