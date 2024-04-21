import matplotlib.pyplot as plt
import numpy as np
import os

class Plot:
    """
    The plot class for the PQEnalyzer application.

    ...

    Attributes
    ----------
    app : App
        The main application object.
    
    Methods
    -------
    build_plot()
        Build the plot.
    plot(info_parameter)
        Plot the data.
    """

    def __init__(self, app):
        """
        Constructs all the necessary attributes for the Plot object.
        """
        self.app = app
        self.reader = app.reader

    def build_plot(self):
        """
        Build the plot.
        """
        self.plot_frame = plt.figure()
        self.ax = self.plot_frame.add_subplot(111)

    
    def plot(self, info_parameter: str):
        """
        Plot the data.
        """
        # if button is not checked, plot main data
        if not self.app.plot_main_data.get():
            for i, energy in enumerate(self.reader.energies):
                basename = os.path.basename(self.reader.filenames[i])
                self.ax.plot(energy.simulation_time, energy.data[energy.info[info_parameter]], label=basename)

        self.__statistics(info_parameter)

        # TODO: implement steps to ps time conversion
        # self.ax.set_xlabel(f'Simulation time / {self.reader.energies[0].units["SIMULATION-TIME"]}')
        self.ax.set_xlabel(f'Simulation step')
        self.ax.set_ylabel(f'{info_parameter} / {self.reader.energies[0].units[info_parameter]}')
        # legend outside of plot
        self.ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.10), ncol=5, fancybox=True, shadow=True)
        self.plot_frame.show()
        

    def __statistics(self, info_parameter: str):
        """
        Plot the statistics.
        """
        if self.app.mean.get():
            self.ax.plot(*self.__mean(info_parameter), label="Mean", linestyle="--")
        if self.app.cummulative_average.get():
            self.ax.plot(*self.__cummulative_average(info_parameter), label="Cummulative Average", linestyle="--")
        if self.app.auto_correlation.get():
            self.ax.plot(*self.__auto_correlation(info_parameter), label="Auto Correlation", linestyle="--")
        if self.app.running_average.get():
            window_size = self.app.window_size.get()
            if window_size == "":
                window_size_int = 10
            else:
                window_size_int = int(window_size)
            self.ax.plot(*self.__running_average(info_parameter,  window_size_int), label='Running Average (' + str(window_size_int) + ')', linestyle="--")
        return self.ax
        
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
        data = np.concatenate([energy.data[energy.info[info_parameter]] for energy in self.reader.energies])
        running_average = [sum(data[i:i+window_size])/window_size for i in range(len(data) - window_size + 1)]
        time = np.concatenate([energy.simulation_time for energy in self.reader.energies])[window_size-1:]
        return time , running_average
