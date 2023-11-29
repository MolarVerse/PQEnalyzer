from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import os

class Plot:

    def __init__(self, parent, reader):
        """
        Constructs all the necessary attributes for the Plot object.
        """
        self.parent = parent
        self.reader = reader

        self.__build_plot()

    def __build_plot(self):
        """
        Build the plot.
        """
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=3, sticky="nsew")
    
    def plot(self, info_parameter: str):
        """
        Plot the data.
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        for i, energy in enumerate(self.reader.energies):
            basename = os.path.basename(self.reader.get_filenames()[i])
            ax.plot(energy.simulation_time, energy.data[energy.info[info_parameter]], label=basename)

        ax.set_xlabel(f'Simulation time / {self.reader.energies[0].units["SIMULATION-TIME"]}')
        ax.set_ylabel(f'{info_parameter} / {self.reader.energies[0].units[info_parameter]}')
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.10), ncol=3)
        self.canvas.draw()
    