"""
Define clients for other services we interact with.

Structure copied from sfl2/gateway//gateway/client.py

For more usage information, see the Bravado docs:

     http://bravado.readthedocs.io/en/latest/quickstart.html
"""

import logging
import os.path
from urlparse import urlparse

from bravado.client import SwaggerClient
from bravado.swagger_model import load_file


logger = logging.getLogger(__name__)


class Clients(object):

    def __init__(self):
        """
        Initialize bravado client.

        """

        self.spec_dir_absolute_path = os.path.dirname(__file__)
        self.bravado_config = dict(
            validate_swagger_spec=True,
            validate_requests=True,
            validate_responses=True,
            use_models=True,
        )

        self._add_swagger('gateway', 'https://gateway.vcf-test.vzw.dev.llabs.io/')

    def _add_swagger(self, service_name, service_url):
        # create client

        # Fix bravado URL. By default Bravado ignores non-host parts of the input
        # URL if the spec base path is defined. We want the path from the URL plus
        # the spec's base path.
        spec_dict = load_file(os.path.join(self.spec_dir_absolute_path, service_name + '.json'))
        base_path = (
            urlparse(service_url).path.rstrip('/') +
            spec_dict.get('basePath', ''))
        if base_path:
            spec_dict['basePath'] = base_path

        swagger_client = SwaggerClient.from_spec(
            spec_dict,
            origin_url=service_url,
            config=self.bravado_config)

        setattr(self, service_name, swagger_client)


clients = Clients()
