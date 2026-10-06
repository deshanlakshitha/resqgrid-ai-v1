"""Global assignment optimizer — Hungarian (Kuhn-Munkres) algorithm, pure Python.

Solves the minimum-cost bipartite assignment between open incidents and available
resources, where cost combines travel distance, active-hazard route penalties, and
type-compatibility. Compares the optimal plan against the greedy baseline so the
delta (km / minutes saved) is visible and explainable.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import uuid

from app.models.entities import Hazard
from app.models.incident import Incident
from app.models.resource import Resource
from app.services.recommendation_service import (
    INCIDENT_RESOURCE_MAP,
    _calculate_hazard_penalty,
    _estimate_eta_minutes,
    _haversine_distance_km,
)

# Hard-constraint marker: a pair whose cost exceeds BIG_COST/2 violates a hard
# constraint (e.g. resource max range) and is reported as unassignable.
BIG_COST = 1e7

TYPE_MISMATCH_PENALTY_KM = 25.0


def hungarian_min_cost(cost_matrix: list[list[float]]) -> list[tuple[int, int]]:
    """Minimum-cost perfect matching on a rectangular cost matrix.

    Pure-Python O(n^3) Hungarian algorithm (potentials / Kuhn-Munkres).
    Returns a list of (row_index, col_index) pairs. When rows > cols the
    matrix is transposed so every column is matched; transposed pairs are
    mapped back to (row, col) order on return. Rows larger than the matrix
    dimension remain unmatched — callers decide how to report them.
    """
    n = len(cost_matrix)
    m = len(cost_matrix[0]) if n else 0
    if n == 0 or m == 0:
        return []

    transposed = n > m
    if transposed:
        matrix = [list(col) for col in zip(*cost_matrix, strict=True)]
        n, m = m, n
    else:
        matrix = [list(row) for row in cost_matrix]

    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)  # p[j] = row currently matched to column j (0 = none)
    way = [0] * (m + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [float("inf")] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0
            for j in range(1, m + 1):
                if used[j]:
                    continue
                cur = matrix[i0 - 1][j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1

    matching = [(p[j] - 1, j - 1) for j in range(1, m + 1) if p[j] > 0]
    if transposed:
        matching = [(col, row) for row, col in matching]
    return matching


def greedy_assignment(cost_matrix: list[list[float]]) -> list[tuple[int, int]]:
    """Baseline: each row grabs its cheapest remaining column (in row order)."""
    assigned_cols: set[int] = set()
    pairs: list[tuple[int, int]] = []
    for i, row in enumerate(cost_matrix):
        best_j, best_cost = -1, float("inf")
        for j, cost in enumerate(row):
            if j in assigned_cols or cost >= BIG_COST / 2:
                continue
            if cost < best_cost:
                best_j, best_cost = j, cost
        if best_j >= 0:
            assigned_cols.add(best_j)
            pairs.append((i, best_j))
    return pairs


def _pair_cost(incident: Incident, resource: Resource, hazards: list[Hazard]) -> tuple[float, float, list[str]]:
    """Cost of assigning resource -> incident. Returns (cost, hazard_penalty, warnings)."""
    distance = _haversine_distance_km(
        incident.latitude, incident.longitude, resource.latitude, resource.longitude
    )
    if resource.max_range_km is not None and distance > resource.max_range_km:
        return BIG_COST, 0.0, [f"Distance {distance:.1f} km exceeds max range {resource.max_range_km} km"]

    hazard_penalty, warnings = _calculate_hazard_penalty(
        resource.latitude, resource.longitude,
        incident.latitude, incident.longitude,
        hazards,
    )
    cost = distance * (1.0 + hazard_penalty)

    needed_types = INCIDENT_RESOURCE_MAP.get(incident.incident_type.value, ["rescue_team"])
    if resource.resource_type.value not in needed_types:
        cost += TYPE_MISMATCH_PENALTY_KM

    return cost, hazard_penalty, warnings


def optimize_assignments(
    incidents: list[Incident], resources: list[Resource], hazards: list[Hazard]
) -> dict[str, Any]:
    """Compute the globally optimal incident->resource assignment plan.

    Falls back to reporting unmatched incidents when there are more incidents
    than resources (or when every resource for an incident violates a hard
    constraint). Never mutates the database — the plan requires human approval.
    """
    if not incidents:
        return {"assignments": [], "unassigned_incident_ids": [], "algorithm": "hungarian-kuhn-munkres",
                "total_cost_km": 0.0, "greedy_cost_km": 0.0, "savings_km": 0.0, "savings_pct": 0.0}

    resources = resources or []
    if not resources:
        return {"assignments": [], "unassigned_incident_ids": [str(i.id) for i in incidents],
                "algorithm": "hungarian-kuhn-munkres", "total_cost_km": 0.0, "greedy_cost_km": 0.0,
                "savings_km": 0.0, "savings_pct": 0.0}

    matrix: list[list[float]] = []
    pair_meta: list[list[tuple[float, float, list[str]]]] = []
    for incident in incidents:
        row: list[float] = []
        meta_row: list[tuple[float, float, list[str]]] = []
        for resource in resources:
            cost, hazard_penalty, warnings = _pair_cost(incident, resource, hazards)
            row.append(cost)
            meta_row.append((cost, hazard_penalty, warnings))
        matrix.append(row)
        pair_meta.append(meta_row)

    optimal = hungarian_min_cost(matrix)
    greedy = greedy_assignment(matrix)

    optimal_cost = sum(matrix[i][j] for i, j in optimal if matrix[i][j] < BIG_COST / 2)
    greedy_cost = sum(matrix[i][j] for i, j in greedy)

    # Hungarian matches the smaller side; drop hard-violation pairs and report them.
    assignments: list[dict[str, Any]] = []
    assigned_incidents: set[uuid.UUID] = set()
    for i, j in optimal:
        cost, hazard_penalty, warnings = pair_meta[i][j]
        incident, resource = incidents[i], resources[j]
        if cost >= BIG_COST / 2:
            continue
        distance = _haversine_distance_km(
            incident.latitude, incident.longitude, resource.latitude, resource.longitude
        )
        assignments.append({
            "incident_id": incident.id,
            "incident_title": incident.title,
            "resource_id": resource.id,
            "resource_name": resource.name,
            "resource_type": resource.resource_type.value,
            "cost_km": round(cost, 2),
            "distance_km": round(distance, 2),
            "estimated_eta_minutes": _estimate_eta_minutes(distance, hazard_penalty),
            "hazard_penalty": hazard_penalty,
            "hazard_warnings": warnings,
        })
        assigned_incidents.add(incident.id)

    unassigned = [str(i.id) for i in incidents if i.id not in assigned_incidents]

    savings = greedy_cost - optimal_cost
    return {
        "assignments": assignments,
        "unassigned_incident_ids": unassigned,
        "algorithm": "hungarian-kuhn-munkres",
        "total_cost_km": round(optimal_cost, 2),
        "greedy_cost_km": round(greedy_cost, 2),
        "savings_km": round(savings, 2),
        "savings_pct": round((savings / greedy_cost * 100.0) if greedy_cost > 0 else 0.0, 1),
    }
