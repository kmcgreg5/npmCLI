from requests import Session

class APIException(Exception):
    pass


class NpmAPI:
    DEFAULT_PORT: int = 8181
    def __init__(self, host: str=None, port: int=DEFAULT_PORT, username: str=None, password: str=None):
        self._host = host
        self._port = port
        self._session = None
        self.__token = None
        self.__username = username
        self.__password = password

    def set_target_info(self, host: str, username: str, password: str):
        self._host = host
        self.__username = username
        self.__password = password
    
    def set_tartget_info(self, host: str, port: int, username: str, password: str):
        self.set_target_info(host, username, password)
        self._port = port
    
    def __validate_response(self, response, *args):
        if response.status_code != 200 and response.status_code != 201:
            raise APIException(response.text)
        
        #if len(args) == 0:
        #    return
        
        return_value = response.json()
        for arg in args:
            return_value = return_value[arg]
        
        return return_value

    def __get_host(self) -> str:
        return f'http://{self._host}:{self._port}'

    def __get_url(self, endPoint) -> str:
        return f'{self.__get_host()}{endPoint}'

    def start_session(self):
        if self._session is None:
            self._session = Session()
            self.__token = self.__get_token()
            

    def end_session(self):
        if self._session is not None:
            self._session.close()
            self._session = None

    def __get_token(self) -> str:
        endPoint = '/api/tokens/'
        response = self._session.post(self.__get_url(endPoint), json={"identity":self.__username, "secret":self.__password})
        return self.__validate_response(response, 'token')

    def get_hosts(self) -> list:
        endPoint = '/api/nginx/proxy-hosts/'
        response = self._session.get(self.__get_url(endPoint), headers = self.__get_auth_header())
        return self.__validate_response(response)
    
    def create_host(self, proxy_properties: dict):
        endPoint = '/api/nginx/proxy-hosts/'
        response = self._session.post(self.__get_url(endPoint), headers=self.__get_auth_header(), json=proxy_properties)
        self.__validate_response(response)

    '''
    def remove_host(self, id: str):
        response = self._session.delete(f'{self._host}/api/nginx/proxy-hosts/{id}/', headers=self.__get_auth_header())
        return response

    def update_host(self, id: str, proxy_properties: dict):
        response = self._session.put(f'{self._host}/api/nginx/proxy-hosts/{id}', headers=self.__get_auth_header(), json=proxy_properties)
        return response
    '''

    def __get_auth_header(self) -> dict:
        return {'Authorization':f'Bearer {self.__token}'}

    def __enter__(self):
        self.start_session()
        return self

    def __exit__(self, *args):
        self.end_session()