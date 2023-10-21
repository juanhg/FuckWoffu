from ISignInManager import ISignInManager
import requests
from datetime import datetime, timedelta


class SignInWoffu(ISignInManager):
    def __init__(self, email, password, company_name):
        self.company_name = company_name
        self.url_path = "https://" + company_name + ".woffu.com/api"
        self.token = self._get_token(email, password)
        self.headers_token = {
            'Authorization': 'Bearer ' + self.token,
            'Content-Type': 'application/json'
        }

    def sign_in(self) -> bool:
        url = self.url_path + "/svc/signs/signs"
        payload = {
            "agreementEventId": None,
            "requestId": None,
            "deviceId": "WebApp",
            "latitude": None,
            "longitude": None,
            "timezoneOffset": -120
        }
        response = requests.post(
            url, json=payload, headers=self.headers_token)
        return response.status_code == 201

    def get_holiday(self):
        return self._get_bank_holiday() + self._get_pto_holiday()

    def _get_bank_holiday(self):
        url = self.url_path + "/users/calendar-events/next"
        response = requests.get(url, headers=self.headers_token)
        holidays_list = []
        if response.status_code == 200:
            holidays_array = response.json()
            for day in holidays_array:
                holidays_list.append(datetime.strptime(
                    day['Date'], '%Y-%m-%dT%H:%M:%S.%f'))
        return holidays_list

    def _get_pto_holiday(self):
        url = self.url_path + "/users/requests/list?pageIndex=0&pageSize=10&statusType=20"
        response = requests.get(url, headers=self.headers_token)
        holidays_list = []
        if response.status_code == 200:
            holidays_array = response.json()
            for day in holidays_array:
                self._calculate_vacation_range(day, holidays_list)
        url = self.url_path + "/users/requests/list?pageIndex=0&pageSize=10&statusType=25"
        response = requests.get(url, headers=self.headers_token)
        if response.status_code == 200:
            holidays_array = response.json()
            for day in holidays_array:
                self._calculate_vacation_range(day, holidays_list)
        return holidays_list

    def _calculate_vacation_range(self, day, holidays_list):
        requested_days = int(day['RequestedFormatted']['Values'][0])
        first_day = datetime.strptime(
            day['StartDate'], '%Y-%m-%dT%H:%M:%S.%f')
        if requested_days == 1:
            holidays_list.append(first_day)
            return

        # Detect vacation range:
        last_day = datetime.strptime(
            day['EndDate'], '%Y-%m-%dT%H:%M:%S.%f')
        time_difference = (last_day - first_day).days + 1
        for d in range(time_difference):
            annother_day = first_day + timedelta(days=d)
            holidays_list.append(annother_day)

    def _get_token(self, email, password):
        url = "https://" + self.company_name + ".woffu.com/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "password",
            "username": email,
            "password": password
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            return '¯\(ツ)/¯'
