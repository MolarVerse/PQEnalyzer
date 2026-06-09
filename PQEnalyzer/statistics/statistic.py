"""
Numeric statistics used by PQEnalyzer plots.

The public energy-based methods are compatibility wrappers for existing call
sites. The ``*_values`` methods contain the actual numeric implementations and
operate only on aligned time/value arrays.
"""

import numpy as np

from ..energy_access import concatenate_series


class Statistic:
    """
    Namespace for stateless plotting statistics.

    Methods
    -------
    mean(energies, info_parameter)
        Calculate a horizontal mean line for a Reader energy parameter.
    mean_values(time, values)
        Calculate a horizontal mean line for numeric arrays.
    median(energies, info_parameter)
        Calculate a horizontal median line for a Reader energy parameter.
    median_values(time, values)
        Calculate a horizontal median line for numeric arrays.
    cumulative_average(energies, info_parameter)
        Calculate cumulative average values for a Reader energy parameter.
    cumulative_average_values(time, values)
        Calculate cumulative average values for numeric arrays.
    cummulative_average(energies, info_parameter)
        Backward-compatible alias for cumulative_average.
    auto_correlation(energies, info_parameter)
        Calculate normalized autocorrelation for a Reader energy parameter.
    auto_correlation_values(time, values)
        Calculate normalized autocorrelation for numeric arrays.
    running_average(energies, info_parameter, window_size)
        Calculate a centered running average for a Reader energy parameter.
    running_average_values(time, values, window_size)
        Calculate a centered running average for numeric arrays.

    Raises
    ------
    TypeError
        If the class is instantiated; all methods are static.

    Examples
    --------
    >>> Statistic.mean_values([1, 2, 3], [10, 20, 30])
    (array([1, 3]), array([20., 20.]))
    """

    def __new__(cls, *args, **kwargs):
        raise TypeError("Statistic class cannot be instantiated.")

    @staticmethod
    def mean(energies: list, info_parameter: str) -> tuple:
        """
        Calculate a horizontal mean line for an energy parameter.

        Parameters
        ----------
        energies : list
            A list of energy objects.
        info_parameter : str
            The info parameter to calculate the mean of.

        Returns
        -------
        tuple
            A tuple containing the time and mean of the data.

        Examples
        --------
        >>> Statistic.mean(energies, "ENERGY")
        ([1, 5], [1.0, 1.0])
        """

        energy_series = concatenate_series(energies, info_parameter)
        return Statistic.mean_values(energy_series.time, energy_series.values)

    @staticmethod
    def mean_values(time, values) -> tuple:
        """
        Calculate the mean line for a numeric series.

        The returned time axis contains the first and last input time so the
        line spans the plotted data range.
        """

        time, data = Statistic.__arrays(time, values)
        mean = np.mean(data)

        return np.array([time[0], time[-1]]), np.array([mean, mean])

    @staticmethod
    def median(energies: list, info_parameter: str) -> tuple:
        """
        Calculate a horizontal median line for an energy parameter.

        Parameters
        ----------
        energies : list
            A list of energy objects.
        info_parameter : str
            The info parameter to calculate the median of.

        Returns
        -------
        tuple
            A tuple containing the time and median of the data.

        Examples
        --------
        >>> Statistic.median(energies, "ENERGY")
        ([1, 5], [1.0, 1.0])
        """

        energy_series = concatenate_series(energies, info_parameter)
        return Statistic.median_values(energy_series.time,
                                       energy_series.values)

    @staticmethod
    def median_values(time, values) -> tuple:
        """
        Calculate the median line for a numeric series.

        The returned time axis contains the first and last input time so the
        line spans the plotted data range.
        """

        time, data = Statistic.__arrays(time, values)
        median = np.median(data)

        return np.array([time[0], time[-1]]), np.array([median, median])

    @staticmethod
    def cumulative_average(energies: list, info_parameter: str) -> tuple:
        """
        Calculate cumulative average values for an energy parameter.

        Parameters
        ----------
        energies : list
            A list of energy objects.
        info_parameter : str
            The info parameter to calculate the cumulative average of.

        Returns
        -------
        tuple
            A tuple containing the time and cumulative average of the data.

        Examples
        --------
        >>> Statistic.cumulative_average(energies, "ENERGY")
        ([1, 2, 3, 4, 5], [2.1666, 2.8571, 3.6666, 4., 4.3333])
        """

        energy_series = concatenate_series(energies, info_parameter)
        return Statistic.cumulative_average_values(energy_series.time,
                                                   energy_series.values)

    @staticmethod
    def cumulative_average_values(time, values) -> tuple:
        """
        Calculate the cumulative average for a numeric series.

        Each output value is the average of all values from the first point
        through the current point.
        """

        time, data = Statistic.__arrays(time, values)
        cumulative_average = np.cumsum(data) / np.arange(1, len(data) + 1)

        return time, cumulative_average

    @staticmethod
    def cummulative_average(energies: list, info_parameter: str) -> tuple:
        """
        Backward-compatible alias for cumulative_average.
        """

        return Statistic.cumulative_average(energies, info_parameter)

    @staticmethod
    def auto_correlation(energies, info_parameter) -> tuple:
        """
        Calculate the normalized autocorrelation of the data.

        Parameters
        ----------
        energies : list
            A list of energy objects.
        info_parameter : str
            The info parameter to calculate the auto correlation of.

        Returns
        -------
        tuple
            A tuple containing the time and normalized autocorrelation data.

        Examples
        --------
        >>> Statistic.auto_correlation(energies, "ENERGY")
        ([1, 2, 3, 4, 5], [1., 0.4, -0.1, -0.4, -0.4])
        """

        energy_series = concatenate_series(energies, info_parameter)
        return Statistic.auto_correlation_values(energy_series.time,
                                                 energy_series.values)

    @staticmethod
    def auto_correlation_values(time, values) -> tuple:
        """
        Calculate the normalized autocorrelation for a numeric series.

        Constant series are reported as a unit impulse: one at zero lag and
        zero afterwards. That keeps the result finite and plot-friendly.
        """

        time, data = Statistic.__arrays(time, values)
        data = data.astype(float)

        centered_data = data - np.mean(data)
        zero_lag_correlation = np.dot(centered_data, centered_data)

        if zero_lag_correlation == 0:
            auto_correlation = np.zeros_like(data)
            auto_correlation[0] = 1
        else:
            auto_correlation = (
                np.correlate(centered_data, centered_data,
                             mode="full")[len(data) - 1:] /
                zero_lag_correlation)

        return time, auto_correlation

    @staticmethod
    def running_average(energies, info_parameter, window_size) -> tuple:
        """
        Calculate a centered running average for an energy parameter.

        Parameters
        ----------
        energies : list
            A list of energy objects.
        info_parameter : str
            The info parameter to calculate the running average of.
        window_size : int
            The window size to calculate the running average with.

        Returns
        -------
        tuple
            A tuple containing the time and running average of the data.

        Raises
        ------
        ValueError
            If the window size is not positive or is larger than the data.

        Examples
        --------
        >>> Statistic.running_average(energies, "ENERGY", 2)
        ([1.5, 2.5, 3.5, 4.5], [10.5, 11.5, 12.5, 13.5])
        """

        energy_series = concatenate_series(energies, info_parameter)
        return Statistic.running_average_values(energy_series.time,
                                                energy_series.values,
                                                window_size)

    @staticmethod
    def running_average_values(time, values, window_size) -> tuple:
        """
        Calculate the centered running average for a numeric series.

        Output time values are centered by averaging the input time values
        inside each window.
        """

        time, data = Statistic.__arrays(time, values)

        if window_size < 1:
            raise ValueError("Window size must be positive")

        # Check if data is smaller than window_size
        if len(data) < window_size:
            raise ValueError("Window size is larger than given data point")

        running_average = np.array([
            np.sum(data[i:i + window_size]) / window_size
            for i in range(len(data) - window_size + 1)
        ])

        time = np.array([
            np.mean(time[i:i + window_size])
            for i in range(len(data) - window_size + 1)
        ])

        return time, running_average

    @staticmethod
    def __arrays(time, values) -> tuple:
        """
        Convert inputs to arrays without tying statistics to energy objects.
        """

        return np.asarray(time), np.asarray(values)
