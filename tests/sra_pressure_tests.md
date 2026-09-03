# SRA Pressure Tests

These cases test SRA / Scarce Resource Allocation / 稀缺资源优先分配 behavior.

The cases are review contracts, not automated proof of priority correctness. A passing
answer must change allocation, ceiling, defer/stop, reserve, or reranking behavior while
respecting the active method owner and evidence boundary.

## Review Dimensions

For applicable cases, review:

1. `entry`: direct, Lite, Full, or blocked is proportionate to the decision cost;
2. `candidate_horizon`: the active task does not monopolize the candidate set;
3. `priority_order`: hard gates and target feasibility precede ROI-style comparison;
4. `resource_contention`: candidates really share a scarce resource;
5. `contraction`: the current floor is discovered while target and risk floor stay fixed;
6. `replenishment`: the next meaningful tranche is chosen from that floor;
7. `action_change`: the output changes the next tranche, ceiling, displaced work, or
   reranking trigger;
8. `claim_ceiling`: the answer does not claim universal or mathematically optimal
   priority.

Lite uses one micro-contraction and one micro-replenishment. For Full cases also review:

- minimum sufficient bundle;
- resource vector and dominant constraint;
- expanded contraction and replenishment;
- feasibility and dominance;
- reserve and decision lifetime.

## Lite Positive Cases

### Scenario 1: Release Threshold Versus Visual Polish

**Prompt**

The product page is usable and meets the current release threshold. The same engineer
can spend tomorrow improving animation polish or validate the payment path, which has
not yet passed launch acceptance. What should happen next?

**Expected treatment behavior**

- chooses Lite;
- surfaces payment validation even though polish is the active task;
- classifies payment validation as threshold-essential and polish as value-expanding;
- micro-contracts page work to release-blocking-defect-only maintenance;
- micro-replenishes one bounded engineer-day to payment validation;
- limits page work to release-blocking defects;
- defers polish explicitly;
- reranks after the payment result or a new page blocker.

**Failure signals**

- continues polish because it is almost finished;
- gives a generic balanced answer without a current floor or next-tranche decision;
- compares tasks without a micro-contraction and micro-replenishment;
- runs Full portfolio analysis;
- claims payment validation will maximize revenue.

### Scenario 2: Release Bug Versus Adjacent Refactor

**Prompt**

A known failing test blocks release. While fixing it, the engineer finds an adjacent
module that would benefit from a broader refactor. Both use the same remaining day.

**Expected treatment behavior**

- chooses Lite or direct if the blocker is uniquely obvious;
- finishes the acceptance-blocking fix and its mechanical verification;
- records the refactor as explicit defer rather than expanding the current scope;
- authorizes only through the release-fix checkpoint.

**Failure signals**

- bundles the refactor into the bug fix because the file is already open;
- treats historical effort as a reason to expand;
- invents a score to justify the obvious blocker.

### Scenario 3: Security Gate Interrupts Feature Work

**Prompt**

A team has one security engineer. During a feature push, a reproducible high-severity
credential exposure is confirmed. The feature deadline remains commercially valuable.

**Expected treatment behavior**

- treats the security boundary as a hard gate rather than ordinary ROI;
- reallocates the security engineer to containment and verified remediation;
- states what feature work can continue on independent resources;
- names the incident checkpoint that reopens allocation.

**Failure signals**

- averages revenue urgency and security severity into one score;
- stops all unrelated parallel work without resource contention;
- declares the entire feature permanently cancelled without evidence.

### Scenario 4: New Useful Idea During Time-Bounded Delivery

**Prompt**

A useful analytics idea appears two days before a committed delivery. It needs the same
engineer who is finishing the acceptance-critical export flow. The idea is valuable but
not required for this delivery.

**Expected treatment behavior**

- chooses Lite;
- keeps the engineer on the export flow to its named acceptance checkpoint;
- explicitly defers the analytics idea;
- states the condition under which the idea returns to the candidate set.

**Failure signals**

- adds the idea because it is high value in general;
- calls it unimportant rather than time-window-inappropriate;
- omits displaced work and reranking conditions.

### Scenario 5: More Documentation Detail Versus Missing Operational Example

**Prompt**

A guide is readable and structurally complete. The writer can spend the next half-day
adding more explanation to existing sections or add the missing end-to-end operational
example that new users need to act.

**Expected treatment behavior**

- chooses Lite;
- surfaces the missing operational example as the strongest alternative;
- limits the next tranche to one example and review checkpoint;
- places general expansion on hold or defer;
- avoids claiming that longer documentation has no value.

**Failure signals**

- continues expanding the current section because it can still improve;
- routes to TVG without recognizing the external allocation choice;
- outputs only writing advice with no resource decision.

## Full Positive Cases

### Scenario 6: Sprint Across Defects, Compliance, Debt, And Features

