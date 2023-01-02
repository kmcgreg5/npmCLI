from nginxAPI import NginxAPI
from typing import Optional
from copy import deepcopy
from base64 import b64encode, b64decode
from requests import Response
from argparse import ArgumentParser

def main():
    nginx = NginxAPI()
    
    parser = ArgumentParser(prog="Nginx Proxy Manager CLI")
    subparsers = parser.add_subparsers(help="The supported commands.", dest="command")

    # Create info file parser
    create_info_file_parser = subparsers.add_parser("create-info-file", help="Create an info file for subsequent usage.")
    create_info_file_parser.add_argument("filepath", help="The info file path to create.")
    create_info_file_parser.add_argument("host", help="The NginxProxyManager instance url.")
    create_info_file_parser.add_argument("username", help="The username for the NginxProxyManager instance.")
    create_info_file_parser.add_argument("password", help="The password for the NginxProxyManager instance.")

    # Create host parser
    create_host_parser = subparsers.add_parser("create-host", help="Creates a host from a template.")
    create_host_parser.add_argument("filepath", help="The path to an info file.")
    create_host_parser.add_argument("domains", help="A single domain or comma seperated list of domains to forward.")
    create_host_parser.add_argument("host", help="The host to forward to.")
    create_host_parser.add_argument("port", help="The port to forward to.")

    args = parser.parse_args()

    if args.command == "create-info-file": #create-info-file info-file-path host username password
        create_info_file(args.filepath, args.host, args.username, args.password)
        print("Success")
    elif args.command == 'create-host': #create-host info-file-path "domain1, ..." forward-host forward-port
        domain_names = [domain.strip() for domain in args.domains.split(",")]
        nginx.set_target_info(*read_info_file(args.filepath))
        
        with nginx:
            template = get_template(nginx, "template")
            response = create_host(nginx, template, domain_names, args.host, int(args.port))
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


def get_template(nginx: NginxAPI, template_domain: str) -> Optional[dict]:
    response = nginx.get_hosts()
    template = None
    if response.status_code == 200:
        proxy_hosts = response.json()
        for proxy_host in proxy_hosts:
            if template_domain in proxy_host['domain_names']:
                template = {}
                wanted_keys = ['domain_names', 'forward_scheme', 'forward_host', 'forward_port', 'certificate_id', 'ssl_forced', 'hsts_enabled', 'hsts_subdomains', 'http2_support',
                                'block_exploits', 'caching_enabled', 'allow_websocket_upgrade', 'access_list_id', 'advanced_config', 'meta', 'locations']

                template['enabled'] = 1
                for key, value in proxy_host.items():
                    if key in wanted_keys:
                        template[key] = value
                return template
    return template

def create_host(nginx: NginxAPI, template: dict, domain_names: list, forward_host: str, forward_port: int) -> Response:
    copy_template = deepcopy(template)
    copy_template['domain_names'] = domain_names
    copy_template['forward_host'] = forward_host
    copy_template['forward_port'] = forward_port
    response = nginx.create_host(copy_template)
    return response



if __name__ == '__main__':
    main()