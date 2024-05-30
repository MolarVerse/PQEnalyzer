"""
The statistic class for the PQEnalyzer application. This class contains
methods to calculate statistics of the data.
"""

import numpy as np


class Statistic:
    """
    The statistic class for the PQEnalyzer application. This class contains
    methods to calculate statistics of the data.

    ...

    Methods
    -------
    mean(energies, info_parameter)
        Calculate the mean of the data.
    median(energies, info_parameter)
        Calculate the median of the data.
    cummulative_average(energies, info_parameter)
        Calculate the cummulative average of the data with a given window size.
    auto_correlation(energies, info_parameter)
        Calculate the auto correlation of the data.
    running_average(energies, info_parameter, window_size)
        Calculate the running average of the data with a given window size.

    ...

    Raises
    ------
    TypeError
        If the class is instantiated.

    ...

    Examples
    --------
    >>> Statistic.mean(energies, "ENERGY")
    ([1, 5], [1.0, 1.0])
    >>> Statistic.median(energies, "ENERGY")
    ([1, 5], [1.0, 1.0])
    >>> Statistic.cummulative_average(energies, "ENERGY")
    ([1, 2, 3, 4, 5], [1, 1.5, 2, 2.5, 3])
    >>> Statistic.auto_correlation(energies, "ENERGY")
    ([1, 2, 3, 4, 5], [2.1666, 2.8571, 3.6666, 4., 4.3333])
    >>> Statistic.running_average(energies, "ENERGY", 2)
    ([1.5, 2.5, 3.5, 4.5], [10.5, 11.5, 12.5, 13.5])
    """

    def __new__(cls, *args, **kwargs):
        raise TypeError("Statistic class cannot be instantiated.")

    @staticmethod
    def mean(energies: list, info_parameter: str) -> tuple:
        """
        Calculate the mean of the data.

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

        time = np.concatenate([energy.simulation_time for energy in energies])

        data = np.concatenate(
            [energy.data[energy.info[info_parameter]] for energy in energies])

        mean = np.mean(data)

        return (np.array([time[0], time[-1]]), np.array([mean, mean]))

    @staticmethod
    def median(energies: list, info_parameter: str) -> tuple:
        """
        Calculate the median of the data.

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

        time = np.concatenate([energy.simulation_time for energy in energies])

        data = np.concatenate(
            [energy.data[energy.info[info_parameter]] for energy in energies])

        median = np.median(data)

        return (np.array([time[0], time[-1]]), np.array([median, median]))

    @staticmethod
    def cummulative_average(energies: list, info_parameter: str) -> tuple:
        """
        Calculate the cummulative average of the data with a given window size.

        Parameters
        ----------
        energies : list
            A list of energy objects.
        info_parameter : str
            The info parameter to calculate the cummulative average of.

        Returns
        -------
        tuple
            A tuple containing the time and cummulative average of the data.

        Examples
        --------
        >>> Statistic.cummulative_average(energies, "ENERGY")
        ([1, 2, 3, 4, 5], [2.1666, 2.8571, 3.6666, 4., 4.3333])
        """

        data = np.concatenate(
            [energy.data[energy.info[info_parameter]] for energy in energies])

        cummulative_average = np.cumsum(data) / np.arange(1, len(data) + 1)

        time = np.concatenate([energy.simulation_time for energy in energies])

        return time, cummulative_average

    @staticmethod
    def auto_correlation(energies, info_parameter) -> tuple:
        """
        Calculate the auto correlation of the data.

        Parameters
        ----------
        energies : list
            A list of energy objects.
        info_parameter : str
            The info parameter to calculate the auto correlation of.

        Returns
        -------
        tuple
            A tuple containing the time and auto correlation of the data.

        Examples
        --------
        >>> Statistic.auto_correlation(energies, "ENERGY")
        ([1, 2, 3, 4, 5], [2.1666, 2.8571, 3.6666, 4., 4.3333])
        """

        data = np.concatenate(
            [energy.data[energy.info[info_parameter]] for energy in energies])

        auto_correlation = np.correlate(
            data, data, mode="same") / np.correlate(
                np.ones_like(data), data, mode="same")

        time = np.concatenate([energy.simulation_time for energy in energies])

        return time, auto_correlation

    @staticmethod
    def running_average(energies, info_parameter, window_size) -> tuple:
        """
        Calculate the running average of the data with a given window size.
        Centered to the middle of the window.

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
            If the window size is larger than the given data point.

        Examples
        --------
        >>> Statistic.running_average(energies, "ENERGY", 2)
        ([1.5, 2.5, 3.5, 4.5], [10.5, 11.5, 12.5, 13.5])
        """

        data = np.concatenate(
            [energy.data[energy.info[info_parameter]] for energy in energies])

        # Check if data is smaller than window_size
        if len(data) < window_size:
            raise ValueError("Window size is larger than given data point")

        running_average = np.array([
            np.sum(data[i:i + window_size]) / window_size
            for i in range(len(data) - window_size + 1)
        ])

        # Centered to the middle of the window
        time = np.mean(
            [
                np.concatenate([energy.simulation_time
                                for energy in energies])[i:i + window_size]
                for i in range(len(data) - window_size + 1)
            ],
            axis=1,
        )

        return time, running_average
