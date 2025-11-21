def add_model_subparser(subparsers, model_spec):
    model_kebab_case = model_spec['name']['kebab_case']
    model_parser = subparsers.add_parser(model_kebab_case, help=f'Model: {model_kebab_case}')

    model_subparsers = model_parser.add_subparsers(dest='action', required=True)

    help_parser = model_subparsers.add_parser('help', help='Show help for this model', aliases=['-h', '--help'])
    help_parser.set_defaults(func=lambda args: model_parser.print_help())
    
    for action in ['create', 'read', 'update', 'delete', 'list']:
        action_parser = model_subparsers.add_parser(action, help=f'Action: {action}')
        action_parser.set_defaults(func=placeholder_action)

def placeholder_action(args):
    print(f'[PLACEHOLDER] Would run {args.action} for model {args.model} in module {args.module}')
