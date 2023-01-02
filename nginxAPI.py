from typing import Optional
from requests import Session, Response

class NginxAPI:
    def __init__(self, host: str=None, username: str=None, password: str=None):
        self._host = host
        self._session = None
        self.__token = None
        self.__username = username
        self.__password = password

    def set_target_info(self, host: str, username: str, password: str):
        self._host = host
        self.__username = username
        self.__password = password

    def start_session(self):
        if self._session is None:
            self._session = Session()
            self.__token = self.__get_token()
            

    def end_session(self):
        if self._session is not None:
            self._session.close()
            self._session = None

    def __get_token(self) -> str:
        response = self._session.post(f'{self._host}/api/tokens', json={"identity":self.__username, "secret":self.__password})

        if response.status_code == 200:
            return response.json()['token']
        
        raise AuthException(response.text)

    def get_hosts(self) -> Optional[list[dict]]:
        response = self._session.get(f'{self._host}/api/nginx/proxy-hosts', headers = self.__get_auth_header())
        if response.status_code != 200:
            return None
        
        return response.json()
    
    def create_host(self, proxy_properties: dict) -> Response:
        response = self._session.post(f'{self._host}/api/nginx/proxy-hosts', headers=self.__get_auth_header(), json=proxy_properties)
        return response

    def remove_host(self, id: str):
        response = self._session.delete(f'{self._host}/api/nginx/proxy-hosts/{id}', headers=self.__get_auth_header())
        return response

    def update_host(self, id: str, proxy_properties: dict):
        response = self._session.put(f'{self._host}/api/nginx/proxy-hosts/{id}', headers=self.__get_auth_header(), json=proxy_properties)
        return response

    def __get_auth_header(self) -> dict:
        return {'Authorization':f'Bearer {self.__token}'}

    def __enter__(self):
        self.start_session()
        return self

    def __exit__(self, *args):
        self.end_session()