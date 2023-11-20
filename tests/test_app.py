import pytest
import customtkinter
import tkinter

from PQEnalyzer.classes.app import App

class TestApp:
    """
    Test the App class.
    """

    app = App()

    def test_instance(self):
        assert isinstance(self.app, App)
        assert isinstance(self.app, customtkinter.CTk)
        assert isinstance(self.app, tkinter.Tk)
    
    def test_title(self):
        assert self.app.title() == "PQEnalyzer - MolarVerse"

