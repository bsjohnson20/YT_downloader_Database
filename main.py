# Python program to download youtube video, scrape name, channel, URL and store in a database
import sqlite3
import sys
import webbrowser
import json
# Kivy imports
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
import ytdownloader as ytdl_class
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivymd.uix.gridlayout import GridLayout
from kivymd.uix.card import MDCard
# from kivymd.uix.datatables import MDDataTable
from datatables import MDDataTable
from kivy.metrics import dp
from kivy.uix.settings import SettingsWithSidebar
from kivy.clock import Clock
# from kivymd.toast import toast
from kivy.uix.progressbar import ProgressBar

from kivy import platform
if platform == 'android':
    from kivymd.toast import toast
    from android.permissions import request_permissions, Permission, check_permission  # pylint: disable=import-error # type: ignore
    request_permissions([Permission.READ_EXTERNAL_STORAGE,
                        Permission.WRITE_EXTERNAL_STORAGE])
elif platform == 'linux':
    from kivymd.uix.snackbar.snackbar import MDSnackbar, MDSnackbarSupportingText
else:
    pass

# Experimental likely to cause issues
import asyncio
from kivy.app import async_runTouchApp
import threading

import re
from kivymd.uix.progressindicator import MDLinearProgressIndicator



class Manager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(HomeScreen(name='home'))
        self.add_widget(DownloadScreen(name='download'))
        self.add_widget(TestScreen(name='test'))
        self.add_widget(DatabaseOutputScreen(name='output'))
        self.add_widget(AddDatabase(name='adddatabase'))
        self.add_widget(MissingVideoScreen(name='missing'))
        self.add_widget(DownloadAudioScreen(name='audio'))

class DatabaseOutputScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        # table columns: name, url, channel, length
        self.table = MDDataTable(
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(1, 0.9),
            column_data=[
                ("Name", dp(50)),
                ("URL", (dp(30))),
                ("Channel", dp(30)),
                ("Length", dp(30)),
            ],
            use_pagination=True,
            row_data=[],
        )
        self.table.bind(on_row_press=self.on_row_press)
        self.ids.body.add_widget(self.table)
        self.data = self.table.row_data
    
    def on_enter(self, *args):
        self.generateData()
        return super().on_enter(*args)

    def on_row_press(self,  table, row):
        # get start index from selected row item range
        start_index, end_index = row.table.recycle_data[row.index]["range"]
        webbrowser.open(row.table.recycle_data[start_index+2]["text"])
        
    
    def generateData(self):
        # read db path from settings
        self.dbpath = MDApp.get_running_app().config.get('Settings','dbpath')
        rows = MDApp.get_running_app().downloader.fetchall()
        
        # conn = sqlite3.connect(self.dbpath)
        # c = conn.cursor()
        # c.execute("SELECT * FROM videos")
        # rows = c.fetchall()
        self.table.row_data = rows
    
    def clearData(self):
        self.table.row_data = []
        self.table.update_row_data(self.table,self.data)


class ScrollTemplate(MDCard):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # name, url, channel, length


class Title(GridLayout):
    text = StringProperty()
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TestScreen(Screen):
    pass


class Hook:
    def hook(self, *args):
        # add progress bar
        percent = float(args[0]['_percent_str'].split('m')[1].split('%')[0])
        
        # debugging
        # with open('stderr2', 'a') as f:
        #     f.write("\n"+str(percent))
        # print(percent)

        if args[0]['status'] == 'downloading':
            self.pb.value = percent
            print(percent)
            
        elif args[0]['status'] == 'finished':
            
            # Toast download complete
            # toast("Download complete")
            self.snackbar.update_text("Download complete")
            # with open('stderr2', 'a') as f:
            #     f.writelines(("\nDownload complete", str(percent), str(args)))
                
            Clock.schedule_once(self.snackbar.open)
            
            self.pb.value = 100
            # delete kids
            for child in self.ids['scroll'].ids['scroll'].boxes.children:
                if child != self.pb:
                    self.ids['scroll'].ids['scroll'].boxes.remove_widget(child)
        elif args[0]['status'] == 'error':
            self.pb.value = 100
            self.snackbar.update_text("Download Failed")
            Clock.schedule_once(self.snackbar.open)           
        else:
            self.pb.value = 0
            self.snackbar.update_text("Unknown error")
            Clock.schedule_once(self.snackbar.open)
        

