"""Authoring-only episode definitions. Never imported by the runtime or agents.

Six independently constructed development scripts, not independent real matches.
Paired cases share their parent's trajectory ancestry. Reference facts live in a
separate evaluation file and are not calculated from these definitions.
"""
from copy import deepcopy
from dataclasses import dataclass, field


@dataclass
class Scene:
    parent: str
    duration: int = 90000
    paths: dict = field(default_factory=dict)
    segments: list = field(default_factory=list)
    events: list = field(default_factory=list)
    shape: list = field(default_factory=list)
    initial_score: dict = field(default_factory=lambda: {'blue': 0, 'amber': 0})

    def path(self, pid, *knots):
        self.paths[pid] = [(int(t * 1000), x, y) for t, x, y in knots]

    def state(self, start, end, status, actor=None, team=None, points=None):
        self.segments.append({'start': int(start * 1000), 'end': int(end * 1000),
                              'status': status, 'actor': actor,
                              'team': team or (actor.split('-')[0] if actor else None),
                              'points': points})

    def event(self, t, kind, team, actor, details, *, key=None, delay=0,
              revision=1, supersedes=None):
        key = key or f'e{len(self.events)+1:03}'
        self.events.append({'time': int(t*1000), 'kind': kind, 'team': team,
                            'actor': actor, 'details': details, 'key': key,
                            'delay': int(delay*1000), 'revision': revision,
                            'supersedes': supersedes})

    def pass_event(self, start, end, passer, receiver, identity, outcome='received'):
        # Exporter binds contact coordinates to the same authored player paths.
        team = passer.split('-')[0]
        self.event(start, 'pass_started', team, passer,
                   {'pass_id': identity, 'intended_receiver_id': receiver}, key=identity+'s')
        self.event(end, 'pass_resolved', team, passer,
                   {'pass_id': identity, 'outcome': outcome,
                    'controlling_team_id': receiver.split('-')[0],
                    'controlling_player_id': receiver}, key=identity+'e')

    def recovery(self, t, actor, previous, cause, identity):
        team = actor.split('-')[0]
        self.event(t, 'ball_recovered', team, actor,
                   {'incident_id': identity, 'previous_team_id': previous, 'cause': cause})
        self.event(t, 'possession_changed', team, actor,
                   {'incident_id': identity, 'previous_team_id': previous,
                    'new_team_id': team, 'controlling_player_id': actor,
                    'reason': 'observed control'})


def support():
    s = Scene('d01')
    s.shape = [(0, 25, 25), (20, 36, 30), (30, 67, 34), (60, 64, 44), (90, 60, 40)]
    s.path('blue-02', (0,18,18), (6,18,18), (25,25,23), (90,32,22))
    s.path('blue-08', (0,27,25), (8,31,26), (16,36,30), (20,36,30), (40,45,25), (90,50,29))
    s.path('blue-11', (0,55,34), (22,60,34), (25,67,34), (35,67,34), (60,72,32), (90,65,30))
    s.path('blue-06', (0,45,49), (25,54,48), (37,58,46), (60,66,45), (90,60,40))
    s.path('amber-06', (0,48,20), (16,38,29), (20,38,29), (35,48,24), (90,62,22))
    s.path('amber-07', (0,50,44), (16,40,33), (20,40,33), (35,46,43), (90,59,48))
    s.path('amber-08', (0,53,18), (16,44,22), (25,48,22), (90,56,15))
    s.state(0,6,'controlled','blue-02')
    s.state(6,8,'in_flight',team='blue',points=('blue-02','blue-08'))
    s.state(8,20,'controlled','blue-08')
    s.state(20,22,'in_flight',team='blue',points=('blue-08','blue-11'))
    s.state(22,35,'controlled','blue-11')
    s.state(35,37,'in_flight',team='blue',points=('blue-11','blue-06'))
    s.state(37,90,'controlled','blue-06')
    s.pass_event(6,8,'blue-02','blue-08','p01')
    s.pass_event(20,22,'blue-08','blue-11','p02')
    s.pass_event(35,37,'blue-11','blue-06','p03')
    return s


