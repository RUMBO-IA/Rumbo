"""Static regression checks for public landing retirement redirects.

Run from any cwd: python -m unittest scripts/test_pr367_retired_routes.py
This file intentionally does not deploy or contact production.
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CANONICAL = 'https://rumbo.verso.fans'


def config(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding='utf-8'))


def redirect_for(document, source):
    matches = [rule for rule in document.get('redirects', ()) if rule.get('source') == source]
    if len(matches) != 1:
        raise AssertionError(f'expected exactly one redirect for {source}, got {len(matches)}')
    return matches[0]


class RetiredLandingRoutesTest(unittest.TestCase):
    def test_root_redirects_spanish_legacy_alias(self):
        root = config('vercel.json')
        rule = redirect_for(root, '/es')
        self.assertEqual(rule['destination'], '/')
        self.assertIs(rule['permanent'], True)
        self.assertFalse(any(x.get('source') == '/es' for x in root.get('rewrites', ())))

    def test_secondary_legal_pages_use_canonical_absolute_redirects(self):
        secondary = config('apps/landing-publica/vercel.json')
        for stem in ('privacy', 'terms'):
            for suffix in ('', '.html'):
                with self.subTest(path=stem + suffix):
                    rule = redirect_for(secondary, '/' + stem + suffix)
                    self.assertEqual(rule['destination'], f'{CANONICAL}/{stem}')
                    self.assertIs(rule['permanent'], True)

    def test_secondary_spanish_rewrite_preserved(self):
        secondary = config('apps/landing-publica/vercel.json')
        matches = [x for x in secondary.get('rewrites', ()) if x.get('source') == '/es']
        self.assertEqual(matches, [{'source': '/es', 'destination': '/index-es.html'}])

    def test_legal_redirects_never_shadow_rewrites(self):
        secondary = config('apps/landing-publica/vercel.json')
        redirects = [x['source'] for x in secondary.get('redirects', ())]
        rewrites = [x['source'] for x in secondary.get('rewrites', ())]
        self.assertEqual(len(redirects), len(set(redirects)))
        self.assertTrue(set(redirects).isdisjoint(rewrites))


if __name__ == '__main__':
    unittest.main()