class SnackBar(MDSnackbar):
    def __init__(self, text,**kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.duration = 2
        self.gravity = 'top'
        self.snackbar = MDSnackbarSupportingText(text=self.text)
        self.add_widget(self.snackbar)
    def open(self,*args):
        return super().open()
    def update_text(self, text):
        self.snackbar.text = text

class DownloadScreen(Screen, Hook):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.toast_text = ""
        # create snackbar but don't show it
        self.snackbar = SnackBar(text=self.toast_text)
        

    
    def on_enter(self, *args):
        
        
        # create progress bar
        # self.pb = ProgressBar(max=1000, size_hint=(1, None), height=30, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        
        # add progress bar to scrollview
        
        self.pb = MDLinearProgressIndicator(max=100, value=0)
        self.pb.size_hint = (1, None)
        self.pb.height = 30
        self.pb.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.ids['scroll'].ids['scroll'].boxes.add_widget(self.pb)
        return super().on_enter(*args)
        
    
            

    def fetchall(self, *args):
        print("Video Download Started")
        downloads=[]
        
        # toast("Downloading started \
        #       Screen will freeze.")
        for child in self.ids['scroll'].ids['scroll'].boxes.children:
            if child == self.pb:
                continue
            if child.text != '':
                if ' ' in child.text:
                    for item in child.text.split(' '):
                        downloads.append(item)
                else:
                    downloads.append(child.text)
                # downloads.append(child.text)
        
        # MDApp.get_running_app().downloader.download_videos(downloads)
        print(downloads)
        MDApp.get_running_app().downloader.download_videos(downloads, hook=self.hook, audio=False)
        # toast("Download complete")
        # clear scrollview
        self.ids['scroll'].ids['scroll'].boxes.clear_widgets()


    def download(self):
        threading.Thread(target=self.fetchall).start()

    def on_leave(self, *args):
        # clear scrollview
        self.ids['scroll'].ids['scroll'].boxes.clear_widgets()
        return super().on_leave(*args)
    
class DownloadAudioScreen(Screen, Hook):
    def __init__(self, **kw):
        super().__init__(**kw)

    async def fetchall(self): # audio version
        downloads=[]
        print("Downloading started Audio")
        # toast("Downloading started \
        #       Screen will freeze.")
        for child in self.ids['scroll'].ids['scroll'].boxes.children:
            if child.text != '':
                if ' ' in child.text:
                    for item in child.text.split(' '):
                        downloads.append(item)
                else:
                    downloads.append(child.text)
                # downloads.append(child.text)
        MDApp.get_running_app().downloader.download_audio(' '.join(downloads), hook=self.hook)
        # toast("Download complete")
        # clear scrollview
        self.ids['scroll'].ids['scroll'].boxes.clear_widgets()
        
    def download(self):
        self.fetchall()

    def on_leave(self, *args):
        # clear scrollview
        self.ids['scroll'].ids['scroll'].boxes.clear_widgets()
        return super().on_leave(*args)
        


class AddDatabase(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

    def fetchall(self):
        downloads=[]
        for child in self.ids['scroll'].ids['scroll'].boxes.children:
            if child.text != '':
                downloads.append(child.text)
        MDApp.get_running_app().downloader.only_add_to_database(downloads)

    def download(self):
        self.fetchall()

class URLScroll(BoxLayout):
    def add_entry(self):
        self.ids['buttonview'].add_widget(MDTextField(hint_text="Enter URL here", size_hint=(1, None), height=30, pos_hint={'center_x': 0.5, 'center_y': 0.5}))
        self.buttonview = self.ids['buttonview']

class HomeScreen(Screen):
    # have title, scrollable input field with + button to add more input fields and download button with progress bar
    def __init__(self, **kw):
        super().__init__(**kw)
        self.details_data = [
            # download path, database path
            ("Download Path", MDApp.get_running_app().config.get('Settings','downloadpath')),
            ("Database Path", MDApp.get_running_app().config.get('Settings','dbpath')),
            ("Missing videos", "default"),
        ]
        self.columns = [
            ("Name", dp(50)),
            ("Data", (dp(90)))]

        self.home_table = MDDataTable(
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(0.9, 0.6),
            rows_num=4,
            column_data=self.columns,
            row_data=self.details_data,
        )
        Clock.schedule_once(self.update_missingVideos)
        self.ids['data'].add_widget(self.home_table)

    def on_enter(self, *args):
        pass
    
    def missingDBvideos(self):
        # set screen to missing videos screen
        MDApp.get_running_app().manager.current = 'missing'



    def update_missingVideos(self, *args):
        number_missing = ("Missing videos", str(len(MDApp.get_running_app().downloader.missingDBvideos())))
        # update table
        self.home_table.row_data[2] = number_missing
        # update details data
        self.details_data[2] = number_missing
        


class MissingVideoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        # table columns: name, url, channel, length
        self.table = MDDataTable(
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(1, 0.9),
            column_data=[
                ("Name", dp(130))
            ],
            use_pagination=True,
            row_data=[],
        )
        self.table.bind(on_row_press=self.on_row_press)
        self.ids.body.add_widget(self.table)
        self.data = self.table.row_data

    def on_enter(self, *args):
        # self.generateData()
        return super().on_enter(*args)

    def on_row_press(self,  table, row):
        # get start index from selected row item range
        start_index, end_index = row.table.recycle_data[row.index]["range"]
        webbrowser.open(row.table.recycle_data[start_index+2]["text"])

    def generateData(self):
        # read db path from settings
        x = []
        source_videos = MDApp.get_running_app().downloader.missingDBvideos()
        for i in source_videos:
            x.append((i,)) # what a weird workaround
        self.data = x
        self.table.update_row_data(self.table,self.data)
    
    def clearData(self):
        self.table.row_data = []
        self.data = []
        self.table.update_row_data(self.table,self.data)

class YoutubeGUIApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Youtube Downloader"

    def build(self):
        self.manager = Manager()
        self.theme_cls.theme_style = "Dark"
        self.settings_cls = SettingsWithSidebar
        # self.config.read('mysettings.ini')
        return self.manager
    
    def thread_gui_operations(self, operation):
        # lets you run threads and update the GUI
        Clock.schedule_once(operation)
    
    def on_start(self):
        sys.stderr = open('./stderr', 'w')
        # change screen to home screen
        # inherit from download class
        # read download path from settings
        self.user_path = MDApp.get_running_app().config.get('Settings','downloadpath')
        self.downloader = ytdl_class.YoutubeNDatabaseDownloader(user_path=self.user_path,database=self.user_path+'/videos.db')

    def build_config(self, config):
        config.setdefaults('Settings', {
            'fullscreen': False,
            'showdebug': False,
            'downloadpath': './',
            'dbpath': './videos.db',
            'randomnumber': '69420'
        })
        return super().build_config(config)

    def build_settings(self, settings):

        settings_json = json.dumps(
    [
        {'type':'title','title':'Settings'},
        {'type':'bool','title':'Fullscreen','desc':'Set the window in windowed or fullscreen','section':'Settings','key':'fullscreen'},
        {'type':'bool','title':'Show debug','desc':'Show debug','section':'Settings','key':'showdebug'},
        {'type':'string','title':'Download Path','desc':'Path to where videos are downloaded','section':'Settings','key':'downloadpath'},
        {'type':'string','title':'Database Path','desc':'Path to where the database is located','section':'Settings','key':'dbpath'},
        {'type':'string','title':'Random Number','desc':'Random number','section':'Settings','key':'randomnumber'},
    ])


        settings.add_json_panel('Settings', self.config, data=settings_json)
        '''The json file will be loaded and constructs the layout of the menu'''


if __name__ == "__main__":
    runAsync = True
    if runAsync:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_runTouchApp(YoutubeGUIApp().run()))
        loop.close()
    else:
        YoutubeGUIApp().run()
    # downloader = YoutubeNDatabaseDownloader()
