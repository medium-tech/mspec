from pathlib import Path


__all__ = [
    'NoParentDefinedError',
    'apply_template_slots'
]

py_dir = Path(__file__).parent.parent.parent / 'templates' / 'py'
_child_template_path = py_dir / 'src' / 'template_module' / 'multi_model' / '__init__.py'

class NoParentDefinedError(Exception):
    pass

def apply_template_slots(child_path: Path | str=_child_template_path) -> str:
    """Given a child template path, regenerate the child template
    by replacing the slot commands in the parent template with the
    corresponding slot content from the child template.

    args:
        child_path: Path or str - path to the child template file

    returns:
        str - the generated child template content
    """

    #
    # init
    #

    child_template_path = Path(child_path)

    with open(child_template_path) as f:
        child_content = f.readlines()

    #
    # parse child template
    #

    parent_commands = []
    child_template_lines = []
    slots_in_child = []
    all_slot_content = {}
    inside_slot = False
    current_slot_name = None
    parent_line = None

    for line in child_content:
        if line.strip().startswith('# parent ::'):
            if inside_slot:
                raise ValueError(f'parent command not allowed inside slot: {current_slot_name}')
            
            parent_commands.append(line)
            parent_line = line

        elif line.strip().startswith('# slot ::'):
            if inside_slot:
                raise ValueError(f'Nested slots are not supported (slot: {slot_name})')
            
            inside_slot = True

            child_slot_name = line.strip().split('::')[1].strip()
            current_slot_name = child_slot_name
            slots_in_child.append(current_slot_name)
            all_slot_content[current_slot_name] = [line]
        
        elif inside_slot and line.strip().startswith('# end slot'):
            if not inside_slot:
                raise ValueError(f'End slot found without matching start slot (slot: {current_slot_name})')
            all_slot_content[current_slot_name].append(line)
            current_slot_name = None
            inside_slot = False
        
        elif inside_slot:
            all_slot_content[current_slot_name].append(line)

        else:
            child_template_lines.append(line)

    if not parent_commands:
        raise NoParentDefinedError(f'No parent defined in child template: {child_template_path}')

    elif len(parent_commands) > 1:
        raise ValueError('Multiple parent templates found, only one parent template is supported.')
    
    # get parent template path #

    parent_line = parent_commands[0]

    try:
        parent_path_str = parent_line.strip().split('::')[1].strip()
    except IndexError:
        raise ValueError('Invalid parent template command format.')
    
    parent_template = child_template_path.parent / parent_path_str

    with open(parent_template) as f:
        parent_content = f.readlines()

    #
    # generate child template from parent
    #

    output_lines = []
    slots_replaced = []

    for line in parent_content:
        if line.strip().startswith('# slot ::'):
            try:
                slot_name = line.strip().split('::')[1].strip()
            except IndexError:
                raise ValueError('Invalid slot command format.')
            try:
                slot_content = all_slot_content[slot_name]
            except KeyError:
                raise ValueError(f'Slot "{slot_name}" in parent not found in child')
            except TypeError:
                breakpoint()
            output_lines.extend(slot_content)
            slots_replaced.append(slot_name)

        else:
            output_lines.append(line)

    output_lines.append(f'\n{parent_line}')

    if not slots_replaced:
        raise ValueError('No slots were replaced; ensure slot names match between parent and child templates.')

    if sorted(list(set(slots_replaced))) != sorted(slots_in_child):
        slots_not_used = set(slots_in_child) - set(slots_replaced)
        raise ValueError(f'Some slots in child template were not used in parent template: {slots_not_used}')

    return ''.join(output_lines)