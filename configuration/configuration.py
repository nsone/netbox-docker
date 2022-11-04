####
## We recommend to not edit this file.
## Create separate files to overwrite the settings.
## See `extra.py` as an example.
####

import re
from os import environ
from os.path import abspath, dirname, join
from termios import VREPRINT
from typing import Any, Callable, Tuple

# For reference see https://docs.netbox.dev/en/stable/configuration/
# Based on https://github.com/netbox-community/netbox/blob/develop/netbox/netbox/configuration_example.py

###
# NetBox-Docker Helper functions
###

# Read secret from file
def _read_secret(secret_name: str, default: str | None = None) -> str | None:
    try:
        f = open('/run/secrets/' + secret_name, 'r', encoding='utf-8')
    except EnvironmentError:
        return default
    else:
        with f:
            return f.readline().strip()

# If the `map_fn` isn't defined, then the value that is read from the environment (or the default value if not found) is returned.
# If the `map_fn` is defined, then `map_fn` is invoked and the value (that was read from the environment or the default value if not found)
# is passed to it as a parameter. The value returned from `map_fn` is then the return value of this function.
# The `map_fn` is not invoked, if the value (that was read from the environment or the default value if not found) is None.
def _environ_get_and_map(variable_name: str, default: str | None = None, map_fn: Callable[[str], Any | None] = None) -> Any | None:
    env_value = environ.get(variable_name, default)

    if env_value == None:
        return env_value

    if not map_fn:
        return env_value
    
    return map_fn(env_value)

_EQUALS_TRUE = lambda value : value.lower() == 'true'
_AS_INT = lambda value : int(value)
_SPLIT_ON_SPACE = lambda value : list(filter(None, value.split(' ')))

_BASE_DIR = dirname(dirname(abspath(__file__)))

#########################
#                       #
#   Required settings   #
#                       #
#########################

# This is a list of valid fully-qualified domain names (FQDNs) for the NetBox server. NetBox will not permit write
# access to the server via any other hostnames. The first FQDN in the list will be treated as the preferred name.
#
# Example: ALLOWED_HOSTS = ['netbox.example.com', 'netbox.internal.local']
ALLOWED_HOSTS = environ.get('ALLOWED_HOSTS', '*').split(' ')

# PostgreSQL database configuration. See the Django documentation for a complete list of available parameters:
#   https://docs.djangoproject.com/en/stable/ref/settings/#databases
DATABASE = {
    'NAME': environ.get('DB_NAME', 'netbox'),       # Database name
    'USER': environ.get('DB_USER', ''),             # PostgreSQL username
    'PASSWORD': _read_secret('db_password', environ.get('DB_PASSWORD', '')),
                                                    # PostgreSQL password
    'HOST': environ.get('DB_HOST', 'localhost'),    # Database server
    'PORT': environ.get('DB_PORT', ''),             # Database port (leave blank for default)
    'OPTIONS': {'sslmode': environ.get('DB_SSLMODE', 'prefer')},
                                                    # Database connection SSLMODE
    'CONN_MAX_AGE': _environ_get_and_map('DB_CONN_MAX_AGE', '300', _AS_INT),
                                                    # Max database connection age
    'DISABLE_SERVER_SIDE_CURSORS': _environ_get_and_map('DB_DISABLE_SERVER_SIDE_CURSORS', 'False', _EQUALS_TRUE),
                                                    # Disable the use of server-side cursors transaction pooling
}

