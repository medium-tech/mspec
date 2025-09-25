"""
# vars :: {"template app": "project.name.lower_case"}

template app
# for :: {% for module in modules.values() %} :: { "template module": "module.name.lower_case" }
    template module
    # for :: {% for model in module.models.values() %} :: { "single model": "model.name.lower_case" }
        single model
            # if :: model.auth.require_login is true
            auth: true
                # if :: not model.auth.max_models_per_user is none
                max models: {{ model.auth.max_models_per_user }}
                # end if ::
            # end if ::
    # end for ::
# end for ::

"""
