from npmAPI import NpmAPI
from argparse import ArgumentParser
import sys

class CLIException(Exception):
    pass

def main(args: list=sys.argv[1:]):
    parser = ArgumentParser(prog="Nginx Proxy Manager CLI")
    parser.add_argument("--host", help="The NPM Server host.", nargs='?')
    parser.add_argument("--username", help="The NPM Server username.", nargs='?')
    parser.add_argument("--password", help="The NPM Server password.", nargs='?')
    parser.add_argument("--port", help="The port to connect to.", nargs='?', type=int, default=NpmAPI.DEFAULT_PORT)

    items = parser.add_subparsers(help="The items to operate on.", dest="item")

    # Host parser
    host_parser = items.add_parser("host")
    operations = host_parser.add_subparsers(help="The operation to perform.", dest='operation')
    # Create Host parser
    host_create_parser = operations.add_parser("create")
    host_create_parser.add_argument('forwardHost', help="The host to forward to.")
    host_create_parser.add_argument('forwardPort', help="The port to forward to.")
    host_create_parser.add_argument('domains', help='The domains to forwards.', nargs='+')
    host_create_parser.add_argument('--template', help='The template\'s domain name.', nargs='?', default='template')

    '''
    # Delete host parser
    remove_host_parser = subparsers.add_parser("remove-host", help="Removes a host.")
    remove_host_parser.add_argument("filepath", help="The path to an info file.")
    remove_host_parser.add_argument("domain", help="The domain to remove.")

    # Update from search
    update_hosts_parser = subparsers.add_parser("update-hosts", help="Updates a host from a template and search template.")
    update_hosts_parser.add_argument("filepath", help="The path to an info file.")
    field_choices = ['domain_names', 'forward_scheme', 'forward_host', 'forward_port', 'certificate_id', 'ssl_forced', 'hsts_enabled', 'hsts_subdomains', 'http2_support',
                            'block_exploits', 'caching_enabled', 'allow_websocket_upgrade', 'access_list_id', 'advanced_config', 'meta', 'locations', 'enabled']
    update_hosts_parser.add_argument("field", choices=field_choices[:-1], help="The field to update.")
    update_hosts_parser.add_argument("--searchfield", default=["advanced_config"], choices=field_choices, nargs='+', help="The field to match.")
    '''
    args = parser.parse_args(args)

    if args.item == 'host':
        if args.operation == 'create':
            __validate_options(args)
            __create_host(args)
        else:
            host_parser.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)
    
    print("Success")

    '''
    elif args.command == "remove-host":
        with NginxAPI(*read_info_file(args.filepath)) as nginx:
            response = remove_host(nginx, args.domain)

        if not response.ok:
            sys.exit(f'Failed:\nStatus {response.status_code}\n\n{response.text}\n\n')
    elif args.command == "update-hosts":
        with NginxAPI(*read_info_file(args.filepath)) as nginx:
            update_template: Optional[dict] = get_template(nginx, "updatetemplate")
            if update_template is None:
                sys.exit("Failed to fetch updatetemplate.")
            
            search_template: Optional[dict] = get_template(nginx, "searchtemplate")
            if search_template is None:
                sys.exit("Failed to fetch searchtemplate.")
            
            hosts = nginx.get_hosts()
            if hosts is None:
                sys.exit("Failed to fetch hosts.")

            update_dict: dict={args.field:update_template[args.field]}
            for host in hosts:
                for field in args.searchfield:
                    if host[field] != search_template[field]:
                        break
                else:
                    response = nginx.update_host(host['id'], update_dict)
                    if not response.ok:
                        print(response.text)
                        sys.exit(f'Failed to update host: {host["domain_names"]}')
                    print(f'Updated host: {host["domain_names"]}')
    else:
        parser.print_help()
        sys.exit(1)
    '''


def __validate_options(args):
    def throwRequiredOptionException(option: str):
        parsed_option = option
        while parsed_option.startswith('-'):
            parsed_option = parsed_option[1:]

        value = getattr(args, parsed_option)
        if value is None:
            raise CLIException(f'The option \'{option}\' is undefined.')

    throwRequiredOptionException("--host")
    throwRequiredOptionException("--username")
    throwRequiredOptionException("--password")
    throwRequiredOptionException("--port")


def __get_template(nginx: NpmAPI, template_domain: str) -> dict:
    proxy_hosts = nginx.get_hosts()

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

    raise CLIException(f'Could not find a template for the domain \'{template_domain}\'.')


def __create_host(args):
    with NpmAPI(args.host, args.port, args.username, args.password) as server:
        print(args.domains)
        template = __get_template(server, args.template)
        template['domain_names'] = args.domains
        template['forward_host'] = args.forwardHost
        template['forward_port'] = args.forwardPort

        existing_domains = []
        for host in server.get_hosts():
            for domain in args.domains:
                if domain in host['domain_names'] and domain not in existing_domains:
                    existing_domains.append(domain)
        
        if len(existing_domains) != 0:
            raise CLIException(f'The following domains already have an entry on this server: {existing_domains}')

        server.create_host(template)


'''
def remove_host(nginx: NginxAPI, domain: str) -> Response:
    proxy_hosts = nginx.get_hosts()
    if proxy_hosts is None:
        sys.exit(f'Failed to fetch hosts.')
    
    for proxy_host in proxy_hosts:
        if domain in proxy_host['domain_names']:
            if len(proxy_host['domain_names']) == 1:
                # remove entry
                return nginx.remove_host(proxy_host['id'])
            else:
                # update entry
                proxy_host['domain_names'].remove(domain)
                return nginx.update_host(proxy_host['id'], {'domain_names':proxy_host['domain_names']})
    
    sys.exit(f'Failed to find domain "{domain}".')
'''

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'Exception occurred: {str(e)}')
        sys.exit(1)