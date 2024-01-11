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
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
from kivy.uix.settings import SettingsWithSidebar







class Manager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(HomeScreen(name='home'))
        self.add_widget(DownloadScreen(name='download'))
        self.add_widget(TestScreen(name='test'))
        self.add_widget(DatabaseOutputScreen(name='output'))
        self.add_widget(AddDatabase(name='adddatabase'))

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
        conn = sqlite3.connect(self.dbpath)
        c = conn.cursor()
        c.execute("SELECT * FROM videos")
        rows = c.fetchall()
        self.table.row_data = rows
        #self.table.update_row_data()
    
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

class DownloadScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

    def fetchall(self):
        downloads=[]
        for child in self.ids['scroll'].ids['scroll'].boxes.children:
            if child.text != '':
                downloads.append(child.text)
        MDApp.get_running_app().downloader.download_videos(downloads)
        # for widget in self.ids['scroll'].children:
        #     print(widget.ids['title'].text)
        #     print(widget.ids['url'].text)
        #     print(widget.ids['channel'].text)
        #     print(widget.ids['length'].text)
        #     print()

    def download(self):
        self.fetchall()

class AddDatabase(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

    def fetchall(self):
        downloads=[]
        for child in self.ids['scroll'].ids['scroll'].boxes.children:
            if child.text != '':
                downloads.append(child.text)
        MDApp.get_running_app().downloader.only_add_to_database(downloads)
        # for widget in self.ids['scroll'].children:
        #     print(widget.ids['title'].text)
        #     print(widget.ids['url'].text)
        #     print(widget.ids['channel'].text)
        #     print(widget.ids['length'].text)
        #     print()

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
    def on_enter(self, *args):
        print("Entered Home Screen")
    
    

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
            'downloadpath': '/home/lunachocken/Videos/YT',
            'dbpath': '/home/lunachocken/Videos/YT/videos.db',
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
    YoutubeGUIApp().run()
    # downloader = YoutubeNDatabaseDownloader()
