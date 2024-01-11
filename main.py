# Python program to download youtube video, scrape name, channel, URL and store in a database
import os
import re
import sqlite3
from kivymd.uix.button import MDFlatButton
from yt_dlp import YoutubeDL
# env file
import dotenv as dot
import csv
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
import ytdownloader as ytdl_class
from kivy.properties import ObjectProperty
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.uix.widget import Widget
from kivymd.uix.button import MDIconButton
from kivymd.uix.gridlayout import GridLayout
class Manager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(HomeScreen(name='home'))
        self.add_widget(DownloadScreen(name='download'))
        self.add_widget(TestScreen(name='test'))

class Title(GridLayout):
    text = StringProperty()
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TestScreen(Screen):
    pass

class DownloadScreen(Screen):
    pass
class URLScroll(BoxLayout):
    def add_entry(self):
        self.ids['buttonview'].add_widget(MDTextField(hint_text="Enter URL here", size_hint=(1, None), height=30, pos_hint={'center_x': 0.5, 'center_y': 0.5}))

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
        return self.manager
    
    def on_start(self):
        # change screen to home screen
        # inherit from download class
        self.downloader = ytdl_class.YoutubeNDatabaseDownloader()


if __name__ == "__main__":
    YoutubeGUIApp().run()
    # downloader = YoutubeNDatabaseDownloader()