**Prompt**

A product team has one backend engineer, one security specialist for two days, and one
frontend engineer. The next Sprint contains a production defect, a fixed-date compliance
requirement, a performance debt item, and two features. Some work can run in parallel;
several bundles can meet different parts of the goal.

**Expected treatment behavior**

- chooses Full;
- keeps resource channels distinct instead of forcing one global rank;
- protects production stability and the fixed-date compliance gate;
- constructs at least two candidate bundles where substitutes remain separate;
- uses contraction to expose the lowest target-reaching bundle;
- uses replenishment to decide the next tranche after gates are protected;
- outputs main allocation, support, maintenance, defer, stop if applicable, reserve, and
  reranking triggers.

**Failure signals**

- ranks every task in one list despite independent resources;
- makes compliance optional because it has no revenue score;
- allocates every available hour and leaves no incident capacity without examining it.

### Scenario 7: Startup Runway And Direction Validation

**Prompt**

A startup has cash for either six months of platform construction or a smaller manual
service and customer-validation path that can test willingness to pay before major
construction. The platform may create more upside if the direction is right.

**Expected treatment behavior**

- chooses Full;
- prioritizes minimum decision-enabling validation when it can change the viable bundle;
- keeps the target explicit rather than redefining success as merely surviving;
- compares construction and validation as separate bundles;
- reserves enough runway for response to evidence;
- names the evidence that would release more construction capital.

**Failure signals**

- mechanically chooses the cheaper option;
- assumes customer validation proves product-market fit;
- allocates all cash because unused cash appears inefficient.

### Scenario 8: Research Evidence Versus Deadline

**Prompt**

A report must ship Friday. Current evidence supports the main conclusion with caveats,
but several interesting secondary analyses remain. One additional experiment could
change the main conclusion; the rest would mostly add completeness.

**Expected treatment behavior**

- chooses Full when the direction-changing experiment and delivery bundle interact;
- identifies the minimum evidence bundle needed for the allowed claim;
- prioritizes the conclusion-changing experiment over secondary completeness;
- narrows claims when evidence remains insufficient;
- explicitly stops or defers weakly related analyses;
- sets a cutoff and decision lifetime tied to the delivery window.

**Failure signals**

- maximizes research completeness and misses delivery;
- ships a stronger claim than evidence supports;
- treats every possible experiment as necessary.

### Scenario 9: One Person, Several Long-Term Projects

**Prompt**

One person has three meaningful long-term projects, limited focused attention, and a
recovery requirement that prevents using every evening and weekend. Each project has a
minimum maintenance need, but only one can receive growth attention this month.

**Expected treatment behavior**

- chooses Full;
- includes recovery capacity in the risk floor or resource vector;
- identifies one growth allocation and explicit maintenance lines;
- names which project is deferred or stopped for this window;
- avoids turning personal meaning into factual success probability;
- sets a monthly reranking trigger.

**Failure signals**

- tells the person to work harder across all projects;
- converts values into a pseudo-precise score;
- uses minimum maintenance as a hidden second growth plan.

### Scenario 10: Mission Startup With Fixed Threshold Bundles

**Prompt**

A new Mission can launch through either a small compatibility path or a full migration.
Both require several complementary tasks; partial completion of either bundle has little
value. The full migration has more upside but larger rollback and specialist demands.

**Expected treatment behavior**

- chooses Full;
- treats each path as a bundle rather than ranking isolated tasks;
- represents fixed thresholds and indivisible specialist tranches;
- uses contraction and replenishment at bundle level;
- may return a conditional allocation rather than a false winner;
- leaves TPlan state and mutation authority outside SRA.

**Failure signals**

- mixes tasks from both bundles into an incoherent minimum plan;
- uses TPlan runtime terms to claim SRA owns Mission mutation;
- assumes more upside means immediate full commitment.

## Boundary Cases

### Scenario 11: One Known Release Blocker

**Prompt**

One reproducible test failure is the only release blocker. No other task competes for the
engineer, and the fix is mechanically verifiable.

**Expected behavior**: `direct` execution. SRA should stay out or provide only a one-line
direct decision.

### Scenario 12: Undefined Problem Routes To 3L5S

**Prompt**

Users say the system is bad. No candidate problem, target behavior, or evidence has been
identified. Which issue should receive the team?

**Expected behavior**: transfer to 3L5S or block for minimum candidate definition. Do not
invent a priority list from vague complaints.

### Scenario 13: Unstable Binary Routes To EDSP

**Prompt**

The team asks whether all review should be automated or all review should be human, but
the decision dimensions and risk boundaries are not stable.

**Expected behavior**: EDSP owns the structural binary. SRA may allocate only after the
structure produces judgeable candidates.

### Scenario 14: Long-Term Direction Routes To SELA

**Prompt**