def interception():
    s = Scene('d02')
    s.shape = [(0,68,45), (17,50,37), (33,65,20), (65,72,29), (90,62,32)]
    s.path('amber-05', (0,68,48), (12,65,45), (15,65,45), (45,72,48), (90,65,42))
    s.path('amber-10', (0,52,40), (17,53,39), (50,45,48), (90,40,46))
    s.path('blue-06', (0,42,34), (17,50,37), (20,57,38), (30,57,38), (60,60,42), (90,52,40))
    s.path('blue-09', (0,65,16), (33,65,20), (60,72,29), (90,62,32))
    s.state(0,15,'controlled','amber-05')
    s.state(15,17,'in_flight',team='amber',points=('amber-05','blue-06'))
    s.state(17,30,'controlled','blue-06')
    s.state(30,33,'in_flight',team='blue',points=('blue-06','blue-09'))
    s.state(33,90,'controlled','blue-09')
    s.pass_event(15,17,'amber-05','blue-06','p01','intercepted')
    s.events[0]['details']['intended_receiver_id'] = 'amber-10'
    s.recovery(17,'blue-06','amber','interception','i01')
    s.pass_event(30,33,'blue-06','blue-09','p02')
    return s


def shot(blocked=False):
    s = Scene('d03')
    s.shape = [(0,75,25), (22,82,26), (35,91,35), (60,83,45), (90,74,39)]
    s.path('blue-09', (0,75,25), (18,82,26), (22,82,26), (45,78,28), (90,69,33))
    s.path('amber-04', (0,86,43), (18,91,30), (23.2,91,30), (34,86,48), (90,74,39))
    s.path('blue-10', (0,72,42), (18,84,36), (26,89,32), (50,82,40), (90,72,45))
    if blocked:
        s.state(0,22,'controlled','blue-09')
        s.state(22,23.2,'in_flight',team='blue',points=('blue-09',(91,30)))
        s.state(23.2,26,'loose',points=((91,30),'blue-10'))
        s.state(26,90,'controlled','blue-10')
        s.recovery(26,'blue-10',None,'loose_ball','i01')
    else:
        s.path('amber-01', (0,99,34), (18,99,32), (23.2,99,32), (30,96,34), (60,99,34), (90,98,34))
        s.state(0,22,'controlled','blue-09')
        s.state(22,23.2,'in_flight',team='blue',points=('blue-09','amber-01'))
        s.state(23.2,30,'controlled','amber-01')
        s.state(30,34,'in_flight',team='amber',points=('amber-01','amber-04'))
        s.state(34,90,'controlled','amber-04')
        s.event(23.2,'possession_changed','amber','amber-01',
                {'incident_id':'i01','previous_team_id':'blue','new_team_id':'amber',
                 'controlling_player_id':'amber-01','reason':'observed control'})
        s.pass_event(30,34,'amber-01','amber-04','p01')
    s.event(22,'shot_started','blue','blue-09',{'shot_id':'s01'})
    s.event(23.2,'shot_resolved','blue','blue-09',
            {'shot_id':'s01','outcome':'blocked' if blocked else 'saved'})
    return s


def goal(cancelled=False):
    s = Scene('d04', initial_score={'blue':1,'amber':1})
    s.shape = [(0,66,45), (20,77,40), (33,95,34), (44,52.5,34), (65,35,48), (90,32,43)]
    s.path('blue-10', (0,66,45), (16,77,40), (20,77,40), (50,67,44), (90,58,40))
    s.path('blue-09', (0,79,33), (22,84,34), (28,88,34), (32,88,34), (60,64,35), (90,54,32))
    s.path('amber-11', (0,43,28), (33,48,32), (44,52.5,34), (52,44,34), (60,44,34), (90,40,30))
    s.path('amber-08', (0,50,49), (33,53,48), (62,35,48), (90,32,43))
    s.state(0,20,'controlled','blue-10')
    s.state(20,22,'in_flight',team='blue',points=('blue-10','blue-09'))
    s.state(22,32,'controlled','blue-09')
    s.state(32,33,'in_flight',team='blue',points=('blue-09',(105,34)))
    s.state(33,44,'out_of_play',points=((105,34),'amber-11'))
    s.state(44,60,'controlled','amber-11')
    s.state(60,62,'in_flight',team='amber',points=('amber-11','amber-08'))
    s.state(62,90,'controlled','amber-08')
    s.pass_event(20,22,'blue-10','blue-09','p01')
    s.pass_event(60,62,'amber-11','amber-08','p02')
    s.event(32,'shot_started','blue','blue-09',{'shot_id':'s01'})
    s.event(33,'shot_resolved','blue','blue-09',{'shot_id':'s01','outcome':'goal'})
    s.event(33,'goal_status_changed','blue',None,
            {'goal_id':'g01','status':'pending','scorer_id':'blue-09','shot_id':'s01'},key='g01a',delay=1)
    s.event(33,'goal_status_changed','blue',None,
            {'goal_id':'g01','status':'confirmed','scorer_id':'blue-09','shot_id':'s01'},
            key='g01b',delay=3,revision=2,supersedes='g01a')
    if cancelled:
        s.event(33,'goal_status_changed','blue',None,
                {'goal_id':'g01','status':'cancelled','scorer_id':None,'shot_id':'s01'},
                key='g01c',delay=19,revision=3,supersedes='g01b')
    s.event(44,'possession_changed','amber','amber-11',
            {'incident_id':'i01','previous_team_id':None,'new_team_id':'amber',
             'controlling_player_id':'amber-11','reason':'restart'})
    return s


