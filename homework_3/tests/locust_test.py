from locust import HttpUser, task, between
from datetime import datetime, timedelta


class ShortLinkUser(HttpUser):
    wait_time = between(1, 5)
    token = None

    def on_start(self):
        """
        Аутентификация при запуске
        """
        response = self.client.post("/auth/jwt/login",
                                    data={"username": "user@test.com", "password": "test"})
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task(5)
    def create_short_link(self):
        """
        Создание короткой ссылки (авторизованный пользователь)
        """
        url = "https://example.com"
        plus_day = (datetime.now() + timedelta(days=1)).isoformat()
        self.client.post("/links/shorten", json={"original_url": url, "expires_at": plus_day},
                         headers={"Authorization": f"Bearer {self.token}"})

    @task(10)
    def redirect_short_link(self):
        """
        Редирект по короткой ссылке
        """
        short_code = self._create_temp_link()
        if short_code:
            self.client.get(f"/links/{short_code}", allow_redirects=False)

    @task(3)
    def get_link_stats(self):
        """
        Получение статистики ссылки
        """
        short_code = self._create_temp_link()
        if short_code:
            self.client.get(f"/links/{short_code}/stats",
                            headers={"Authorization": f"Bearer {self.token}"})

    @task(2)
    def delete_link(self):
        """
        Удаление ссылки
        """
        short_code = self._create_temp_link()
        if short_code:
            self.client.delete(f"/links/{short_code}",
                               headers={"Authorization": f"Bearer {self.token}"})

    @task(2)
    def update_link(self):
        """
        Обновление ссылки
        """
        short_code = self._create_temp_link()
        if short_code:
            plus_2day = (datetime.now() + timedelta(days=2)).isoformat()
            self.client.put(
                f"/links/{short_code}",
                json={"original_url": "https://updated.example.com",
                      "expires_at": plus_2day}, headers={"Authorization": f"Bearer {self.token}"})

    @task(4)
    def search_link(self):
        """
        Поиск ссылки
        """
        url = "https://search.example.com"
        self._create_temp_link(url)
        self.client.get("/links/search/", params={"original_url": url},
                        headers={"Authorization": f"Bearer {self.token}"})

    @task(5)
    def create_public_link(self):
        """
        Создание короткой ссылки (неавторизованный пользователь)
        """
        url = "https://public.example.com"
        plus_day = (datetime.now() + timedelta(days=1)).isoformat()
        self.client.post("/links/public", json={"original_url": url, "expires_at": plus_day})

    @task(2)
    def get_user_links(self):
        """
        Получение всех ссылок пользователя
        """
        self.client.get("/links/user/all", headers={"Authorization": f"Bearer {self.token}"})

    def _create_temp_link(self, url=None):
        """
        Вспомогательная функция для создания тестовой ссылки
        """
        if not url:
            url = "https://temp.example.com"
        plus_day = (datetime.now() + timedelta(days=1)).isoformat()
        response = self.client.post(
            "/links/shorten",
            json={"original_url": url,
                  "expires_at": plus_day},
            headers={"Authorization": f"Bearer {self.token}"})
        return response.json().get("short_code") if response.ok else None