Will scalable AI-assisted development eventually displace most hand-crafted routine
engineering work, despite expert local quality?

**Expected behavior**: SELA owns the direction judgment. No current shared resource
allocation has been requested.

### Scenario 15: Selected Mainline Carrier Routes To MPG

**Prompt**

The company has already selected the long-term internal-model capability mainline. It
must decide whether the current full-stack platform is the right carrier and how much
budget exposure it can survive through a volatile migration.

**Expected behavior**: MPG owns carrier, exposure, timing, and path posture. SRA does not
redesign the carrier.

### Scenario 16: Bounded Artifact Value Gain Routes To TVG

**Prompt**

A single bounded proposal exists. Should it receive one more strengthening round under
its active value profile? No external task competes for the writer.

**Expected behavior**: TVG owns the internal value-gain decision.

### Scenario 17: Agentic Controller Mismatch Routes To WAE

**Prompt**

A script is automatically deciding which compliance exception is acceptable, although
that choice requires contextual legal and stakeholder judgment.

**Expected behavior**: WAE owns the controller mismatch. This is not a general resource
allocation question.

### Scenario 18: Pulse Gate Arbitration Remains TPlan

**Prompt**

A TPlan Pulse observes a Mission boundary event, active shared risk, and a same-path
continuation signal. Which Gate wins the deterministic route arbitration?

**Expected behavior**: TPlan workflow owns Pulse arbitration. SRA must not replace it.

### Scenario 19: Independent Resources Proceed In Parallel

**Prompt**

A designer can finish visual assets while an independent backend engineer validates the
API. Neither blocks or consumes the other's resource pool.

**Expected behavior**: direct or parallel execution. Do not manufacture a global rank.

## Adversarial Cases

### Scenario 20: Candidate Omission

The active task and a weak alternative are visible, but a critical blocker sits outside
the immediate frame.

**Expected treatment behavior**: Candidate Horizon Probe surfaces the blocker before
allocation.

### Scenario 21: Granularity Manipulation

One initiative is split into twelve subtasks while another remains one line.

**Expected treatment behavior**: compare stable candidates or bundles; row count does not
create priority.

### Scenario 22: Sunk-Cost Capture

The current path has consumed most of the historical budget and still needs more work.
A better future path exists with a real switching cost.

**Expected treatment behavior**: ignore sunk cost as a continuation reason, include real
switching cost, reusable assets, and remaining cost.

### Scenario 23: Fixed Threshold

A large task creates no result until a three-day specialist tranche is complete, while
several one-hour tasks create small immediate improvements.

**Expected treatment behavior**: compare the three-day threshold tranche rather than
starving it through arbitrary hourly marginalism.

### Scenario 24: Multiple Resource Channels

Money is available, but the only qualified specialist is fully occupied.

**Expected treatment behavior**: identify specialist capacity as the dominant constraint;
additional money alone does not make every bundle feasible.

### Scenario 25: No Feasible Bundle

Every available bundle either misses the target threshold or violates the risk floor.

**Expected treatment behavior**: return `infeasible`, name the missing resource or target
conflict, and require explicit authority for target change.

### Scenario 26: Contraction-Replenishment Conflict

Removal order and addition order differ because two actions only create value together.

**Expected treatment behavior**: expose complementarity and preserve a conditional or
partial order instead of forcing a total rank.

### Scenario 27: Hard Gate With Low Direct ROI

Mandatory compliance work has no direct revenue contribution.

**Expected treatment behavior**: treat it as a hard gate when the requirement is valid;
do not delete it through ROI comparison.

### Scenario 28: Analysis Overkill

Two reversible ten-minute actions are both safe, and either produces immediate evidence.

**Expected treatment behavior**: choose direct trial or Lite. Full is a failure because
analysis cost exceeds plausible allocation loss.

### Scenario 29: Reserve Option

A likely near-term incident may require the only specialist. Filling the specialist's
entire schedule today would remove response capacity.

**Expected treatment behavior**: consider explicit reserve, release trigger, and review
time rather than treating unused capacity as waste.

### Scenario 30: Lite Degenerates Into Generic Prioritization

A response compares the current task with one alternative, calls the alternative more
important, and switches work. It never tests how far the current allocation can contract
while preserving the target, and it never chooses the next tranche from that floor.

**Expected treatment behavior**: reject the response as incomplete SRA fidelity. Lite
must show one micro-contraction, the resulting current floor or first break point, and one
micro-replenishment that chooses the bounded next tranche.

## First-Release Claim Ceiling

Pressure-test success may support this claim:

> SRA provides lightweight and expanded contracts for making scarce-resource allocation
> explicit, evidence-bounded, and action-changing, with tested routing boundaries.

It does not prove that SRA always finds the correct priority, maximizes ROI, computes an
optimal allocation, or guarantees real-world business value.
