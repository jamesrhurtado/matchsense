"""Offline-only scenario catalogue. Never imported by the application or agents.

Expectations describe authored situations and observation availability. They do not
call the detector, copy its output, or contain generated narrative answers.
"""
from dataclasses import asdict, dataclass
from uuid import NAMESPACE_URL, uuid5

VERSION = '2.0.0'


@dataclass(frozen=True)
class Parent:
    id: str
    split: str
    x: float
    y: float
    distance: float
    reverse: bool
    team: str
    release_ms: int
    seed: int


# Whole geometry/roster/motion parents belong to one split, including all faults.
# Frozen before the first v2 evaluation. Held-out parents are now a regression
# set; any subsequent detector/prompt tuning needs a newly authored final test.
PARENTS = (
    Parent('p01', 'development', 26, 22, 18, False, 'blue', 12000, 8101),
    Parent('p02', 'development', 32, 40, 20, True, 'amber', 18000, 8102),
    Parent('p03', 'validation', 38, 28, 22, False, 'amber', 16000, 8201),
    Parent('p04', 'validation', 29, 44, 17, True, 'blue', 22000, 8202),
    Parent('p05', 'held_out', 41, 20, 19, True, 'blue', 24000, 8301),
    Parent('p06', 'held_out', 24, 35, 24, False, 'amber', 14000, 8302),
)

# Description, expected behavior; generation semantics live in suite.py.
FAMILIES = {
    'escape': ('Pressured, received forward pass followed by a seven metre carry.', 'candidate'),
    'unpressured': ('Completed forward pass with every opponent far from the passer.', 'quiet'),
    'intercepted': ('Opponent receives the ball and possession changes at resolution.', 'quiet'),
    'insufficient_bypass': ('Only one opponent is longitudinally between release and reception.', 'quiet'),
    'backward_pass': ('Reception is behind the passer in the attacking direction.', 'quiet'),
    'lateral_pass': ('Reception changes width without moving forward along the pitch.', 'quiet'),
    'insufficient_progression': ('Received under pressure but continuation advances only four metres.', 'quiet'),
    'rounding_boundary': ('Continuation advances 4.96 m, below the five metre requirement.', 'quiet'),
    'possession_interruption': ('Ball becomes loose briefly within the retention window.', 'quiet'),
    'uncontrolled': ('Pass ends without a known receiving controller.', 'quiet'),
    'out_of_play': ('Pass ends at the touchline with play stopped.', 'quiet'),
    'missing_pressure': ('Opponent is absent throughout the pressure observation window.', 'abstain'),
    'sparse_pressure': ('Three of twenty-one pressure samples omit an opponent.', 'abstain'),
    'missing_release': ('All opponents are absent from the release frame.', 'abstain'),
    'retention_gap': ('A six hundred millisecond hole interrupts confirmation coverage.', 'abstain'),
    'missing_ball_confirmation': ('Ball location is unknown at the confirmation endpoint.', 'abstain'),
    'unknown_possession': ('Possession is explicitly unknown during continuation.', 'abstain'),
    'delayed_outcome': ('Resolution arrives five seconds after confirmation; no early story.', 'candidate_late'),
    'expired_outcome': ('Resolution arrives after the original overlay deadline.', 'expired'),
    'reordered_delivery': ('Deterministic delivery jitter changes arrival order.', 'candidate_late'),
    'duplicates': ('Exact retransmissions preserve source identity.', 'candidate'),
    'correction_withdraws': ('A late correction makes confirmation ball location unknown.', 'withdraw'),
    'correction_restores': ('A late correction supplies the previously unknown confirmation ball.', 'restore'),
    'noisy_tracking': ('Small smooth observational position noise preserves the clear situation.', 'candidate'),
    'different_receiver': ('The actual receiver differs from the intended receiver.', 'candidate'),
    'no_pass_events': ('Tracking alone provides no explicit pass identity or outcome.', 'abstain'),
    'multiple_passes': ('An ordinary pass precedes a qualifying second pass.', 'multiple'),
    'long_session': ('Three qualifying passes separated by quiet play over three minutes.', 'multiple'),
}


@dataclass(frozen=True)
class Case:
    id: str
    parent: Parent
    family: str
    @property
    def match_id(self):
        return 'match-' + uuid5(NAMESPACE_URL, f'whynow-synthetic/{VERSION}/{self.id}').hex[:16]
    def record(self):
        return {'case_id': self.id, 'match_id': self.match_id, 'generator_version': VERSION,
                'parent': asdict(self.parent), 'family': self.family,
                'description': FAMILIES[self.family][0], 'intent': FAMILIES[self.family][1]}


def cases(split=None):
    return [Case(f'{p.id}-{i:02d}', p, family)
            for p in PARENTS if split is None or p.split == split
            for i, family in enumerate(FAMILIES, 1)]


def get_case(case_id):
    return next(c for c in cases() if c.id == case_id)
