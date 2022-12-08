from NginxAPI import NginxAPI
from typing import Optional
from copy import deepcopy
from sys import argv, exit
from base64 import b64encode, b64decode

def main():
    nginx = NginxAPI()
    command_list = ["create-info-file", "create-host"]
    check_help(command_list)

    command = argv[1]
    if command == "create-info-file": #create-info-file info-file-path host username password
        create_info_file(argv[2], argv[3], argv[4], argv[5])
    elif command == 'create-host': #create-host info-file-path "domain1, ..." forward-host forward-port
        info_file_path = argv[2]
        domain_names = [domain.strip() for domain in argv[3].split(",")]
        forward_host = argv[4]
        forward_port = int(argv[5])
        nginx.set_target_info(*read_info_file(info_file_path))
        
        with nginx:
            template = get_template(nginx, "template")
            response = create_host(nginx, template, domain_names, forward_host, forward_port)
            if response.ok:
                print("Success")
            else:
                print(f'Failed:\nStatus {response.status_code}\n\n{response.text}\n\n')


def create_info_file(file_path: str, host: str, username: str, password: str):
    with open(file_path, "w") as file:
        host = str(b64encode(host.encode("utf-8")))[2:-1]
        username = str(b64encode(username.encode("utf-8")))[2:-1]
        password= str(b64encode(password.encode("utf-8")))[2:-1]
        file.write(f'{host}\n{username}\n{password}\n')

def read_info_file(file_path: str) -> tuple[str]:
    with open(file_path, "r") as file:
        host = b64decode(file.readline()).decode("utf-8")
        username = b64decode(file.readline()).decode("utf-8")
        password = b64decode(file.readline()).decode("utf-8")
    
    return host, username, password

def check_help(command_list: list[str]):
    help_message = f'Usage: python {argv[0]} {"|".join(command_list)} --help'
    if len(argv) == 1:
        print(help_message)
        exit(1)

    command = argv[1]
    if command not in command_list:
        print(help_message)
        exit(1)
    elif command == "create-host" and ("--help" in argv or len(argv) != 6):
        create_host_help_message = f'Usage: python {argv[0]} create-host info-file-path \"domain1, ...\" forward-host forward-port'
        print(create_host_help_message)
        exit(1)
    elif command == "create-info-file" and ("--help" in argv or len(argv) != 6):
        print(len(argv))
        print(argv)
        create_password_file_help_message = f'Usage python {argv[0]} create-info-file info-file-path host username password'
        print(create_password_file_help_message)
        exit(1)


def get_template(nginx: NginxAPI, template_domain: str) -> Optional[dict]:
    response = nginx.get_hosts()
    template = None
    if response.status_code == 200:
        proxy_hosts = response.json()
        for proxy_host in proxy_hosts:
            if template_domain in proxy_host['domain_names']:
                template = {}
                wanted_keys = ['domain_names', 'forward_scheme', 'forward_host', 'forward_port', 'certificate_id', 'ssl_forced', 'hsts_enabled', 'hsts_subdomains', 'http2_support',
                                'block_exploits', 'caching_enabled', 'allow_websocket_upgrade', 'access_list_id', 'advanced_config', 'enabled', 'meta', 'locations']

                for key, value in proxy_host.items():
                    if key in wanted_keys:
                        template[key] = value
                return template
    return template

def create_host(nginx: NginxAPI, template: dict, domain_names: list, forward_host: str, forward_port: int) -> int:
    copy_template = deepcopy(template)
    copy_template['domain_names'] = domain_names
    copy_template['forward_host'] = forward_host
    copy_template['forward_port'] = forward_port
    response = nginx.create_host(copy_template)
    return response.status_code



if __name__ == '__main__':
    main()