# Redis database settings. Redis is used for caching and for queuing background tasks such as webhook events. A separate
# configuration exists for each. Full connection details are required in both sections, and it is strongly recommended
# to use two separate database IDs.
REDIS = {
    'tasks': {
        'HOST': environ.get('REDIS_HOST', 'redis'),
        'PORT': _environ_get_and_map('REDIS_PORT', 6379, _AS_INT),
        'PASSWORD': _read_secret('redis_password', environ.get('REDIS_PASSWORD', '')),
        'DATABASE': _environ_get_and_map('REDIS_DATABASE', 0, _AS_INT),
        'SSL': _environ_get_and_map('REDIS_SSL', 'False', _EQUALS_TRUE),
        'INSECURE_SKIP_TLS_VERIFY': _environ_get_and_map('REDIS_INSECURE_SKIP_TLS_VERIFY', 'False', _EQUALS_TRUE),
    },
    'caching': {
        'HOST': environ.get('REDIS_CACHE_HOST', environ.get('REDIS_HOST', 'redis')),
        'PORT': _environ_get_and_map('REDIS_CACHE_PORT', environ.get('REDIS_PORT', '6379'), _AS_INT),
        'PASSWORD': _read_secret('redis_cache_password', environ.get('REDIS_CACHE_PASSWORD', environ.get('REDIS_PASSWORD', ''))),
        'DATABASE': _environ_get_and_map('REDIS_CACHE_DATABASE', '1', _AS_INT),
        'SSL': _environ_get_and_map('REDIS_CACHE_SSL', environ.get('REDIS_SSL', 'False'), _EQUALS_TRUE),
        'INSECURE_SKIP_TLS_VERIFY': _environ_get_and_map('REDIS_CACHE_INSECURE_SKIP_TLS_VERIFY', environ.get('REDIS_INSECURE_SKIP_TLS_VERIFY', 'False'), _EQUALS_TRUE),
    },
}

# This key is used for secure generation of random numbers and strings. It must never be exposed outside of this file.
# For optimal security, SECRET_KEY should be at least 50 characters in length and contain a mix of letters, numbers, and
# symbols. NetBox will not run without this defined. For more information, see
# https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-SECRET_KEY
SECRET_KEY = _read_secret('secret_key', environ.get('SECRET_KEY', ''))


#########################
#                       #
#   Optional settings   #
#                       #
#########################

# # Specify one or more name and email address tuples representing NetBox administrators. These people will be notified of
# # application errors (assuming correct email settings are provided).
# ADMINS = [
#    # ['John Doe', 'jdoe@example.com'],
# ]

_ALLOWED_URL_SCHEMES = _environ_get_and_map('ALLOWED_URL_SCHEMES', None, _SPLIT_ON_SPACE)
if _ALLOWED_URL_SCHEMES:
    ALLOWED_URL_SCHEMES = _ALLOWED_URL_SCHEMES

# Optionally display a persistent banner at the top and/or bottom of every page. HTML is allowed. To display the same
# content in both banners, define BANNER_TOP and set BANNER_BOTTOM = BANNER_TOP.
if 'BANNER_TOP' in environ:
    BANNER_TOP = environ.get('BANNER_TOP', None)
if 'BANNER_BOTTOM' in environ:
    BANNER_BOTTOM = environ.get('BANNER_BOTTOM', None)

# Text to include on the login page above the login form. HTML is allowed.
if 'BANNER_LOGIN' in environ:
    BANNER_LOGIN = environ.get('BANNER_LOGIN', None)

# Base URL path if accessing NetBox within a directory. For example, if installed at http://example.com/netbox/, set:
# BASE_PATH = 'netbox/'
BASE_PATH = environ.get('BASE_PATH', '')

# Maximum number of days to retain logged changes. Set to 0 to retain changes indefinitely. (Default: 90)
_CHANGELOG_RETENTION = _environ_get_and_map('CHANGELOG_RETENTION', None, _AS_INT)
if _CHANGELOG_RETENTION:
    CHANGELOG_RETENTION = _CHANGELOG_RETENTION

# Maximum number of days to retain job results (scripts and reports). Set to 0 to retain job results in the database indefinitely. (Default: 90)
if 'JOBRESULT_RETENTION' in environ:
    JOBRESULT_RETENTION = _environ_get_and_map('JOBRESULT_RETENTION', None, _AS_INT)

# API Cross-Origin Resource Sharing (CORS) settings. If CORS_ORIGIN_ALLOW_ALL is set to True, all origins will be
# allowed. Otherwise, define a list of allowed origins using either CORS_ORIGIN_WHITELIST or
# CORS_ORIGIN_REGEX_WHITELIST. For more information, see https://github.com/ottoyiu/django-cors-headers
CORS_ORIGIN_ALLOW_ALL = _environ_get_and_map('CORS_ORIGIN_ALLOW_ALL', 'False', _EQUALS_TRUE)
CORS_ORIGIN_WHITELIST = _environ_get_and_map('CORS_ORIGIN_WHITELIST', 'https://localhost', _SPLIT_ON_SPACE)
CORS_ORIGIN_REGEX_WHITELIST = [re.compile(r) for r in _environ_get_and_map('CORS_ORIGIN_REGEX_WHITELIST', '', _SPLIT_ON_SPACE)]

