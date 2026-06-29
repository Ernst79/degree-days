"""Module to calculate the (weighted) degree days from KNMI data"""
from datetime import datetime
from io import StringIO
import logging

import pandas as pd
import requests

from ..const import STATION_MAPPING, WEIGHT_FACTOR

_LOGGER = logging.getLogger(__name__)
REFERENCE_FALLBACK_STATION = "De Bilt"


class KNMI:
    """KMNI data"""

    def __init__(self, startdate, station, T_indoor, T_heatinglimit, total_consumption, dhw_consumption, heatpump):
        self.startdate = startdate
        self.station = station
        self.T_indoor = T_indoor
        self.T_heatinglimit = T_heatinglimit
        self.total_consumption = total_consumption
        self.dhw_consumption_per_day = dhw_consumption * 12 / 365
        self.heatpump = heatpump
        data = self.get_degree_days()

        self.last_update = data["last_update"]
        self.total_degree_days_this_year = data["total_degree_days_this_year"]
        self.weighted_degree_days_year = data["weighted_degree_days_year"]
        if self.heatpump:
            self.energy_consumption_per_weighted_degree_day = data["consumption_per_weighted_degree_day"]
            self.energy_consumption_prognose_total = data["consumption_prognose_total"]
            self.energy_consumption_prognose_heating = data["consumption_prognose_heating"]
        else:
            self.gas_per_weighted_degree_day = data["consumption_per_weighted_degree_day"]
            self.gas_prognose_total = data["consumption_prognose_total"]
            self.gas_prognose_heating = data["consumption_prognose_heating"]

    def get_degree_days(self):
        """Calculate degree days."""
        enddate = datetime.now().strftime("%Y%m%d")

        startdate = datetime.strptime(self.startdate, "%Y%m%d")
        year = startdate.year
        startdate_offset_year = startdate.replace(year=year - 1)
        variables = ["TG"]
        history_startdate = self.startdate.replace(str(year), str(int(year) - 20), 1)
        df = self._get_station_df(self.station, history_startdate, enddate, variables)

        if df.empty:
            if self.station == REFERENCE_FALLBACK_STATION:
                return self._empty_data()
            _LOGGER.warning(
                "KNMI station %s returned no usable data for %s through %s. "
                "Falling back to %s for all degree day calculations.",
                self.station,
                history_startdate,
                enddate,
                REFERENCE_FALLBACK_STATION,
            )
            df = self._get_station_df(
                REFERENCE_FALLBACK_STATION,
                history_startdate,
                enddate,
                variables,
            )
            if df.empty:
                return self._empty_data()

        # add day, month and year number
        df["day"] = df["Date"].dt.dayofyear
        df["month"] = df["Date"].dt.month
        df["year"] = df["Date"].dt.year

        reference_station = self._get_reference_station_name(df, startdate_offset_year, startdate)
        reference_df = (
            df
            if reference_station == self.station
            else self._get_station_df(reference_station, history_startdate, enddate, variables)
        )
        if reference_df.empty:
            _LOGGER.warning(
                "Reference station %s returned no usable data. Falling back to %s averages for prognosis.",
                reference_station,
                self.station,
            )
            reference_df = df

        # add weight factor based on month
        df["WF"] = df["month"].map(lambda value: WEIGHT_FACTOR[value])

        # Calculate degree days
        df["DD"] = df.apply(lambda x: self.calculate_DD(x.TG, 1.0), axis=1)
        # Calculate weighted degree days
        df["WDD"] = df.apply(lambda x: self.calculate_DD(x.TG, x.WF), axis=1)

        # calculate degree year
        DD = df[df.year == year].DD.sum()

        # calculate weighted degree year
        WDD = df[df["Date"] >= startdate].WDD.sum()
        reference_tg_by_day = reference_df.groupby("day")["TG"].mean().to_dict()
        last_update_dt = df["Date"].max().to_pydatetime()
        WDD_average_total = self._sum_average_wdd_for_period(
            reference_tg_by_day,
            startdate_offset_year,
            startdate,
        )
        WDD_average_cum = self._sum_average_wdd_for_period(
            reference_tg_by_day,
            startdate,
            last_update_dt,
        )

        data = {}

        data["last_update"] = df["YYYYMMDD"].iloc[-1]
        data["total_degree_days_this_year"] = DD
        data["weighted_degree_days_year"] = WDD
        last_update = str(df["YYYYMMDD"].iloc[-1])
        number_of_days_consumption = (datetime.strptime(enddate, "%Y%m%d") - startdate).days

        # calculate prognose
        if self.total_consumption and number_of_days_consumption > 0 and WDD > 0:
            # estimate consumption at the end of KNMI data
            number_of_days_knmi = (
                datetime.strptime(last_update, "%Y%m%d") - startdate
            ).days

            dhw_consumption_other = self.dhw_consumption_per_day * number_of_days_consumption
            consumption_heating = (
                (self.total_consumption - dhw_consumption_other)
                * number_of_days_knmi
                / number_of_days_consumption
            )

            consumption_prognose_heating = round(
                consumption_heating
                / WDD
                * (WDD + (WDD_average_total - WDD_average_cum)),
                1,
            )
            consumption_prognose_total = round(
                consumption_prognose_heating + self.dhw_consumption_per_day * 365,
                1,
            )
            consumption_per_weighted_degree_day = round(consumption_heating / WDD, 3)

            data["consumption_per_weighted_degree_day"] = consumption_per_weighted_degree_day
            data["consumption_prognose_heating"] = consumption_prognose_heating
            data["consumption_prognose_total"] = consumption_prognose_total
        else:
            data["consumption_per_weighted_degree_day"] = None
            data["consumption_prognose_heating"] = None
            data["consumption_prognose_total"] = None
        return data

    def _get_reference_station_name(self, df, startdate_offset_year, startdate):
        """Pick a station with enough history to build prognosis reference averages."""
        reference_period = df[df["Date"].between(startdate_offset_year, startdate)]
        expected_days = (startdate - startdate_offset_year).days + 1
        available_days = reference_period["Date"].nunique()
        minimum_days = min(expected_days, 300)

        if available_days >= minimum_days:
            return self.station

        _LOGGER.warning(
            "KNMI station %s has only %s historical day(s) for the prognosis "
            "reference period %s through %s. Falling back to %s for reference averages.",
            self.station,
            available_days,
            startdate_offset_year.strftime("%Y-%m-%d"),
            startdate.strftime("%Y-%m-%d"),
            REFERENCE_FALLBACK_STATION,
        )
        return REFERENCE_FALLBACK_STATION

    def _get_station_df(self, station_name, startdate, enddate, variables):
        """Load and normalize KNMI day data for one station."""
        station_code = STATION_MAPPING[station_name]
        df = self.get_daily_data_df(startdate, enddate, [station_code], variables)
        if df.empty:
            return pd.DataFrame()

        df.columns = df.columns.str.strip()
        if not {"YYYYMMDD", "TG"}.issubset(df.columns):
            return pd.DataFrame()

        df["Date"] = pd.to_datetime(df["YYYYMMDD"], format="%Y%m%d", errors="coerce")
        df["TG"] = pd.to_numeric(df["TG"], errors="coerce", downcast="float")
        df = df.dropna(subset=["Date", "TG"]).copy()
        if df.empty:
            return pd.DataFrame()

        df["day"] = df["Date"].dt.dayofyear
        return df

    def _sum_average_wdd_for_period(self, reference_tg_by_day, startdate, enddate):
        """Sum average weighted degree days over a full calendar period."""
        if enddate < startdate:
            return 0

        total = 0
        for current_date in pd.date_range(start=startdate, end=enddate, freq="D"):
            tg_average = reference_tg_by_day.get(current_date.dayofyear)
            if tg_average is None:
                continue
            total += self.calculate_DD(
                tg_average,
                WEIGHT_FACTOR[current_date.month],
            )
        return total

    def calculate_DD(self, TG, WF):
        """Calculate Weighted Degree Days"""
        if self.T_heatinglimit - TG/10 <= 0:
            return 0
        else:
            return (max(self.T_indoor - TG / 10, 0) * WF)

    def _empty_data(self):
        """Return an unavailable dataset when KNMI has no usable rows."""
        return {
            "last_update": None,
            "total_degree_days_this_year": None,
            "weighted_degree_days_year": None,
            "consumption_per_weighted_degree_day": None,
            "consumption_prognose_heating": None,
            "consumption_prognose_total": None,
        }

    def get_daily_data_df(self, startdate, enddate, stations, variables):
        """Request and parse data from knmi api.

        Parameters
        ----------
        start : str
            Startdate in string format, eg '20210101'
        end : str
            Enddate in string format, eg '20210101'
        stations : [int], optional
            List of station numbers in int format, by default None
        variables : [str], optional
            List of variables in str format, if None is given, all are returned by the api

        Returns
        -------
        DataFrame
            Containing data returned by knmi api
        """
        r = self.get_daily_data_raw(startdate, enddate, stations, variables)
        df = self.parse_result_to_df(r)
        return df

    def get_daily_data_raw(self, start, end, stations=None, variables=None):
        """Get raw data from knmi api.

        See: https://www.knmi.nl/kennis-en-datacentrum/achtergrond/data-ophalen-vanuit-een-script
        Parameters
        ----------
        start : str
            Startdate in string format, eg '20210101'
        end : str
            Enddate in string format, eg '20210101'
        stations : [int], optional
            List of station numbers in int format, by default None
        variables : [str], optional
            List of variables in str format, if None is given, all are returned by the api

        Returns
        -------
        str
            Containing data returned by knmi api
        """
        url = 'https://www.daggegevens.knmi.nl/klimatologie/daggegevens'
        params = 'start=' + start
        params = params + '&end=' + end
        params = self.add_list_items_to_params(params, 'stns', stations)
        params = self.add_list_items_to_params(params, 'vars', variables)
        r = requests.post(url=url, data=params, timeout=30)
        r.raise_for_status()
        return r.text

    def add_list_items_to_params(self, params, name, variables):
        """Add every variable in var_list to the parameter string.

        Parameters
        ----------
        params : str
            String containing the request parameters
        name : str
            Name of the variable, specified by knmi api
        variables : list
            Containing items to be added to params

        Returns
        -------
        str
            Appended string of request parameters
        """
        if variables is not None:
            vars_parsed = str(variables[0])
            if len(variables) != 1:
                for var in variables[1:]:
                    vars_parsed = vars_parsed + ':' + str(var)
            params = params + '&' + name + '=' + vars_parsed
        return params

    def parse_result_to_df(self, response_text):
        """Parse result of function get_daily_data_raw

        Parameters
        ----------
        response_text : str
            Containing data returned by knmi api

        Returns
        -------
        DataFrame
            Containing data returned by knmi api
        """
        header_line = None
        data_lines = []

        for raw_line in response_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("#"):
                candidate = line.lstrip("#").strip()
                if "," in candidate:
                    header_line = candidate
                continue

            data_lines.append(line)

        if header_line is None:
            return pd.DataFrame()

        csv_text = "\n".join([header_line, *data_lines])
        return pd.read_csv(StringIO(csv_text), skipinitialspace=True)
