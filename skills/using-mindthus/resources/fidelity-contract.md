# using-mindthus Fidelity Contract

This Fidelity Contract defines required judgment moves for the Mindthus router.

required judgment moves:

- perform intervention-boundary judgment before choosing a skill
- do premise calibration when the object, constraints, or goal function are unclear
- separate facts from values, risks, authority, and user preference constraints
- route by active judgment object, not by keyword
- arbitrate conflicts with dominate / defer / degrade / block / stop
- require execution impact from any method use

Allowed exits:

- `not_applicable`: the task is simple, clear, low-risk, and factually sufficient.
- `transfer`: a specific Mindthus method owns the active judgment after routing.
- `challenge premise`: the user's or platform's framing silently changes the object,
  goal, evidence ceiling, or authority boundary.

shape pass is not semantic approval. scripts must not decide semantic truth; router
discipline protects method choice without forcing Mindthus onto simple tasks.
