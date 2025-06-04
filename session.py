import requests
import json


class APISession:
    def __init__(self, base_url, password):
        self.base_url = base_url
        self.password = password
        self.session = requests.Session()

    def login(self):
        url = f"{self.base_url}/session"
        payload = json.dumps({"password": self.password})
        headers = {"Content-Type": "application/json"}
        response = self.session.post(url, headers=headers, data=payload)

        # Вывод для отладки
        print("URL:", url)
        print("Headers:", headers)
        print("Payload:", payload)
        print("Response Status Code:", response.status_code)
        print("Response Text:", response.text)

        if response.status_code != 204:
            raise Exception(f"Failed to log in: {response.text}")

    def request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}/{endpoint}"
        response = self.session.request(method, url, **kwargs)

        # Если сессия истекла, логинимся и повторяем запрос
        if response.status_code == 401:  # Unauthorized
            self.login()
            response = self.session.request(method, url, **kwargs)

        return response


# Экземпляр для использования
api_session = APISession(base_url="http://109.71.246.92:51821/api", password="1234")