# Set to True to enable server debugging. WARNING: Debugging introduces a substantial performance penalty and may reveal
# sensitive information about your installation. Only enable debugging while performing testing.
# Never enable debugging on a production system.
DEBUG = _environ_get_and_map('DEBUG', 'False', _EQUALS_TRUE)

# This parameter serves as a safeguard to prevent some potentially dangerous behavior,
# such as generating new database schema migrations.
# Set this to True only if you are actively developing the NetBox code base.
DEVELOPER = _environ_get_and_map('DEVELOPER', 'False', _EQUALS_TRUE)

# Email settings
EMAIL = {
    'SERVER': environ.get('EMAIL_SERVER', 'localhost'),
    'PORT': _environ_get_and_map('EMAIL_PORT', 25, _AS_INT),
    'USERNAME': environ.get('EMAIL_USERNAME', ''),
    'PASSWORD': _read_secret('email_password', environ.get('EMAIL_PASSWORD', '')),
    'USE_SSL': _environ_get_and_map('EMAIL_USE_SSL', 'False', _EQUALS_TRUE),
    'USE_TLS': _environ_get_and_map('EMAIL_USE_TLS', 'False', _EQUALS_TRUE),
    'SSL_CERTFILE': environ.get('EMAIL_SSL_CERTFILE', ''),
    'SSL_KEYFILE': environ.get('EMAIL_SSL_KEYFILE', ''),
    'TIMEOUT': _environ_get_and_map('EMAIL_TIMEOUT', 10, _AS_INT),  # seconds
    'FROM_EMAIL': environ.get('EMAIL_FROM', ''),
}

# Enforcement of unique IP space can be toggled on a per-VRF basis. To enforce unique IP space within the global table
# (all prefixes and IP addresses not assigned to a VRF), set ENFORCE_GLOBAL_UNIQUE to True.
_ENFORCE_GLOBAL_UNIQUE = _environ_get_and_map('ENFORCE_GLOBAL_UNIQUE', None, _EQUALS_TRUE)
if _ENFORCE_GLOBAL_UNIQUE:
    ENFORCE_GLOBAL_UNIQUE = _ENFORCE_GLOBAL_UNIQUE

# Exempt certain models from the enforcement of view permissions. Models listed here will be viewable by all users and
# by anonymous users. List models in the form `<app>.<model>`. Add '*' to this list to exempt all models.
EXEMPT_VIEW_PERMISSIONS = _environ_get_and_map('EXEMPT_VIEW_PERMISSIONS', '', _SPLIT_ON_SPACE)

# HTTP proxies NetBox should use when sending outbound HTTP requests (e.g. for webhooks).
# HTTP_PROXIES = {
#     'http': 'http://10.10.1.10:3128',
#     'https': 'http://10.10.1.10:1080',
# }

# IP addresses recognized as internal to the system. The debugging toolbar will be available only to clients accessing
# NetBox from an internal IP.
INTERNAL_IPS = _environ_get_and_map('INTERNAL_IPS', '127.0.0.1 ::1', _SPLIT_ON_SPACE)

# Enable GraphQL API.
_GRAPHQL_ENABLED = _environ_get_and_map('GRAPHQL_ENABLED', None, _EQUALS_TRUE)
if _GRAPHQL_ENABLED:
    GRAPHQL_ENABLED = _GRAPHQL_ENABLED

# # Enable custom logging. Please see the Django documentation for detailed guidance on configuring custom logs:
# #   https://docs.djangoproject.com/en/stable/topics/logging/
# LOGGING = {}

# Automatically reset the lifetime of a valid session upon each authenticated request. Enables users to remain
# authenticated to NetBox indefinitely.
LOGIN_PERSISTENCE = _environ_get_and_map('LOGIN_PERSISTENCE', 'False', _EQUALS_TRUE)

