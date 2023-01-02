from nginxAPI import NginxAPI
from typing import Optional
from copy import deepcopy
from base64 import b64encode, b64decode
from requests import Response
from argparse import ArgumentParser
import sys

def main():
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

    # Delete host parser
    delete_host_parser = subparsers.add_parser("delete-host", help="Removes a host.")
    delete_host_parser.add_argument("filepath", help="The path to an info file.")
    delete_host_parser.add_argument("domain", help="The domain to remove.")

    args = parser.parse_args()

    if args.command == "create-info-file":
        create_info_file(args.filepath, args.host, args.username, args.password)
        print("Success")
    elif args.command == 'create-host':
        domain_names = [domain.strip() for domain in args.domains.split(",")]
        with NginxAPI(*read_info_file(args.filepath)) as nginx:
            template = get_template(nginx, "template")
            if template is None:
                sys.exit(f'Failed to fetch template.')

            response = create_host(nginx, template, domain_names, args.host, int(args.port))

        if response.ok:
            print("Success")
        else:
            sys.exit(f'Failed:\nStatus {response.status_code}\n\n{response.text}\n\n')
    elif args.command == "delete-host":
        with NginxAPI(*read_info_file(args.filepath)) as nginx:
            response = delete_host(nginx, args.domain)

        if response.ok:
            print("Success")
        else:
            sys.exit(f'Failed:\nStatus {response.status_code}\n\n{response.text}\n\n')


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
    proxy_hosts = nginx.get_hosts()
    if proxy_hosts is None: return None

    for proxy_host in proxy_hosts:
        if template_domain in proxy_host['domain_names']:
            template: dict = {}
            wanted_keys = ['domain_names', 'forward_scheme', 'forward_host', 'forward_port', 'certificate_id', 'ssl_forced', 'hsts_enabled', 'hsts_subdomains', 'http2_support',
                            'block_exploits', 'caching_enabled', 'allow_websocket_upgrade', 'access_list_id', 'advanced_config', 'meta', 'locations']

            template['enabled'] = 1
            for key, value in proxy_host.items():
                if key in wanted_keys:
                    template[key] = value
            return template

    return None

def create_host(nginx: NginxAPI, template: dict, domain_names: list, forward_host: str, forward_port: int) -> tuple:
    copy_template = deepcopy(template)
    copy_template['domain_names'] = domain_names
    copy_template['forward_host'] = forward_host
    copy_template['forward_port'] = forward_port
    return nginx.create_host(copy_template)

def delete_host(nginx: NginxAPI, domain: str) -> Response:
    proxy_hosts = nginx.get_hosts()
    if response is None:
        sys.exit(f'Failed to fetch hosts.')
    
    for proxy_host in proxy_hosts:
        if domain in proxy_host['domain_names']:
            if len(proxy_host['domain_names']) == 1:
                # delete entry
                return nginx.delete_host(proxy_host['id'])
            else:
                # update entry
                return nginx.update_host(proxy_host['id'], {'domain_names':proxy_host['domain_names']})
                
    
    sys.exit(f'Failed to find domain "{domain}".')




if __name__ == '__main__':
    main()