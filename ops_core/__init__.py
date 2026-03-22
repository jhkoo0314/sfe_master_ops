"""
Sales Data OS Validation / Orchestration implementation package.

`ops_core` is not the top-level system engine.
It contains the current package boundary for:
- Validation Layer (OPS) API endpoints
- Result Asset evaluation orchestration
- runtime execution coordination

Long term, this responsibility is expected to converge toward a
`modules/validation`-style package after safe refactoring.
"""
