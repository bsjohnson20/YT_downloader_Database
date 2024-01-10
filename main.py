# Python program to download youtube video, scrape name, channel, URL and store in a database
import os
import sqlite3
from yt_dlp import YoutubeDL
# env file
import dotenv as dot
dot.load_dotenv()

def download_video(url,quality='res:720 ',user_path='./videos/'):
    if not os.path.exists(user_path):
        os.makedirs(user_path)

    ydl_opts = {
        "format": "mp4[height=720]",
        'outtmpl': f'{user_path}/YouTube/%(uploader)s/%(title)s.%(ext)s',
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def get_video_info(url):
    # fetch name, channel, URL
    ydl_opts = {'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        meta = ydl.extract_info(url, download=False)
        name = meta['title']
        channel = meta['uploader']
        url = meta['webpage_url']
        length = meta['duration']
        return name, channel, url, length
    
if "__main__" == __name__:
    # using dotenv to store environment variables

    # check if dotenv file exists
    if not os.path.exists('.env'):
        print("No .env file found")
        # create .env file
        with open('.env','w') as f:
            f.write("VIDEOS_PATH=./videos/")
        print("Created .env file")
    
    else:
        # read from dotenv
        dot.load_dotenv()


    user_path = os.getenv('VIDEOS_PATH')
    if not user_path:
        user_path = './videos/'
        os.environ['VIDEOS_PATH'] = user_path
        print("Default path set to ./videos/")
    else:
        print(f"Default path set to {user_path}")

    # create database
    database = f"{user_path}/videos.db"
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS videos
                (name text, channel text, url text, length int)''')
    conn.commit()
    conn.close()

    while True:
        choice = input("1 - Download video/videos \n"
                       "2 - Change download path \n"
                       "3 - output database as csv \n"
                       "4 - download videos from text file \n"
                       "5 - only add to database\n"
                       "6 - set default path\n"
                       "7 - exit \n"
                       "Choice: ")
        
        if choice == '1':
            # get video/videos list of urls separated by space
            urls = input("Enter video URL(s): ").split()
            for url in urls:
                # download video
                download_video(url, user_path=user_path)

                print("TESTING")
                # get video info
                name, channel, url, length = get_video_info(url)

                # check if video url already exists in database
                conn = sqlite3.connect(database)
                c = conn.cursor()
                c.execute("SELECT * FROM videos WHERE url=?",(url,))
                if c.fetchone():
                    print("Video already exists in database")
                    continue
                conn.close()
                

                # add to database
                conn = sqlite3.connect(database)
                c = conn.cursor()
                c.execute("INSERT INTO videos VALUES (?,?,?,?)",(name, channel, url, length))
                conn.commit()
                conn.close()

                print("Video added to database")
        
        elif choice == '2':
            # set working directory
            os.chdir(input("Enter path: "))
            user_path = os.getcwd()
            print(f"Working directory set to {user_path}")


        
        elif choice == '3':
            # output database as csv
            conn = sqlite3.connect(database)
            c = conn.cursor()
            c.execute("SELECT * FROM videos")
            with open('videos.csv','w') as f:
                for row in c.fetchall():
                    f.write(f'{row[0]},{row[1]},{row[2]}\n')
            print("Database output as csv")
            conn.close()
        
        elif choice == '4':
            # download videos from text file
            with open('urls.txt','r') as f:
                for url in f.readlines():
                    url = url.strip()
                    download_video(url)
                    name, channel, url, length = get_video_info(url)
                    conn = sqlite3.connect(database)
                    c = conn.cursor()
                    c.execute("INSERT INTO videos VALUES (?,?,?,?)",(name, channel, url, length))
                    conn.commit()
                    conn.close()
            print("Videos added to database")

        elif choice == '5':
            # add video/videos to database
            # support multiple videos separated by space
            urls = input("Enter video URL(s): ").split()
            for url in urls:
                name, channel, url, length = get_video_info(url)
                conn = sqlite3.connect(database)
                c = conn.cursor()
                c.execute("INSERT INTO videos VALUES (?,?,?,?)",(name, channel, url, length))
                conn.commit()
                conn.close()
        
        elif choice == '6':
            # ask for default path
            path = input("Enter default path: ")
            os.environ['VIDEOS_PATH'] = path
            print(f"Default path set to {path}")

            # save to .env file
            with open('.env','w') as f:
                f.write(f"VIDEOS_PATH={path}")



        elif choice == '7':
            break
        else:
            print("Invalid choice")
    