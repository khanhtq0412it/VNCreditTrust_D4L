from variables.helper import BaseConfig

class GoogleConfig(BaseConfig):
    """
    Configuration loader for Google Gemini and Google Cloud authentication.

    This class inherits from `BaseConfig` and defines the required environment
    variables used to authenticate with Google's Gemini APIs and related services.

    It ensures that the listed variables are present when loaded, and can be
    accessed by other modules that require Google Cloud credentials.

    Attributes
    ----------
    VARIABLES : list[str]
        List of required configuration variable keys:
        - "GOOGLE_GEMINI_SERVICE_ACCOUNT": String containing the service account
          JSON credentials or a filesystem path to the credential file.
        - "GOOGLE_GEMINI_API_KEY": Google API key used for accessing the Gemini API
          without a service account.
    """
    VARIABLES = [
        "GOOGLE_GEMINI_SERVICE_ACCOUNT",
        "GOOGLE_GEMINI_API_KEY"
    ]