# Setting this to True will permit only authenticated users to access any part of NetBox. By default, anonymous users
# are permitted to access most data in NetBox (excluding secrets) but not make any changes.
LOGIN_REQUIRED = _environ_get_and_map('LOGIN_REQUIRED', 'False', _EQUALS_TRUE)

# The length of time (in seconds) for which a user will remain logged into the web UI before being prompted to
# re-authenticate. (Default: 1209600 [14 days])
LOGIN_TIMEOUT = _environ_get_and_map('LOGIN_TIMEOUT', 1209600, _AS_INT)

# Setting this to True will display a "maintenance mode" banner at the top of every page.
_MAINTENANCE_MODE = _environ_get_and_map('MAINTENANCE_MODE', None, _EQUALS_TRUE)
if _MAINTENANCE_MODE:
    MAINTENANCE_MODE = _MAINTENANCE_MODE

# Maps provider
if 'MAPS_URL' in environ:
    MAPS_URL = environ.get('MAPS_URL', None)

# An API consumer can request an arbitrary number of objects =by appending the "limit" parameter to the URL (e.g.
# "?limit=1000"). This setting defines the maximum limit. Setting it to 0 or None will allow an API consumer to request
# all objects by specifying "?limit=0".
_MAX_PAGE_SIZE = _environ_get_and_map('MAX_PAGE_SIZE', None, _AS_INT)
if _MAX_PAGE_SIZE:
    MAX_PAGE_SIZE = _MAX_PAGE_SIZE

# The file path where uploaded media such as image attachments are stored. A trailing slash is not needed. Note that
# the default value of this setting is derived from the installed location.
MEDIA_ROOT = environ.get('MEDIA_ROOT', join(_BASE_DIR, 'media'))

# Expose Prometheus monitoring metrics at the HTTP endpoint '/metrics'
METRICS_ENABLED = _environ_get_and_map('METRICS_ENABLED', 'False', _EQUALS_TRUE)

# Credentials that NetBox will uses to authenticate to devices when connecting via NAPALM.
if 'NAPALM_USERNAME' in environ:
    NAPALM_USERNAME = environ.get('NAPALM_USERNAME', None)
if 'NAPALM_PASSWORD' in environ:
    NAPALM_PASSWORD = _read_secret('napalm_password', environ.get('NAPALM_PASSWORD', None))

# NAPALM timeout (in seconds). (Default: 30)
_NAPALM_TIMEOUT = _environ_get_and_map('NAPALM_TIMEOUT', None, _AS_INT)
if _NAPALM_TIMEOUT:
    NAPALM_TIMEOUT = _NAPALM_TIMEOUT

# # NAPALM optional arguments (see http://napalm.readthedocs.io/en/latest/support/#optional-arguments). Arguments must
# # be provided as a dictionary.
# NAPALM_ARGS = None

# Determine how many objects to display per page within a list. (Default: 50)
_PAGINATE_COUNT = _environ_get_and_map('PAGINATE_COUNT', None, _AS_INT)
if _PAGINATE_COUNT:
    PAGINATE_COUNT = _PAGINATE_COUNT

# # Enable installed plugins. Add the name of each plugin to the list.
# PLUGINS = []

# # Plugins configuration settings. These settings are used by various plugins that the user may have installed.
# # Each key in the dictionary is the name of an installed plugin and its value is a dictionary of settings.
# PLUGINS_CONFIG = {
# }

# When determining the primary IP address for a device, IPv6 is preferred over IPv4 by default. Set this to True to
# prefer IPv4 instead.
_PREFER_IPV4 = _environ_get_and_map('PREFER_IPV4', None, _EQUALS_TRUE)
if _PREFER_IPV4:
    PREFER_IPV = _PREFER_IPV4

# The default value for the amperage field when creating new power feeds.
_POWERFEED_DEFAULT_AMPERAGE = _environ_get_and_map('POWERFEED_DEFAULT_AMPERAGE', None, _AS_INT)
if _POWERFEED_DEFAULT_AMPERAGE:
    POWERFEED_DEFAULT_AMPERAGE = _POWERFEED_DEFAULT_AMPERAGE

