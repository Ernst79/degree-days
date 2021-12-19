import requests
import pandas as pd
from io import StringIO
from datetime import datetime
import logging

from ..const import STATION_MAPPING, WEIGHT_FACTOR


class KNMI(object):
    def __init__(self, startdate, station, T_indoor, T_heatinglimit, gas_usage, gas_other):
        self.startdate = startdate
        self.station = station
        self.T_indoor = T_indoor
        self.T_heatinglimit = T_heatinglimit
        self.gas_usage = gas_usage
        self.gas_other_per_day = gas_other * 12 / 365
        data = self.get_degree_days()

        self.last_update = data["last_update"]
        self.total_degree_days_this_year = data["total_degree_days_this_year"]
        self.weighted_degree_days_year = data["weighted_degree_days_year"]
        if self.gas_usage:
            self.gas_per_weighted_degree_day = data["gas_per_weighted_degree_day"]
            self.gas_prognose = data["gas_prognose"]
        else:
            self.gas_per_weighted_degree_day = "Unavailable"
            self.gas_prognose = "Unavailable"

    def get_degree_days(self):
        enddate = datetime.now().strftime("%Y%m%d")

        station_code = STATION_MAPPING[self.station]
        year = datetime.strptime(self.startdate, '%Y%m%d').year
        variables = ['TG']
        df = self.get_daily_data_df("20000101", enddate, [station_code], variables)
    
        df = df.rename(columns={'   TG': 'TG'})
        df['Date'] = pd.to_datetime(df['YYYYMMDD'], format='%Y%m%d')
        df["TG"] = pd.to_numeric(df["TG"], errors='coerce', downcast="float")
    
        # add day, month and year number
        df['day'] = df['Date'].dt.dayofyear
        df['month'] = df['Date'].dt.month
        df['year'] = df['Date'].dt.year
    
        # calculate mean of every yearday in range
        df_average = df.groupby('day')['TG'].mean().reset_index(name="TG_average")
        df = pd.merge(df, df_average, on=['day'], how='left')
    
        # add weight factor based on month
        df['WF'] = df['month'].map(lambda value: WEIGHT_FACTOR[value])

        # Calculate degree days
        df["DD"] = df.apply(lambda x: self.calculate_DD(x.TG, 1.0), axis=1)
        # Calculate weighted degree days
        df["WDD"] = df.apply(lambda x: self.calculate_DD(x.TG, x.WF), axis=1)
        # Calculate 20 year average weighted degree days
        df["WDD_average"] = df.apply(lambda x: self.calculate_DD(x.TG_average, x.WF), axis=1)

        # calculate degree year
        DD = df[df.year == year].DD.sum()

        # calculate weighted degree year
        WDD = df[df.year == year].WDD.sum()
        WDD_average_total = df[df.year == year-1].WDD_average.sum()
        WDD_average_cum = df[df.year == year].WDD_average.sum()
    
        data = {}
        
        data["last_update"] = df["YYYYMMDD"].iloc[-1]
        data["total_degree_days_this_year"] = DD
        data["weighted_degree_days_year"] = WDD
        last_update = str(df["YYYYMMDD"].iloc[-1])

        # calculate gas prognose
        if self.gas_usage:
            # estimate gas consumption at the end of KNMI data
            number_of_days_gas = (datetime.strptime(enddate, '%Y%m%d') - datetime.strptime(self.startdate, '%Y%m%d')).days
            number_of_days_knmi = (datetime.strptime(last_update, '%Y%m%d') - datetime.strptime(self.startdate, '%Y%m%d')).days

            gas_use_other = self.gas_other_per_day * number_of_days_gas
            gas_consumption_total = self.gas_usage * number_of_days_knmi / number_of_days_gas
            gas_consumption_heating = (self.gas_usage - gas_use_other) * number_of_days_knmi / number_of_days_gas

            gas_prognose = round(gas_consumption_total / WDD * (WDD + (WDD_average_total - WDD_average_cum)), 1)
            gas_per_weighted_degree_day = round(gas_consumption_heating / WDD, 3)

            data["gas_per_weighted_degree_day"] = gas_per_weighted_degree_day
            data["gas_prognose"] = gas_prognose

        return data

    def calculate_DD(self, TG, WF):
        """Calculate Weighted Degree Days"""
        if self.T_heatinglimit - TG/10 <= 0:
            return 0
        else:
            return(max(self.T_indoor - TG/10 , 0) * WF)

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
        r = requests.post(url=url, data=params)
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
        # Count and drop the # lines, except last containing column names
        count = 0
        for i in range(0, len(response_text)):
            if (response_text[i] == '#'):
                count = count + 1
        r = response_text.split("\n", count - 1)[count - 1]
        # drop '# '
        r = r[2:]
        df = pd.read_csv(StringIO(r))
        return df
