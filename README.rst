==================
aws-okta-processor
==================

.. image:: https://github.com/godaddy/aws-okta-processor/workflows/.github/workflows/build.yml/badge.svg?branch=master
   :target: https://github.com/godaddy/aws-okta-processor/actions?query=workflow%3A.github%2Fworkflows%2Fbuild.yml
   :alt: Build Status

.. image:: https://codecov.io/gh/godaddy/aws-okta-processor/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/godaddy/aws-okta-processor
   :alt: Coverage

.. image:: https://img.shields.io/pypi/v/aws-okta-processor.svg
   :target: https://pypi.python.org/pypi/aws-okta-processor
   :alt: Latest Version

.. image:: https://img.shields.io/pypi/status/aws-okta-processor
   :target: https://pypi.python.org/pypi/aws-okta-processor
   :alt: Status

.. image:: https://img.shields.io/pypi/pyversions/aws-okta-processor
   :target: https://pypi.python.org/pypi/aws-okta-processor
   :alt: Python Version

.. image:: https://img.shields.io/pypi/dm/aws-okta-processor
   :target: https://pypi.python.org/pypi/aws-okta-processor
   :alt: Downloads

This package provides a command for fetching AWS credentials through Okta.

------------
Installation
------------

The recommended way to install aws-okta-processor is using `pipx`_. This has the
benefit that the command is available in your shell without needing to activate
a virtualenv while still keeping its dependencies isolated from site-packages::

    $ pipx install aws-okta-processor

and, to upgrade to a new version::

    $ pipx upgrade aws-okta-processor


You can also install with `pip`_ in a ``virtualenv``::

    $ pip install aws-okta-processor

or, if you are not installing in a ``virtualenv``, to install globally::

    $ sudo pip install aws-okta-processor

or for your user::

    $ pip install --user aws-okta-processor


If you have aws-okta-processor installed with `pip`_ and want to upgrade to the latest
version you can run::

    $ pip install --upgrade aws-okta-processor

.. note::

    On OS X, if you see an error regarding the version of six that came with
    distutils in El Capitan, use the ``--ignore-installed`` option::

        $ sudo pip install aws-okta-processor --ignore-installed six

This will install the aws-okta-processor package as well as all dependencies.  You can
also just `download the tarball`_.  Once you have the
aws-okta-processor directory structure on your workstation, you can just run::

    $ cd <path_to_aws-okta-processor>
    $ python setup.py install

---------------
Getting Started
---------------

This package is best used in `AWS Named Profiles`_ 
with tools and libraries that recognize `credential_process`_.

To setup aws-okta-processor in a profile create an INI formatted file like this::

    [default]
    credential_process=aws-okta-processor authenticate --user <user_name> --organization <organization>.okta.com

and place it in ``~/.aws/credentials`` (or in
``%UserProfile%\.aws/credentials`` on Windows). Then run::

    $ pip install awscli
    $ aws sts get-caller-identity

Supply a password then select your AWS Okta application and account role if prompted.
The AWS CLI command will return a result showing the assumed account role. If you run the
AWS CLI command again you will get the same role back without any prompts due to caching.

For tools and libraries that do not recognize ``credential_process`` aws-okta-processor
can be ran to export the following as environment variables::

    AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY
    AWS_SESSION_TOKEN

For Linux or OSX run::

    $ eval $(aws-okta-processor authenticate --environment --user <user_name> --organization <organization>.okta.com)

