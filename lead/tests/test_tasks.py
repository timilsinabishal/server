from django.conf import settings
from deep.tests import TestCase

from lead.tasks import extract_from_lead, _preprocess
from lead.models import Lead

from utils.common import get_or_write_file, makedirs
from utils.extractor.tests.test_web_document import HTML_URL

import os
import logging
logger = logging.getLogger(__name__)


class ExtractFromLeadTaskTest(TestCase):
    def setUp(self):
        super().setUp()

        # This is similar to test_web_document
        self.path = os.path.join(settings.TEST_DIR, 'documents_urls')
        makedirs(self.path)

        # Create the sample lead
        self.lead = self.create(Lead)
        self.lead.text = ''
        self.lead.url = HTML_URL
        self.lead.save()

    def test_extraction(self):
        # Check if extraction works succesfully

        try:
            result = extract_from_lead(self.lead.id)
            self.assertTrue(result)

            # Check if the extraction did create proper lead preview
            lead_preview = self.lead.leadpreview
            self.assertIsNotNone(lead_preview)

            # This is similar to test_web_document
            path = os.path.join(
                self.path,
                '.'.join(HTML_URL.split('/')[-1:]),
            )
            extracted = get_or_write_file(path + '.txt',
                                          lead_preview.text_extract)
            self.assertEqual(
                ' '.join(lead_preview.text_extract.split()),
                _preprocess(' '.join(extracted.read().split())),
            )
        except Exception:
            import traceback
            logger.warning('\n' + ('*' * 30))
            logger.warning('LEAD EXTRACTION ERROR:')
            logger.warning(traceback.format_exc())
            return
