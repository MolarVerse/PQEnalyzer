from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
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
        self.figure = Figure(figsize=(10, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=3, rowspan=3, columnspan=2, sticky="nsew")
    
    def plot(self, info_parameter: str):
        """
        Plot the data.
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        for i, energy in enumerate(self.reader.energies):
            basename = os.path.basename(self.reader.get_filenames()[i])
            ax.plot(energy.simulation_time, energy.data[energy.info[info_parameter]], label=basename)

        self.__statistics(ax, info_parameter)

        ax.set_xlabel(f'Simulation time / {self.reader.energies[0].units["SIMULATION-TIME"]}')
        ax.set_ylabel(f'{info_parameter} / {self.reader.energies[0].units[info_parameter]}')
        # legend outside of plot
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.10), ncol=5, fancybox=True, shadow=True)
        self.canvas.draw()

    def __statistics(self, ax, info_parameter: str):
        if self.parent.mean.get():
            ax.plot(*self.__mean(info_parameter), label="Mean", linestyle="--", color="blue")
        if self.parent.cummulative_average.get():
            ax.plot(*self.__cummulative_average(info_parameter), label="Cummulative Average", linestyle="--", color="red")
        if self.parent.auto_correlation.get():
            ax.plot(*self.__auto_correlation(info_parameter), label="Auto Correlation", linestyle="--", color="orange")
        if self.parent.running_average.get():
            window_size = self.parent.window_size.get()
            ax.plot(*self.__running_average(info_parameter,  window_size), label='Running Average (' + str(window_size) + ')', linestyle="--", color="green")
        return ax
        
    def __mean(self, info_parameter):
        """
        Calculate the mean of the data.
        """
        time = np.concatenate([energy.simulation_time for energy in self.reader.energies])
        data = np.concatenate([energy.data[energy.info[info_parameter]] for energy in self.reader.energies])
        mean = np.mean(data)
        return [time[0], time[-1]], [mean, mean]

    def __cummulative_average(self, info_parameter):
        """
        Calculate the cummulative average of the data with a given window size.
        """
        data = np.concatenate([energy.data[energy.info[info_parameter]] for energy in self.reader.energies])
        cummulative_average = np.cumsum(data)/np.arange(1, len(data)+1)
        time = np.concatenate([energy.simulation_time for energy in self.reader.energies])
        return time, cummulative_average

    def __auto_correlation(self, info_parameter):
        """
        Calculate the auto correlation of the data.
        """
        data = np.concatenate([energy.data[energy.info[info_parameter]] for energy in self.reader.energies])
        auto_correlation = np.correlate(data, data, mode='same')/np.correlate(np.ones_like(data), data, mode='same')
        time = np.concatenate([energy.simulation_time for energy in self.reader.energies])
        return time, auto_correlation
    
    def __running_average(self, info_parameter, window_size):
        """
        Calculate the running average of the data with a given window size.
        """
        if window_size == "":
            window_size = 10
        else:
            window_size = int(window_size)
        
        data = np.concatenate([energy.data[energy.info[info_parameter]] for energy in self.reader.energies])
        running_average = [sum(data[i:i+window_size])/window_size for i in range(len(data) - window_size + 1)]
        time = np.concatenate([energy.simulation_time for energy in self.reader.energies])[window_size-1:]
        return time , running_average
