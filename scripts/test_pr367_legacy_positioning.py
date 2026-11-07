"""Behavioral regression tests for retiring CRM-only marketing claims without banning geography."""
import pathlib
import unittest

from scripts import verify_brand_contract as brand


class LegacyPublicPositioningTest(unittest.TestCase):
    def scan(self, body):
        root = pathlib.Path('/virtual/rumbo-brand')
        errors = []
        brand._check_surface(
            root, root / 'privacy.html', f'<title>RUMBO IA</title><p>{body}</p>',
            {'non_canonical': []}, errors, require_human_control=False
        )
        return [e for e in errors if 'legacy public positioning' in e]

    def test_geographic_disclosure_does_not_impersonate_retired_crm_brand(self):
        for text in (
            'Prestamos soporte de privacidad en Latinoamérica.',
            'Our services may be offered in Latin America.',
            'Jurisdicciones incluidas: LATAM, América Latina, Argentina.',
        ):
            with self.subTest(text=text):
                self.assertEqual(self.scan(text), [])

    def test_spanish_integration_and_sync_claim_is_retired(self):
        for text in (
            'Integración y sincronización de CRM',
            'Integracion y sincronizacion de CRM',
            'Integración y sincronizacion de CRM',
            'Integracion y sincronización de CRM',
        ):
            with self.subTest(text=text):
                self.assertTrue(self.scan(text), text)

    def test_dashed_human_controlled_ai_crm_claim_stays_retired(self):
        self.assertTrue(self.scan('Human-controlled AI CRM software.'))

    def test_generic_current_operational_ai_claim_passes(self):
        self.assertEqual(self.scan('Operational AI systems with human control.'), [])


if __name__ == '__main__':
    unittest.main()
