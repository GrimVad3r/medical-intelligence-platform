"""SSL configuration for corporate environments."""

import os
import ssl
import warnings

def disable_ssl_verification():
    """Disable SSL verification for development in corporate networks."""
    
    # Disable SSL verification for requests
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # For older Python versions
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    
    warnings.warn(
        "SSL verification has been disabled. This should only be used in "
        "development environments behind corporate proxies.",
        RuntimeWarning
    )