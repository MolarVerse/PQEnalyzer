"""
Numeric statistics used by PQEnalyzer plots.

The public energy-based methods are compatibility wrappers for existing call
sites. The ``*_values`` methods contain the actual numeric implementations and
operate only on aligned time/value arrays.
"""

import math

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
    self_correlation_mean(energies, info_parameter)
        Calculate a self-correlation mean for a Reader energy parameter.
    self_correlation_mean_values(time, values)
        Calculate a self-correlation mean for numeric arrays.
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
        ([1, 2, 3, 4, 5], [1, 1.5, 2, 2.5, 3])
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
    def self_correlation_mean(energies, info_parameter) -> tuple:
        """
        Calculate the self-correlation mean of the data.

        Parameters
        ----------
        energies : list
            A list of energy objects.
        info_parameter : str
            The info parameter to calculate the self-correlation mean of.

        Returns
        -------
        tuple
            A tuple containing the time and self-correlation mean.

        Examples
        --------
        >>> Statistic.self_correlation_mean(energies, "ENERGY")
        ([1, 2, 3, 4, 5], [2, 2.5, 3, 3.5, 4])
        """

        energy_series = concatenate_series(energies, info_parameter)
        return Statistic.self_correlation_mean_values(
            energy_series.time, energy_series.values)

    @staticmethod
    def self_correlation_mean_values(time, values) -> tuple:
        """
        Calculate the self-correlation mean for a numeric series.

        The result stays on the original data scale. Each output point is the
        mean of the values that overlap that lag, which avoids the squared
        magnitude returned by an unnormalized product correlation.
        """

        time, data = Statistic.__arrays(time, values)
        data = data.astype(float)

        numerator = np.correlate(data, np.ones_like(data), mode="same")
        overlap = np.correlate(
            np.ones_like(data), np.ones_like(data), mode="same")
        self_correlation_mean = np.divide(
            numerator,
            overlap,
            out=np.zeros_like(data),
            where=overlap != 0,
        )

        return time, self_correlation_mean

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
        inside each window. Linear-time prefix sums replace the naive
        per-window summation; results match windowed means to float
        precision while staying interactive on long trajectories.
        """

        time, data = Statistic.__arrays(time, values)

        if window_size < 1:
            raise ValueError("Window size must be positive")

        # Check if data is smaller than window_size
        if len(data) < window_size:
            raise ValueError("Window size is larger than given data point")

        padded_data = np.cumsum(
            np.concatenate([[0.0], np.asarray(data, dtype=float)]))
        data_sums = padded_data[window_size:] - padded_data[:-window_size]
        running_average = data_sums / window_size

        padded_time = np.cumsum(
            np.concatenate([[0.0], np.asarray(time, dtype=float)]))
        time_sums = padded_time[window_size:] - padded_time[:-window_size]
        time = time_sums / window_size

        return time, running_average

    @staticmethod
    def block_error_values(time, values) -> tuple:
        """
        Estimate the correlated standard error of the mean.

        Naive ``std / sqrt(n)`` underestimates uncertainty for correlated
        simulation data. This implements Flyvbjerg-Petersen blocking
        (J. Chem. Phys. 91, 461, 1989) with Geyer initial-positive-sequence
        truncation (Stat. Sci. 7, 473, 1992): the normalized autocorrelation
        from an FFT is summed over consecutive positive pairs, giving the
        integrated correlation time ``tau`` (in steps), the statistical
        inefficiency ``g`` and the effective sample size ``n / g``.

        Returns
        -------
        tuple
            ``(sem, inefficiency, correlation_time, n_effective)`` with
            ``sem`` the standard error of the mean. All four are ``None``
            when fewer than four finite values are available.
        """

        _, data = Statistic.__arrays(time, values)
        data = np.asarray(data, dtype=float)
        data = data[np.isfinite(data)]
        count = data.size
        if count < 4:
            return None, None, None, None

        std = float(np.std(data))
        if std == 0 or not math.isfinite(std):
            return 0.0, 1.0, 1.0, float(count)

        centered = data - float(np.mean(data))
        size = 1
        while size < 2 * count - 1:
            size *= 2
        spectrum = np.fft.rfft(centered, n=size)
        autocovariance = np.fft.irfft(spectrum * np.conj(spectrum))[:count]
        autocorrelation = autocovariance / autocovariance[0]

        tau = 1.0
        pair = 1
        while 2 * pair < count:
            gamma = (
                float(autocorrelation[2 * pair - 1])
                + float(autocorrelation[2 * pair])
            )
            if not math.isfinite(gamma) or gamma <= 0:
                break
            tau += 2.0 * gamma
            pair += 1

        inefficiency = max(tau, 1.0)
        n_effective = count / inefficiency
        sem = std * math.sqrt(inefficiency / count)
        return sem, inefficiency, tau, n_effective

    @staticmethod
    def mser_truncation_index(values, max_batches=500) -> int | None:
        """
        Locate equilibration with the batched marginal-standard-error rule.

        The series is split into at most ``max_batches`` batches; the
        truncation point minimizing the standard error of the remaining
        batch means marks the end of the initial transient. A constant
        series needs no truncation and returns ``0``.

        Returns
        -------
        int or None
            Index of the first equilibrated point, or ``None`` when fewer
            than four finite values are available.
        """

        data = np.asarray(values, dtype=float)
        data = data[np.isfinite(data)]
        count = data.size
        if count < 4:
            return None
        if float(np.std(data)) == 0:
            return 0

        batches = max(2, min(max_batches, count))
        batch_size = max(1, count // batches)
        usable = (count // batch_size) * batch_size
        means = np.mean(data[:usable].reshape(-1, batch_size), axis=1)
        batches = means.size

        # A one-batch tail always scores zero error; require a tail of at
        # least a tenth of the batches so the minimum cannot sit at the end.
        min_tail = max(2, batches // 10)
        limit = max(0, batches - min_tail)
        best, best_error = 0, math.inf
        for start in range(limit + 1):
            tail = means[start:]
            error = float(np.std(tail)) / math.sqrt(tail.size)
            if error < best_error:
                best, best_error = start, error
        return int(best * batch_size)

    @staticmethod
    def __arrays(time, values) -> tuple:
        """
        Convert inputs to arrays without tying statistics to energy objects.
        """

        return np.asarray(time), np.asarray(values)
