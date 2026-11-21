"""TICKET-02 restaurant core and interface to the day coordinator."""
import copy
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState, InputPlayer
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.quan import QuanSim


def idle(interact=False):
    return InputState((0, 0), {}, {'interact'} if interact else set())


class QuanPhase2(unittest.TestCase):
    def setUp(self):
        self.t = load_contract()['tuning']

    def sim(self, scenario=None, **kwargs):
        return QuanSim(self.t, {'random_customers': False, **(scenario or {})},
                       Streams(1), IdAllocator(), **kwargs)

    def customer(self, ident='C1', table='T1', dish='ca_loc_nuong_trui', **kw):
        return dict(id=ident, table_id=table, dish_id=dish, **kw)

    def test_six_dishes_cook_pick_serve_and_pay(self):
        self.assertEqual(len(self.t['menu']), 6)
        self.assertEqual([s['id'] for s in self.t['quan']['stoves']], ['B1', 'B2'])
        self.assertEqual(len(self.t['quan']['tables']), 4)
        for dish, spec in self.t['menu'].items():
            with self.subTest(dish=dish):
                s = self.sim({'stock': spec['recipe'], 'player': {'pos': [2, 8]},
                              'customers': [self.customer(dish=dish)]})
                self.assertEqual(s.step(idle(True))[0][0], 'cook_started')
                self.assertFalse(s.snapshot()['stock'])
                for _ in range(round(spec['cook_s'] * 60) - 1):
                    s.step(idle())
                self.assertEqual([n for n, _ in s.step(idle(True))], ['dish_ready', 'dish_picked'])
                s.pos = [9, 2]
                event = s.step(idle(True))[0]
                self.assertEqual(event[0], 'served')
                self.assertEqual(event[1]['base_price'], spec['price'])
                for _ in range(600):
                    s.step(idle())
                self.assertEqual(s.earned, spec['price'] + event[1]['tip'])

    def test_two_stoves_assign_distinct_oldest_orders(self):
        s = self.sim({'stock': {'ca_loc': 2}, 'player': {'pos': [2, 8]},
                      'customers': [self.customer('C2', 'T2'), self.customer()]})
        self.assertEqual(s.step(idle(True))[0][1]['order_id'], 'C1')
        s.pos = [5, 8]
        self.assertEqual(s.step(idle(True))[0][1]['order_id'], 'C2')
        self.assertEqual([b['state'] for b in s.stoves], ['cooking', 'cooking'])
        self.assertFalse(s.snapshot()['stock'])

    def test_four_tables_fill_then_full_table_skips_arrival(self):
        s = self.sim({'random_customers': True, 'stock': {'ca_loc': 8}})
        # Keep patrons seated while checking the fifth arrival slot.
        for _ in range(3720):
            for c in s.customers:
                c['patience_ticks_left'] = 10000
            events = s.step(idle())
        self.assertEqual([c['table_id'] for c in s.customers], ['T1', 'T2', 'T3', 'T4'])
        self.assertEqual(events, [])

    def test_day_filter_allows_repeat_orders_beyond_planned_count(self):
        dish = 'ca_keo_nuong'
        s = self.sim({'random_customers': True}, inventory={'ca_keo': 4, 'ca_loc': 5},
                     day_plan={'dishes': {dish: 1}}, money=100, earned=200, reputation=4)
        for _ in range(1020):
            s.step(idle())
        self.assertEqual([c['dish_id'] for c in s.customers], [dish, dish])
        self.assertEqual((s.money, s.earned, s.shift_earned, s.reputation), (100, 200, 0, 4))

    def test_day_filter_reports_no_dish_when_only_unplanned_food_is_available(self):
        s = self.sim({'random_customers': True}, inventory={'ca_loc': 5},
                     day_plan={'dishes': {'lau_mam': 1}})
        for _ in range(120):
            events = s.step(idle())
        self.assertEqual(events, [('no_dish', {})])

    def test_day_rejects_fixture_outside_plan_and_wrong_actual_inventory(self):
        for fixture, inventory in (({'customers': [self.customer()]}, {'ca_loc': 1}),
                                   ({'customers': [self.customer(dish='ca_keo_nuong')]}, {}),
                                   ({'stock': {}}, {}), ({'reputation': 3}, {})):
            with self.subTest(fixture=fixture), self.assertRaises(BadInput):
                self.sim(fixture, inventory=inventory, day_plan={'dishes': {'ca_keo_nuong': 1}})

    def test_settlements_are_in_table_order_with_carried_money(self):
        s = self.sim({'time_left_ticks': 1, 'customers': [
            self.customer('C4', 'T4', state='eating', order_status='served',
                          eat_ticks_left=1, base_price=60, tip=12),
            self.customer('C1', 'T1', order_status='unfulfillable')]}, money=50, earned=100)
        events = s.step(idle())
        self.assertEqual([n for n, _ in events], ['customer_left', 'paid', 'quan_end'])
        self.assertEqual((s.money, s.earned, s.shift_earned), (122, 172, 72))
        self.assertFalse(s.customers)

    def test_pause_freezes_timers_and_consumes_interact_edge(self):
        session = Session('quan', self.t, {'stock': {'ca_loc': 1}, 'random_customers': False,
                          'customers': [self.customer()], 'player': {'pos': [2, 8]}}, 1)
        player = InputPlayer([{'tick': 0, 'pause': True, 'interact': True},
                              {'tick': 1, 'pause': False}, {'tick': 2, 'pause': True}])
        before = copy.deepcopy(session.snapshot())
        self.assertEqual(session.step(player.advance(0))[0]['name'], 'paused')
        self.assertEqual(session.snapshot()['state'], 'paused')
        session.step(player.advance(1))
        self.assertEqual(session.snapshot()['time_left_ticks'], before['time_left_ticks'])
        self.assertEqual(session.snapshot()['sim_tick'], 0)
        self.assertEqual([e['name'] for e in session.step(player.advance(2))], ['resumed'])
        self.assertEqual(session.snapshot()['sim_tick'], 1)
        self.assertEqual(session.sim.stoves[0]['state'], 'idle')

    def test_snapshot_and_fixture_do_not_alias(self):
        fixture = {'stock': {'ca_loc': 1}, 'customers': [self.customer()]}
        original = copy.deepcopy(fixture)
        s = self.sim(fixture)
        s.pos = [2, 8]
        s.step(idle(True))
        self.assertEqual(fixture, original)
