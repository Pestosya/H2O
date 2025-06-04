import requests
import json


class APISession:
    def __init__(self, base_url, password):
        """
        Инициализация сессии.
        :param base_url: URL вашего сервера.
        :param password: Пароль для авторизации.
        """
        self.base_url = base_url
        self.password = password
        self.session = requests.Session()  # Создаем сессию для повторного использования соединений

    def login(self):
        """
        Выполняет логин на сервере.
        """
        url = f"{self.base_url}/api/session"
        payload = json.dumps({"password": self.password})
        headers = {"Content-Type": "application/json"}

        # Отправляем POST-запрос на авторизацию
        response = self.session.post(url, headers=headers, data=payload)

        if response.status_code == 201:
            print("Успешно залогинился на сервере.")
        else:
            raise Exception(f"Ошибка авторизации: {response.text}")

    def request(self, method, endpoint, **kwargs):
        """
        Выполняет запрос к серверу.
        :param method: HTTP-метод (GET, POST, PUT, DELETE).
        :param endpoint: Конечная точка API (например, api/wapi/wireguard/client/).
        :param kwargs: Дополнительные параметры для запроса (json, data и т.д.).
        :return: Ответ сервера (Response object).
        """
        try:
            # Формируем полный URL
            url = f"{self.base_url}/{endpoint}"

            # Выполняем запрос
            response = self.session.request(method, url, **kwargs)

            # Если требуется авторизация, выполняем логин и повторяем запрос
            if response.status_code == 401:  # Unauthorized
                print("Необходима авторизация. Выполняем логин.")
                self.login()
                response = self.session.request(method, url, **kwargs)

            return response
        except Exception as e:
            raise Exception(f"Ошибка при выполнении запроса: {e}")
