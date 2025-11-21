def add_model_subparser(subparsers, model_spec):
    model_kebab_case = model_spec['name']['kebab_case']
    model_parser = subparsers.add_parser(model_kebab_case, help=f'Model: {model_kebab_case}')
    
    action_subparsers = model_parser.add_subparsers(dest='action', required=True)
    for action in ['help', 'create', 'read', 'update', 'delete', 'list']:
        action_parser = action_subparsers.add_parser(action, help=f'Action: {action}')
        action_parser.set_defaults(func=placeholder_action)

def placeholder_action(args):
    print(f'[PLACEHOLDER] Would run {args.action} for model {args.model} in module {args.module}')
