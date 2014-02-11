Stackdriver API Client Library for Python
=========================================

*Note: The Stackdriver Public REST APIs are currently in Alpha testing.
They may change often.  You can read the current REST API docs at http://docs.stackdriver.com/api*

The Stackdriver API Client Library is a thin wrapper for accessing
Stackdriver's public REST API

Examples
--------

**Instantiate an api instance**

.. sourcecode:: python

    from stackdriver import StackApi
    api = StackApi(apikey='yourapikey')

**Users**

.. sourcecode:: python

    # grab a list of users
    print api.Users.LIST()

    # grab a single user
    print api.Users.GET(id=2)

**Groups**

.. sourcecode:: python

    # grab a list of groups
    print api.Groups.LIST()

    # grab a single group
    print api.Groups.GET(id=67)

    # create a new group
    group = api.Groups({
        'conjunction': 'And',
        'name': 'Production Webservers',
        'parent_id': None,
        'cluster': False,
        'conditions': [
            {
                'type': 'name',
                'comparison': 'starts_with',
                'value': 'web'
            },
            {
                'type': 'tag',
                'comparison': 'equals',
                'name': 'environment',  # this assumes an environment tag on all production machines
                'value': 'production'
            },
        ]
    })

    group.CREATE()

    print group.id

    # delete the group
    group.DELETE()

    print group.deleted_epoch

**Resolve**

.. sourcecode:: python

    # query a resource name to resolve to a unique id
    # if the name exists for multiple resources (such as across availability
    # zones and different resource types) return them all

    # since resolve takes a json query object we use post instead of get to
    # avoid URL length limits - in REST terms you are creating an adhoc query
    # which then gets executed on the server

    resources = api.Resolve.POST({
        'name': 'web-1'
    })

    print resources

