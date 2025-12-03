from mapp.context import OpRouteContext


def create_op_routes(module_spec:dict, op_spec:dict) -> tuple[callable, type]:
    op_kebab_case = op_spec['name']['kebab_case']
    module_kebab_case = module_spec['name']['kebab_case']

    op_ctx = OpRouteContext(
        op_kebab_case=op_kebab_case,
        module_kebab_case=module_kebab_case,
        api_op_regex=rf'/api/{module_kebab_case}/ops/{op_kebab_case}'
    )

def op_routes():
    pass
