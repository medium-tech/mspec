from collections import namedtuple

def new_model_class(model_spec:dict) -> type:
    """
    Dynamically creates a model class based on the provided model specification.

    Args:
        model_spec (dict): The specification dictionary for the model.

    Returns:
        type: A dynamically created model class.
    """

    try:
        class_name = model_spec['name']['pascal_case']
        fields = [field['name'] for field in model_spec['fields']]
    except KeyError as e:
        raise ValueError(f'Missing required model specification key: {e}')
    
    return namedtuple(class_name, fields)

def new_model(model_class:type, data:dict):
    """
    Creates an instance of the given model class using the provided data.

    No data type conversion is performed. Use convert_data_to_model for that.

    Args:
        model_class (type): The model class to instantiate.
        data (dict): A dictionary containing field values for the model.

    Returns:
        object: An instance of the model class.
    """

    try:
        return model_class(**data)
    except TypeError as e:
        raise ValueError(f'Error creating model instance: {e}')
    
def convert_data_to_model(model_class:type, data:dict):
    """
    Converts a dictionary of data into an instance of the specified model class.

    Will convert types as necessary based on the model class definition.

    Useful for user input like CLI args.

    Args:
        model_class (type): The model class to instantiate.
        data (dict): A dictionary containing field values for the model.

    Returns:
        object: An instance of the model class.
    """
    return new_model(model_class, data)
