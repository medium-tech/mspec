from pathlib import Path


__all__ = [
    'apply_template_slots'
]

def _get_child_slot_content(template_lines, slot_name):
    slot_content = []
    inside_slot = False
    for line in template_lines:
        if line.strip() == f'# slot :: {slot_name}':
            if inside_slot:
                raise ValueError(f'Nested slots are not supported (slot: {slot_name})')
            inside_slot = True

        elif inside_slot and line.strip().startswith('# end slot'):
            if not inside_slot:
                raise ValueError(f'End slot found without matching start slot (slot: {slot_name})')
            inside_slot = False

        elif inside_slot:
            slot_content.append(line)

    return slot_content

def apply_template_slots() -> str:
    py_dir = Path(__file__).parent.parent.parent / 'templates' / 'py'
    child_template_path = py_dir / 'src' / 'template_module' / 'multi_model' / '__init__.py'

    with open(child_template_path) as f:
        child_content = f.readlines()

    # search for parent template command #

    parent_slots = []
    parent_slot_count = 0
    template_lines = []

    for line in child_content:
        if line.strip().startswith('# parent ::'):
            parent_slots.append(line)
            parent_slot_count += 1
        else:
            template_lines.append(line)

    if parent_slot_count == 0:
        raise ValueError(f'No parent defined in child template: {child_template_path}')
    
    elif parent_slot_count > 1:
        raise ValueError('Multiple parent templates found, only one parent template is supported.')
    
    # get parent template path #

    parent_line = parent_slots[0]

    try:
        parent_path_str = parent_line.strip().split('::')[1].strip()
    except IndexError:
        raise ValueError('Invalid parent template command format.')
    
    parent_template = child_template_path.parent / parent_path_str

    with open(parent_template) as f:
        parent_content = f.readlines()

    # apply slots #

    output_lines = []
    replacements = 0

    for line in parent_content:
        if line.strip().startswith('# slot ::'):
            try:
                slot_name = line.strip().split('::')[1].strip()
            except IndexError:
                raise ValueError('Invalid slot command format.')

            slot_content = _get_child_slot_content(template_lines, slot_name)
            output_lines.extend(slot_content)
            replacements += 1

        else:
            output_lines.append(line)
    
    if replacements == 0:
        raise ValueError('No slots were replaced; ensure slot names match between parent and child templates.')

    return ''.join(output_lines)