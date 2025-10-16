import logging
import requests

from odoo import models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    def _get_crawl_service_url(self):
        """Get the crawl service URL"""
        return 'http://localhost:8000/crawl' # this endpoint needs to be running on a server

    def action_enrich_with_crawlai(self):
        """Crawl website using HTTP service"""
        self.ensure_one()

        url = self.website

        if not url:
            raise UserError('Please set a website URL for this lead')

        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            _logger.info(f'Starting crawl for lead {self.id}: {url}')

            service_url = self._get_crawl_service_url()

            # Call the crawl service
            response = requests.post(
                service_url,
                json={'url': url},
                timeout=90
            )
            response.raise_for_status()

            data = response.json()

            if data.get('success'):
                _logger.info(f'Successfully crawled {url} for lead {self.id}')
            else:
                raise UserError(f'Crawl failed: {data.get("error")}')

        except requests.RequestException as e:
            _logger.error(f'Error calling crawl service: {str(e)}')
            raise UserError(f'Failed to connect to crawl service: {str(e)}')
        except Exception as e:
            _logger.error(f'Error crawling {url} for lead {self.id}: {str(e)}')
            raise UserError(f'Failed to crawl website: {str(e)}')