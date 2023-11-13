import customtkinter

from PQEnalyzer.custom_theme import default_theme

class App(customtkinter.CTk):
    """
    The main application class for the Enalyzer application. This class inherits from the CTK class.
    """

    def __init__(self):
        super().__init__()

        default_theme()

        self.title("PQEnalyzer - MolarVerse")
        
        

if __name__ == "__main__":
    app = App()
    app.mainloop()
