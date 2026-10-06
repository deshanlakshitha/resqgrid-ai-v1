"""Tests for the Hungarian assignment optimizer."""

import itertools
import random
from types import SimpleNamespace

from app.allocation.optimizer import (
    greedy_assignment,
    hungarian_min_cost,
    optimize_assignments,
)


def brute_force_min_cost(matrix: list[list[float]]) -> float:
    """Reference solver: try every assignment of the smaller side to the larger."""
    n, m = len(matrix), len(matrix[0])
    best = float("inf")
    if n <= m:
        for cols in itertools.permutations(range(m), n):
            best = min(best, sum(matrix[i][c] for i, c in enumerate(cols)))
    else:
        for rows in itertools.combinations(range(n), m):
            for cols in itertools.permutations(range(m), m):
                best = min(best, sum(matrix[r][c] for r, c in zip(rows, cols, strict=True)))
    return best


def matching_cost(matrix: list[list[float]], pairs: list[tuple[int, int]]) -> float:
    return sum(matrix[i][j] for i, j in pairs)


class TestHungarian:
    def test_single_element(self):
        assert hungarian_min_cost([[5.0]]) == [(0, 0)]

    def test_prefers_cheapest(self):
        pairs = hungarian_min_cost([[3.0, 1.0]])
        assert pairs == [(0, 1)]

    def test_matches_known_optimum(self):
        matrix = [[1.0, 2.0], [1.0, 100.0]]
        # Greedy row-order picks (0,0)+(1,1)=101; optimal is (0,1)+(1,0)=3.
        pairs = hungarian_min_cost(matrix)
        assert matching_cost(matrix, pairs) == 3.0

    def test_rectangular_more_rows_than_cols(self):
        matrix = [[1.0, 2.0], [2.0, 1.0], [5.0, 5.0]]
        pairs = hungarian_min_cost(matrix)
        assert len(pairs) == 2  # smaller side fully matched
        assert matching_cost(matrix, pairs) == 2.0  # (0,0)+(1,1)

    def test_rectangular_more_cols_than_rows(self):
        matrix = [[4.0, 1.0, 3.0], [2.0, 0.0, 5.0]]
        pairs = hungarian_min_cost(matrix)
        assert len(pairs) == 2
        assert matching_cost(matrix, pairs) == 3.0  # (0,1)=1 + (1,0)=2
        assert matching_cost(matrix, pairs) == brute_force_min_cost(matrix)

    def test_matches_brute_force_random_square(self):
        rng = random.Random(42)
        for size in range(2, 7):
            for _ in range(25):
                matrix = [[rng.randint(0, 50) for _ in range(size)] for _ in range(size)]
                pairs = hungarian_min_cost(matrix)
                assert len(pairs) == size
                assert matching_cost(matrix, pairs) == brute_force_min_cost(matrix)

    def test_matches_brute_force_random_rectangular(self):
        rng = random.Random(7)
        for n, m in [(2, 5), (4, 6), (5, 3), (6, 2)]:
            for _ in range(25):
                matrix = [[rng.randint(0, 50) for _ in range(m)] for _ in range(n)]
                pairs = hungarian_min_cost(matrix)
                assert len(pairs) == min(n, m)
                assert matching_cost(matrix, pairs) == brute_force_min_cost(matrix)


class TestGreedyBaseline:
    def test_greedy_is_suboptimal_on_trap_matrix(self):
        matrix = [[1.0, 2.0], [1.0, 100.0]]
        greedy = greedy_assignment(matrix)
        optimal = hungarian_min_cost(matrix)
        assert matching_cost(matrix, greedy) == 101.0
        assert matching_cost(matrix, optimal) == 3.0


def make_incident(rid, lat, lon, itype, title):
    return SimpleNamespace(
        id=rid, title=title, latitude=lat, longitude=lon,
        incident_type=SimpleNamespace(value=itype),
    )


def make_resource(rid, name, rtype, lat, lon, max_range=None):
    return SimpleNamespace(
        id=rid, name=name, resource_type=SimpleNamespace(value=rtype),
        latitude=lat, longitude=lon, max_range_km=max_range,
    )


class TestOptimizeAssignments:
    def test_empty_input(self):
        plan = optimize_assignments([], [], [])
        assert plan["assignments"] == []
        assert plan["savings_pct"] == 0.0

    def test_no_resources_reports_unassigned(self):
        incidents = [make_incident("i1", 6.9, 79.9, "fire", "Fire")]
        plan = optimize_assignments(incidents, [], [])
        assert plan["unassigned_incident_ids"] == ["i1"]

    def test_prefers_closest_compatible(self):
        incidents = [
            make_incident("i1", 6.90, 79.86, "medical", "Heart attack"),
            make_incident("i2", 6.92, 79.90, "medical", "Car crash"),
        ]
        near = make_resource("r1", "City Ambulance", "ambulance", 6.905, 79.865)
        far = make_resource("r2", "Rural Ambulance", "ambulance", 7.40, 80.20)
        plan = optimize_assignments(incidents, [near, far], [])
        assert len(plan["assignments"]) == 2
        by_incident = {a["incident_id"]: a for a in plan["assignments"]}
        # Hungarian must not let both incidents grab the same resource.
        assert {a["resource_id"] for a in plan["assignments"]} == {"r1", "r2"}
        assert by_incident["i1"]["distance_km"] < by_incident["i2"]["distance_km"]

    def test_hard_constraint_violation_is_unassigned(self):
        incidents = [make_incident("i1", 6.90, 79.86, "fire", "Fire far away")]
        short_range = make_resource("r1", "Small truck", "fire_truck", 6.0, 79.0, max_range=10.0)
        plan = optimize_assignments(incidents, [short_range], [])
        assert plan["assignments"] == []
        assert plan["unassigned_incident_ids"] == ["i1"]

    def test_type_mismatch_penalty_applied(self):
        incidents = [make_incident("i1", 6.90, 79.86, "medical", "Injury")]
        boat = make_resource("r1", "Boat", "rescue_boat", 6.905, 79.865)
        ambulance = make_resource("r2", "Ambulance", "ambulance", 6.91, 79.87)
        plan = optimize_assignments(incidents, [boat, ambulance], [])
        assert plan["assignments"][0]["resource_id"] == "r2"

    def test_savings_nonnegative_vs_greedy(self):
        incidents = [
            make_incident(f"i{k}", 6.9 + k * 0.01, 79.86, "fire", f"Fire {k}")
            for k in range(3)
        ]
        resources = [
            make_resource(f"r{k}", f"Truck {k}", "fire_truck", 6.9 + k * 0.02, 79.86)
            for k in range(3)
        ]
        plan = optimize_assignments(incidents, resources, [])
        assert plan["savings_km"] >= 0
        assert plan["greedy_cost_km"] >= plan["total_cost_km"]
        assert len(plan["assignments"]) == 3

    def test_plan_is_pure_no_mutation(self):
        incidents = [make_incident("i1", 6.90, 79.86, "fire", "Fire")]
        resources = [make_resource("r1", "Truck", "fire_truck", 6.905, 79.865)]
        optimize_assignments(incidents, resources, [])
        assert not hasattr(incidents[0], "status")  # stubs untouched
