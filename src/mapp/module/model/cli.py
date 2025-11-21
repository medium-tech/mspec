def add_model_subparser(subparsers, model_name, model_spec):
    model_parser = subparsers.add_parser(model_name, help=f"Model: {model_name}")
    # Add actions (help, create, read, update, delete, list, etc.)
    action_subparsers = model_parser.add_subparsers(dest="action", required=True)
    for action in ["help", "create", "read", "update", "delete", "list"]:
        action_parser = action_subparsers.add_parser(action, help=f"Action: {action}")
        action_parser.set_defaults(func=placeholder_action)

def placeholder_action(args):
    print(f"[PLACEHOLDER] Would run {args.action} for model {args.model} in module {args.module}")
