from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

class Plot:

    def __init__(self, parent, data):
        """
        Constructs all the necessary attributes for the Plot object.
        """
        self.parent = parent
        self.data = data

        self.__build_plot()

    def __build_plot(self):
        """
        Build the plot.
        """
        self.figure = Figure(figsize=(5, 4), dpi=100, tight_layout=True)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=3, sticky="nsew")
    
    def plot(self, info_parameter: str):
        """
        Plot the data.
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        for en in self.data:
            ax.plot(en.simulation_time, en.data[en.info[info_parameter]])

        ax.set_xlabel(f'Simulation time / {self.data[0].units["SIMULATION-TIME"]}')
        ax.set_ylabel(f'{info_parameter} / {self.data[0].units[info_parameter]}')
        self.canvas.draw()
    