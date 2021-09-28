import requests
import pandas as pd
import numpy as np
from io import StringIO
from datetime import datetime
from dateutil.relativedelta import relativedelta


class KNMI(object):
    def __init__(self, heating_limit, indoor_temp, weather_station):
        self.heating_limit = heating_limit
        self.indoor_temp = indoor_temp
        self.weather_station = weather_station

        data = self.get_degree_days()

        self.last_update = data["last_update"]
        self.total_degree_days_this_year = data["total_degree_days_this_year"]
        self.weighted_degree_days_year = data["weighted_degree_days_year"]

    def get_degree_days(self):
        startdate = datetime.now().strftime("%Y0101")
        enddate = datetime.now().strftime("%Y%m%d")
        stations = [self.weather_station]
        variables = ['TG']
        df = self.get_daily_data_df(startdate, enddate, stations, variables)
    
        df = df.rename(columns={'   TG': 'TG'})
        df['Date'] = pd.to_datetime(df['YYYYMMDD'], format='%Y%m%d')
        year = datetime.strptime(startdate, '%Y%m%d')
    
        conditions = [
            (df['Date'] < year + relativedelta(months=+2)),
            (df['Date'] >= year + relativedelta(months=+2)) & (df['Date'] < year + relativedelta(months=+3)),
            (df['Date'] >= year + relativedelta(months=+3)) & (df['Date'] < year + relativedelta(months=+9)),
            (df['Date'] >= year + relativedelta(months=+9)) & (df['Date'] < year + relativedelta(months=+10)),
            (df['Date'] >= year + relativedelta(months=+10))
        ]
        values = [1.1, 1.0, 0.8, 1.0, 1.1]
        degree_days_conditions = [
            (self.heating_limit - (df['TG'] / 10) <= 0),
            (self.heating_limit - (df['TG'] / 10) > 0)
        ]
        degree_days = [0, self.indoor_temp - (df['TG'] / 10)]
    
    
        df['GD'] = np.select(degree_days_conditions, degree_days)
        df['GGD'] = df.GD * np.select(conditions, values)

        data = {}
        data["last_update"] = df["YYYYMMDD"].iloc[-1]
        data["total_degree_days_this_year"] = df.GD.sum()
        data["weighted_degree_days_year"] = df.GGD.sum()
        return data
    
    
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