# The default value (percentage) for the max_utilization field when creating new power feeds.
_POWERFEED_DEFAULT_MAX_UTILIZATION = _environ_get_and_map('POWERFEED_DEFAULT_MAX_UTILIZATION', None, _AS_INT)
if _POWERFEED_DEFAULT_MAX_UTILIZATION:
    POWERFEED_DEFAULT_MAX_UTILIZATION = _POWERFEED_DEFAULT_MAX_UTILIZATION

# The default value for the voltage field when creating new power feeds.
_POWERFEED_DEFAULT_VOLTAGE = _environ_get_and_map('POWERFEED_DEFAULT_VOLTAGE', None, _AS_INT)
if _POWERFEED_DEFAULT_VOLTAGE:
    POWERFEED_DEFAULT_VOLTAGE = _POWERFEED_DEFAULT_VOLTAGE

# Rack elevation size defaults, in pixels. For best results, the ratio of width to height should be roughly 10:1.
_RACK_ELEVATION_DEFAULT_UNIT_HEIGHT = _environ_get_and_map('RACK_ELEVATION_DEFAULT_UNIT_HEIGHT', None, _AS_INT)
if _RACK_ELEVATION_DEFAULT_UNIT_HEIGHT:
    RACK_ELEVATION_DEFAULT_UNIT_HEIGHT = _RACK_ELEVATION_DEFAULT_UNIT_HEIGHT
_RACK_ELEVATION_DEFAULT_UNIT_WIDTH = _environ_get_and_map('RACK_ELEVATION_DEFAULT_UNIT_WIDTH', None, _AS_INT)
if _RACK_ELEVATION_DEFAULT_UNIT_WIDTH:
    RACK_ELEVATION_DEFAULT_UNIT_WIDTH = _RACK_ELEVATION_DEFAULT_UNIT_WIDTH

# Remote authentication support
REMOTE_AUTH_ENABLED = _environ_get_and_map('REMOTE_AUTH_ENABLED', 'False', _EQUALS_TRUE)
REMOTE_AUTH_BACKEND = environ.get('REMOTE_AUTH_BACKEND', 'netbox.authentication.RemoteUserBackend')
REMOTE_AUTH_HEADER = environ.get('REMOTE_AUTH_HEADER', 'HTTP_REMOTE_USER')
REMOTE_AUTH_AUTO_CREATE_USER = _environ_get_and_map('REMOTE_AUTH_AUTO_CREATE_USER', 'True', _EQUALS_TRUE)
REMOTE_AUTH_DEFAULT_GROUPS = _environ_get_and_map('REMOTE_AUTH_DEFAULT_GROUPS', '', _SPLIT_ON_SPACE)
# REMOTE_AUTH_DEFAULT_PERMISSIONS = {}

# This repository is used to check whether there is a new release of NetBox available. Set to None to disable the
# version check or use the URL below to check for release in the official NetBox repository.
RELEASE_CHECK_URL = environ.get('RELEASE_CHECK_URL', None)
# RELEASE_CHECK_URL = 'https://api.github.com/repos/netbox-community/netbox/releases'

# The file path where custom reports will be stored. A trailing slash is not needed. Note that the default value of
# this setting is derived from the installed location.
REPORTS_ROOT = environ.get('REPORTS_ROOT', '/opt/netbox/reports')

# Maximum execution time for background tasks, in seconds.
RQ_DEFAULT_TIMEOUT = _environ_get_and_map('RQ_DEFAULT_TIMEOUT', 300, _AS_INT)

# The file path where custom scripts will be stored. A trailing slash is not needed. Note that the default value of
# this setting is derived from the installed location.
SCRIPTS_ROOT = environ.get('SCRIPTS_ROOT', '/opt/netbox/scripts')

# The name to use for the csrf token cookie.
CSRF_COOKIE_NAME = environ.get('CSRF_COOKIE_NAME', 'csrftoken')

