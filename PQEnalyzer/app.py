import tkinter
import tkinter.messagebox
import customtkinter

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    """
    The main application class for the Enalyzer application. This class inherits from the CTK class.
    """

    def __init__(self):
        super().__init__()

        self.title("Enalyzer - MolarVerse")
        

if __name__ == "__main__":
    app = App()
    app.mainloop()
        