On Unix systems pass a `--target-shell` in order to change the
export command output. Bash is the default target shell.
We also allow [fish shell](https://fishshell.com/) as a valid target::

    $ eval (aws-okta-processor authenticate --environment --user <user_name> --organization <organization>.okta.com --target-shell fish)

For Windows run::

    $ Invoke-Expression (aws-okta-processor authenticate --environment --user <user_name> --organization <organization>.okta.com)

----------------------------
Other Configurable Variables
----------------------------

Additional variables can also be passed to aws-okta-processors ``authenticate`` command 
as options or environment variables as outlined in the table below.

============= =============== ====================== ========================================
Variable      Option          Environment Variable   Description
============= =============== ====================== ========================================
user          --user          AWS_OKTA_USER          Okta user name
------------- --------------- ---------------------- ----------------------------------------
password      --pass          AWS_OKTA_PASS          Okta user password
------------- --------------- ---------------------- ----------------------------------------
organization  --organization  AWS_OKTA_ORGANIZATION  Okta FQDN for Organization
------------- --------------- ---------------------- ----------------------------------------
application   --application   AWS_OKTA_APPLICATION   Okta AWS application URL
------------- --------------- ---------------------- ----------------------------------------
role          --role          AWS_OKTA_ROLE          AWS Role ARN
------------- --------------- ---------------------- ----------------------------------------
account_alias --account-alias AWS_OKTA_ACCOUNT_ALIAS AWS Account Filter
------------- --------------- ---------------------- ----------------------------------------
region        --region        AWS_OKTA_REGION        AWS Region
------------- --------------- ---------------------- ----------------------------------------
duration      --duration      AWS_OKTA_DURATION      Duration in seconds for AWS session
------------- --------------- ---------------------- ----------------------------------------
key           --key           AWS_OKTA_KEY           Key used in generating AWS session cache
------------- --------------- ---------------------- ----------------------------------------
environment   --environment                          Output command to set ENV variables
------------- --------------- ---------------------- ----------------------------------------
silent        --silent                               Silence Info output
------------- --------------- ---------------------- ----------------------------------------
factor        --factor        AWS_OKTA_FACTOR        MFA type. `push:okta`, `token:software:totp:okta`, `token:software:totp:google` and `token:hardware:yubico` are supported.
------------- --------------- ---------------------- ----------------------------------------
no_okta_cache --no-okta-cache AWS_OKTA_NO_OKTA_CACHE Do not read okta cache
------------- --------------- ---------------------- ----------------------------------------
no_aws_cache  --no-aws-cache  AWS_OKTA_NO_AWS_CACHE  Do not read aws cache
------------- --------------- ---------------------- ----------------------------------------
target_shell  --target-shell  AWS_OKTA_TARGET_SHELL  Target shell to format export command
------------- --------------- ---------------------- ----------------------------------------
sign_in_url   --sign-in-url   AWS_OKTA_SIGN_IN_URL   AWS Sign In URL
============= =============== ====================== ========================================

^^^^^^^^
Examples
^^^^^^^^

If you do not want aws-okta-processor to prompt for any selection input you can export the following::

    $ export AWS_OKTA_APPLICATION=<application_url> AWS_OKTA_ROLE=<role_arn> AWS_OKTA_FACTOR=<factor_type>

Or pass additional options to the command::

    $ aws-okta-processor authenticate --user <user_name> --organization <organization>.okta.com --application <application_url> --role <role_arn> --factor <factor_type>

-------
Caching
-------

This package leverages caching of both the Okta session and AWS sessions. It's helpful to 
understand how this caching works to avoid confusion when attempting to switch between AWS roles.

^^^^
Okta
^^^^

When aws-okta-processor attempts authentication it will check ``~/.aws-okta-processor/cache/``
for a file named ``<user>-<organization>-session.json`` based on the ``user`` and ``organization`` 
option values passed. If the file is not found or the session contents are stale then 
aws-okta-processor will create a new session and write it to ``~/.aws-okta-processor/cache/``.
If the file exists and the session is not stale then the existing session gets refreshed.

^^^
AWS
^^^

After aws-okta-processor has a session with Okta and an AWS role has been selected it will fetch 
the role's keys and session token. This session information from the AWS role gets cached as a 
json file under ``~/.aws/boto/cache``. The file name is a SHA1 hash based on a combination the
``user``, ``organization`` and ``key`` option values passed to the command.

If you want to store a seperate AWS role session cache for each role assumed using the same 
``user`` and ``organization`` option values then pass a unique value to ``key``.
Named profiles for different roles can then be defined in ``~/.aws/credentials`` with content like this::

    [role_one]
    credential_process=aws-okta-processor authenticate --user <user_name> --organization <organization>.okta.com --application <application_url> --role <role_one_arn> --factor <factor_type> --key role_one

    [role_two]
    credential_process=aws-okta-processor authenticate --user <user_name> --organization <organization>.okta.com --application <application_url> --role <role_two_arn> --factor <factor_type> --key role_two

To clear all AWS session caches run::

    $ rm ~/.aws/boto/cache/*


-----------------------------
Project or User Configuration
-----------------------------

``aws-okta-processor`` can inherit arguments from a ``.awsoktaprocessor`` file located in the user's home directory or the current working
directory.

*.awsoktaprocessor*

.. code-block:: ini

    [defaults]
    user=jdoe

    [authenticate]
    user=ssmith

In this example...

* ``authenticate > user`` overrides ``defaults > user``
* ``{workingDir}/.awsoktaprocessor`` overrides ``~/.awsoktaprocessor``
* ``aws-okta-processor`` arguments override any options from dotfiles

-----------------------------
Get Roles
-----------------------------

To get roles, use the ``get-roles`` command. This command supports outputing the roles as AWS profiles, JSON, or custom formatted text.

.. code-block:: bash

   # write all the roles as AWS profiles
   aws-okta-processor get-roles -u jdoe -o mycompany.okta.com --output=profiles > ~/.aws/credentials
   
   # get account and role
   aws-okta-processor get-roles -u jdoe -o mycompany.okta.com --output=text --output-format="{account},{role}"

   # get JSON
   aws-okta-processor get-roles -u jdoe -o mycompany.okta.com --output=json


Output Types

* ``json`` (default): output as JSON
* ``profiles``: output AWS profiles to be stored in ``~/.aws/credentials``
* ``text``: custom formatted text using ``--output-format`` and tokens

Output Format Tokens

* ``{account}``: name of the account
* ``{account_id}``: account Id
* ``{account_raw}``: account information as seen on Okta site (``Account: blah-blah (id)``)
* ``{application_url}``: full Okta application url
* ``{organization}``: organization as provided
* ``{role}``: role ARN
* ``{role_suffix}``: last element of the role (delimited using ``AWS_OKTA_ROLE_SUFFIX_DELIMITER`` or ``-``)
* ``{user}``: user as provided




------------
Getting Help
------------

* Ask a question on `slack <https://godaddy-oss-slack.herokuapp.com>`__
* If it turns out that you may have found a bug, please `open an issue <https://github.com/godaddy/aws-okta-processor/issues/new>`__

---------------
Acknowledgments
---------------

This package was influenced by `AlainODea <https://github.com/AlainODea>`__'s
work on `okta-aws-cli-assume-role <https://github.com/oktadeveloper/okta-aws-cli-assume-role>`__.



.. _`pip`: http://www.pip-installer.org/en/latest/
.. _`pipx`: https://pipxproject.github.io/pipx/
.. _`download the tarball`: https://pypi.org/project/aws-okta-processor/
.. _`AWS Named Profiles`: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html
.. _`credential_process`: https://docs.aws.amazon.com/cli/latest/topic/config-vars.html#sourcing-credentials-from-external-processes
