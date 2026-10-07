import pathlib,re,unittest

P=pathlib.Path('.github/workflows/rumbo-signed-merge-enqueue-r1.yml')

class Contract(unittest.TestCase):
    def test_bounded_signed_enqueue_contract(self):
        s=P.read_text(encoding='utf-8')
        for needle in [
            'workflow_dispatch:',
            'pr_number:',
            'expected_head_sha:',
            "github.actor == 'fscfede-beep'",
            'runs-on: [self-hosted, Linux, X64, rumbo-ci-linux]',
            "PRIVATE_REPO: 'RUMBO-IA/rumbo-control-queue'",
            'docs/control-authority-anchor-v1.json',
            'required status checks',
            'merge_queue_enqueue.py',
            '--dry-run',
            '--expected-head',
            'RUMBO_EXTERNAL_SPEND_USD=0',
            'RUMBO_PRODUCTION=NO_GO',
        ]:
            self.assertIn(needle,s)
        self.assertNotIn('force: true',s)
        self.assertNotIn('pull_request:',s)
        self.assertNotIn('push:',s)
        self.assertNotRegex(s,re.compile(r'inputs:\s*\n\s*(command|script|shell):',re.I))

if __name__=='__main__': unittest.main()