# Cross-Site-Request-Forgery-Attack settings. If Netbox is sitting behind a reverse proxy, you might need to set the CSRF_TRUSTED_ORIGINS flag.
# Django 4.0 requires to specify the URL Scheme in this setting. An example environment variable could be specified like:
# CSRF_TRUSTED_ORIGINS=https://demo.netbox.dev http://demo.netbox.dev
CSRF_TRUSTED_ORIGINS = _environ_get_and_map('CSRF_TRUSTED_ORIGINS', '', _SPLIT_ON_SPACE)

# The name to use for the session cookie.
SESSION_COOKIE_NAME = environ.get('SESSION_COOKIE_NAME', 'sessionid')

# By default, NetBox will store session data in the database. Alternatively, a file path can be specified here to use
# local file storage instead. (This can be useful for enabling authentication on a standby instance with read-only
# database access.) Note that the user as which NetBox runs must have read and write permissions to this path.
SESSION_FILE_PATH = environ.get('SESSION_FILE_PATH', environ.get('SESSIONS_ROOT', None))

# Time zone (default: UTC)
TIME_ZONE = environ.get('TIME_ZONE', 'UTC')

# Date/time formatting. See the following link for supported formats:
# https://docs.djangoproject.com/en/stable/ref/templates/builtins/#date
DATE_FORMAT = environ.get('DATE_FORMAT', 'N j, Y')
SHORT_DATE_FORMAT = environ.get('SHORT_DATE_FORMAT', 'Y-m-d')
TIME_FORMAT = environ.get('TIME_FORMAT', 'g:i a')
SHORT_TIME_FORMAT = environ.get('SHORT_TIME_FORMAT', 'H:i:s')
DATETIME_FORMAT = environ.get('DATETIME_FORMAT', 'N j, Y g:i a')
SHORT_DATETIME_FORMAT = environ.get('SHORT_DATETIME_FORMAT', 'Y-m-d H:i')

# Base level security
SESSION_COOKIE_SECURE = environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
CSRF_COOKIE_SECURE = environ.get('CSRF_COOKIE_SECURE', 'True').lower() == 'true'
SECURE_HSTS_PRELOAD = environ.get('SECURE_HSTS_PRELOAD', 'True').lower() == 'true'
SECURE_HSTS_INCLUDE_SUBDOMAINS = environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True').lower() == 'true'
SECURE_HSTS_SECONDS = environ.get('SECURE_HSTS_SECONDS', '31536000')

# Social Auth Okta
SOCIAL_AUTH_OKTA_OPENIDCONNECT_API_URL = environ.get('SOCIAL_AUTH_OKTA_OPENIDCONNECT_API_URL', None)
SOCIAL_AUTH_OKTA_OPENIDCONNECT_KEY= environ.get('SOCIAL_AUTH_OKTA_OPENIDCONNECT_KEY', None)
SOCIAL_AUTH_OKTA_OPENIDCONNECT_SECRET= environ.get('SOCIAL_AUTH_OKTA_OPENIDCONNECT_SECRET', None)

# Social Auth Azure AD Tenant
SOCIAL_AUTH_REDIRECT_IS_HTTPS = environ.get('SOCIAL_AUTH_REDIRECT_IS_HTTPS', 'True').lower() == 'true'
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = environ.get('SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY', None)
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_RESOURCE = environ.get('SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_RESOURCE', None)
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = environ.get('SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET', None)
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = environ.get('SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID', None)

# Social Auth Azure AD
SOCIAL_AUTH_AZUREAD_OAUTH2_KEY = environ.get('SOCIAL_AUTH_AZUREAD_OAUTH2_KEY', None)
SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET = environ.get('SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET', None)

# This is needed for Storage Bucket
STORAGE_BACKEND = environ.get('STORAGE_BACKEND', 'storages.backends.s3boto3.S3Boto3Storage')
STORAGE_CONFIG  = {
	'AWS_ACCESS_KEY_ID': environ.get('AWS_S3_ACCESS_KEY_ID', None),
	'AWS_SECRET_ACCESS_KEY': _read_secret('aws_s3_secret_access_key', environ.get('AWS_S3_SECRET_ACCESS_KEY', None)),
	'AWS_STORAGE_BUCKET_NAME': environ.get('AWS_STORAGE_BUCKET_NAME', None),
	'AWS_S3_REGION_NAME': environ.get('AWS_S3_REGION_NAME', None),
}