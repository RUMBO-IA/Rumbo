"""R7: a ruleset with correct rule names but weakened regex isn't safe."""
import sys, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from safe_merge_evidence import RealEvidence

AUTHOR="commit_author_email_pattern"
COMMITTER="committer_email_pattern"

def ruleset(*, weak=False, missing=False, wrong_operator=False, negate=False):
    pattern=".*" if weak else r"^approved@example\.com$"
    params={"operator":"ends_with" if wrong_operator else "regex",
            "pattern":pattern,"negate":negate}
    items=[
        {"type":AUTHOR} if missing else {"type":AUTHOR,"parameters":dict(params)},
        {"type":COMMITTER,"parameters":dict(params)},
        {"type":"non_fast_forward"}]
    return {"enforcement":"active","bypass_actors":[],
            "conditions":{"ref_name":{"include":["~ALL"],"exclude":[]}},
            "rules":items}

class RulesetIntegrityTests(unittest.TestCase):
    def subject(self,data):
        obj=RealEvidence(HERE.parent,runner=object())
        obj._json=lambda args:data
        return obj

    def test_weakened_wildcard_regex_must_not_pass(self):
        self.assertFalse(self.subject(ruleset(weak=True)).ruleset_ok())

    def test_rule_without_regex_parameters_must_not_pass(self):
        self.assertFalse(self.subject(ruleset(missing=True)).ruleset_ok())

    def test_wrong_regex_operator_must_not_pass(self):
        self.assertFalse(self.subject(ruleset(wrong_operator=True)).ruleset_ok())

    def test_negated_allowlist_must_not_pass(self):
        self.assertFalse(self.subject(ruleset(negate=True)).ruleset_ok())

    def test_explicit_branch_exclusion_must_not_pass(self):
        value=ruleset()
        value["conditions"]["ref_name"]["exclude"]=["refs/heads/main"]
        self.assertFalse(self.subject(value).ruleset_ok())

    def test_duplicate_author_rule_must_not_pass(self):
        value=ruleset()
        value["rules"].append(dict(value["rules"][0]))
        self.assertFalse(self.subject(value).ruleset_ok())

if __name__=="__main__": unittest.main()