def quiet():
    s = Scene('d05')
    s.shape = [(0,30,42), (20,30,42), (40,23,36), (60,14,34), (90,32,48)]
    s.path('blue-04', (0,30,42), (20,30,42), (50,35,36), (90,40,38))
    s.path('blue-02', (0,23,36), (22,23,36), (40,23,36), (70,30,28), (90,34,26))
    s.path('blue-01', (0,8,34), (30,12,34), (42,14,34), (60,14,34), (90,8,34))
    s.path('blue-05', (0,27,51), (62,24,48), (90,32,48))
    s.state(0,20,'controlled','blue-04')
    s.state(20,22,'in_flight',team='blue',points=('blue-04','blue-02'))
    s.state(22,40,'controlled','blue-02')
    s.state(40,42,'in_flight',team='blue',points=('blue-02','blue-01'))
    s.state(42,60,'controlled','blue-01')
    s.state(60,62,'in_flight',team='blue',points=('blue-01','blue-05'))
    s.state(62,90,'controlled','blue-05')
    s.pass_event(20,22,'blue-04','blue-02','p01')
    s.pass_event(40,42,'blue-02','blue-01','p02')
    s.pass_event(60,62,'blue-01','blue-05','p03')
    return s


def competing():
    s = Scene('d06')
    s.shape = [(0,31,45), (14,36,40), (20,68,37), (34,85,47), (46,99,34), (70,78,20), (90,67,25)]
    s.path('blue-07', (0,31,45), (10,36,40), (14,36,40), (40,45,46), (90,53,40))
    s.path('blue-09', (0,52,33), (16,61,37), (19,68,37), (23,62,36), (26,68,37), (28,68,37), (60,66,31), (90,55,35))
    s.path('blue-10', (0,68,49), (18.9,67.99753,37), (22,72,40), (26,68,37), (30,77,50), (33,78,48), (60,72,40), (90,62,42))
    s.path('amber-06', (0,48,29), (10,38,39), (14,38,39), (35,54,30), (90,68,20))
    s.path('amber-07', (0,51,50), (10,40,43), (14,40,43), (40,65,30), (60,80,15), (90,67,25))
    s.path('amber-08', (0,54,54), (10,44,49), (14,44,49), (40,65,49), (90,61,47))
    s.path('amber-01', (0,99,34), (30,100,38), (34.2,100,38), (46,99,34), (58,99,34), (90,97,34))
    s.state(0,14,'controlled','blue-07')
    s.state(14,16,'in_flight',team='blue',points=('blue-07','blue-09'))
    s.state(16,18.9,'controlled','blue-09')
    s.state(18.9,26,'controlled','blue-10')
    s.state(26,28,'controlled','blue-09')
    s.state(28,30,'in_flight',team='blue',points=('blue-09','blue-10'))
    s.state(30,33,'controlled','blue-10')
    s.state(33,34.2,'in_flight',team='blue',points=('blue-10',(105,45)))
    s.state(34.2,46,'out_of_play',points=((105,45),'amber-01'))
    s.state(46,58,'controlled','amber-01')
    s.state(58,60,'in_flight',team='amber',points=('amber-01','amber-07'))
    s.state(60,90,'controlled','amber-07')
    s.pass_event(14,16,'blue-07','blue-09','p01')
    s.pass_event(28,30,'blue-09','blue-10','p02')
    s.pass_event(58,60,'amber-01','amber-07','p03')
    s.event(33,'shot_started','blue','blue-10',{'shot_id':'s01'})
    s.event(34.2,'shot_resolved','blue','blue-10',{'shot_id':'s01','outcome':'off_target'})
    s.event(46,'possession_changed','amber','amber-01',
            {'incident_id':'i01','previous_team_id':None,'new_team_id':'amber',
             'controlling_player_id':'amber-01','reason':'restart'})
    return s


BUILDERS = (support, interception, shot, goal, quiet, competing)


def scene_for(parent, paired=False):
    scene = BUILDERS[parent-1](paired) if parent in (3,4) else BUILDERS[parent-1]()
    return deepcopy(scene)
