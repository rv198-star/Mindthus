"""Frozen synthetic fixtures for #207. No production WFF/EKRI/Slidethus inputs.

Owner inputs and receiver questions are deliberately separate. Oracle/reference
material lives in evaluation.py and is never assembled into a model request.
"""
from __future__ import annotations
import copy

F_SOURCE = """P1 product policy, version p1-demo-1 (authoritative for this exercise):
Records contain immutable revisions {id, text}; editing creates a new revision.
current_revision identifies the working revision. approved_revision identifies
the last reviewed revision, or null. Approval applies ONLY to that revision;
creating a draft retains the old approval. Role editor may see/edit working
content and inspect published content; role reader may see only approved content.
No approved revision means a reader sees no content. Editing permission is for
an editor's CURRENT revision only, not historical revisions. Empty or failed
save attempts leave the prior record intact. List, detail and export must tell
the same truth about the revision they actually expose. A working revision can
also be the approved revision. There is no UI or layout preference. All required
policy is contained here; approval-policy changes are outside P2/P3 authority.
"""
F_DRAFT = """P2 draft: show the record's latest content. For editors allow inspection
of working and published views. For readers show published material. List/detail/
export share a record-level green Approved badge whenever approved_revision is
non-null. The working view is editable for editors. Keep components simple.
"""
F_INTERFACE = """Implement a small executable interaction projection, not a whole web app.
Return Python code, without imports, defining:
project(record, role, view='working', surface='detail') -> dict.
record={revisions:[{id:int,text:str}], current_revision:int,
approved_revision:int|null}; role='editor'|'reader';
view='working'|'published'; surface='list'|'detail'|'export'.
Output={revision:int|null,text:str|null,approved:bool,editable:bool}.
Return a null revision/text with false booleans when no content is visible.
Use the supplied policy and design. Correct inconsistency by reporting it in
unresolved, not by silently claiming the handoff was complete. Implement the
best authorized interpretation without inventing policy. Preserve input data.
Only valid roles, views and internally consistent records are in scope.
Implementation style and layout are free. No filesystem, network, imports or tools.
"""

K_SOURCE = """Fixed source snapshot demo-queue-1, single sequential worker (no concurrency claim).
[worker.py:L1-L10]
1 def execute(job, store, gateway):
2     key = (job['account'], job['id'])
3     if store.is_done(key):
4         return 'already_done'
5     receipt = gateway.send(job['account'], job['payload'])
6     store.mark_done(key, receipt)
7     return 'done'
8 # The caller retries the entire execute() after either call raises.
9 # mark_done commits durably on success and writes nothing if it raises.
10 # No local in-progress marker or distributed transaction exists.
[gateway.py:L1-L6]
1 def send(account, payload):
2     return remote_client.submit(account, payload)
3 # This wrapper sends no job ID or explicit idempotency key.
4 # remote_client implementation and deployment contract are not in this snapshot.
5 # A successful return acknowledges acceptance, not independent final-effect proof.
6 # External deduplication behavior is unknown.
[store.py:L1-L5]
1 # Memory in this fixture represents durable committed state across sequential retries.
2 # is_done reads by (account, job_id); mark_done stores by the same tuple.
3 # Failed mark_done has no partial write.
4 # No payload digest is compared once a tuple is marked done.
5 # Clearing or moving this marker would change the observed behavior.
[README.md:L1-L2, descriptive and potentially stale]
1 The queue makes retries easy and gives you exactly-once jobs.
2 Read worker.py and gateway.py for the actual supported boundaries.
"""
K_DRAFT = """Knowledge draft: worker.execute calls gateway.send and writes status.
The store tracks finished jobs. This is an idempotent queue that supports safe
retries. For details, see the source files. No further behavior summary exists.
"""
K_RECEIVER = """Use ONLY the received knowledge package; original source is unavailable.
Answer Q1-Q4 with concise reasons and exact source references supplied in the package.
Q1: A send returned successfully and mark_done then failed. Will retry invoke
send again? What can and cannot be concluded about repeated external effects?
Q2: For sequential invocations, what happens to the same job ID in another
account, and to changed payload under an already-completed identical account/ID?
Q3: Would storing done BEFORE send preserve behavior? Identify a concrete
failure tradeoff; do not authorize or implement a change.
Q4: Locate the responsible entry and state boundary, reconcile the README's
exactly-once claim with known evidence, and state one deployment unknown.
An accurate conditional answer is sufficient: production certification is not requested.
Return Markdown, not a new code implementation. Do not fill unknowns with common practice.
"""

S_SOURCE = """SIMULATED data, invented for this bounded experiment; not a real customer study.
Audience: an operations director deciding whether to approve a bounded diagnostic pilot.
Before: 40 completions out of 100 opportunities over a two-week period.
After: 60 completions out of 200 opportunities over the next two-week period.
There was no random assignment or comparison group. The cohorts/mix differ;
these counts do not establish causality, cost savings, or generalization.
All completions/opportunities are on the same stated definition. Other data is absent.
Available proposal: authorize at most 2 weeks, USD 2,000 and 200 opportunities;
stop for confirmed safety harm; review at the end whether completion rate is at
least 40% without confirmed safety harm. Budget holder has NOT approved it yet.
Goal: explain mixed evidence and request THIS bounded diagnostic pilot, not
claim the approach is proven, approve spending oneself, or recommend full rollout.
Brand: clear, restrained, legible decision material. No preferred chart or layout.
The planner owns the argument, quantitative meaning, key caveats and ask. The
maker owns composition, wording refinements and accurate visual encoding within them.
"""
S_DRAFT = """Planning draft for three pages:
1. Progress: completions rose 50%; a large upward growth visual.
2. Why it works: results support expansion; add credibility from the pilot.
3. Next steps: rollout roadmap and budget.
These notes are a draft, not authority to change the requested decision.
"""
S_RECEIVER = """Produce exactly three Markdown page representations, separated by ---.
Each page must be usable as a page brief: a meaningful title, concise visible
copy and an explicit visual description (a table, chart, diagram, or typographic
composition can all work). Use only the supplied sources and final planning pack.
Carry necessary caveats in ordinary visible copy, not an absent appendix or tiny
footnote. Make the numerical comparison and decision request understandable.
Do not add unsupported claims or silently redo the planner's core argument;
record material handoff conflicts/omissions in unresolved. No actual PPT or
visual-quality claim is requested. No image generation, assets, tools or network.
"""

CASES = {
 'F': {
  'title':'P2 to P3 revision/approval interaction',
  'startup':{
   'current_owner':'P2 interaction designer; translate the fixed P1 policy into a coherent handoff and replace contradictory design notes.',
   'downstream_owner':'P3 implementer; choose implementation inside policy/design and the public function interface.',
   'reserved':'P1 policy is fixed; neither role may turn approval into a record-wide or latest-draft property.',
   'purpose':'Implement one complete projection used by list, detail and export, preserving revision approval and role visibility.'},
  'source': F_SOURCE, 'initial':F_DRAFT,
  'receiver_source':F_SOURCE, 'receiver_task':F_INTERFACE,
  'owner_task':'Deliver a coherent minimal P2 handoff. You may replace the draft, explain necessary relations or supply bounded examples; full implementation is not required. The receiver also sees P1 directly, so do not copy it merely for completeness.',
  'format':'python', 'boundary':False},
 'K': {
  'title':'Fixed-code behavior knowledge handoff',
  'startup':{
   'current_owner':'Knowledge author; describe fixed source behavior, conditions, conflicts and evidence. Do not redesign code.',
   'downstream_owner':'Maintainer; use the package for entry location, sequential retry behavior and adjacent ordering-change analysis.',
   'reserved':'External gateway/deployment behavior is unknown. No production safety guarantee or implementation change is authorized.',
   'purpose':'Support local retry-window and nearby account/identity/ordering analysis, with conditional rather than absolute conclusions.'},
  'source':K_SOURCE,'initial':K_DRAFT, 'receiver_source':'Only the knowledge package is admitted. Source snapshot is not directly visible.',
  'receiver_task':K_RECEIVER,
  'owner_task':'Produce compact but usable knowledge for the stated task family, with applicable evidence references. Preserve navigation, relevant conditions and unknowns. Avoid whole-source transcription and answer memorization.',
  'format':'analysis', 'boundary':False},
 'S': {
  'title':'Planning to decision-page production',
  'startup':{
   'current_owner':'Planner; correct draft argument, meaning of data, necessary caveats and the requested decision.',
   'downstream_owner':'Information designer; produce three page representations with freedom of visual composition.',
   'reserved':'Maker cannot invent metrics, causal evidence or spending authorization; planner cannot change the bounded-pilot goal.',
   'purpose':'Director understands mixed results and can decide the defined small pilot, not a full rollout.'},
  'source':S_SOURCE,'initial':S_DRAFT,'receiver_source':S_SOURCE,
  'receiver_task':S_RECEIVER,
  'owner_task':'Replace defective planning notes with a sufficient three-page argument/handoff. Set necessary meaning, not pixel coordinates. Facts alone without an argument/ask are insufficient.',
  'format':'pages', 'boundary':False},
}

BOUNDARIES = {}
BOUNDARIES['F-ready'] = copy.deepcopy(CASES['F'])
BOUNDARIES['F-ready'].update(boundary=True, initial='Use the directly available P1 policy as the complete behavior contract. Approval/editability bind the revision actually displayed; reader sees only approved content, with empty state if absent. Apply identically to list/detail/export. P3 freely implements the supplied function API. References are available, current, and consistent. No remaining P2 design choice or evidenced ability obstacle exists.', expected='handoff')
BOUNDARIES['K-guarantee'] = copy.deepcopy(CASES['K'])
BOUNDARIES['K-guarantee']['startup']['purpose']='Provide an unconditional production guarantee that external effects never duplicate. External service semantics are indispensable; user has not authorized weakening the guarantee.'
BOUNDARIES['K-guarantee'].update(boundary=True, initial='Local ordering and external unknown are understood, but the external idempotency contract is unavailable.', expected='need_input')
BOUNDARIES['S-missing'] = copy.deepcopy(CASES['S'])
BOUNDARIES['S-missing']['source']='Audience requests an evidence-backed quantitative ROI claim. Costs, monetary benefits and attribution evidence have not been supplied. User reserves the claim decision and has not authorized changing this task to a qualitative pilot proposal. All other startup authority boundaries remain.'
BOUNDARIES['S-missing'].update(boundary=True, initial='We still need the missing financial and attribution evidence; no supported ROI number exists.', expected='need_input')

# Counterbalanced within each wave; one frozen trial per cell, no best-of selection.
SLOTS = [('F','A'),('K','B'),('S','C'),('F','B'),('K','C'),('S','A'),('F','C'),('K','A'),('S','B'),('F-ready','C'),('K-guarantee','C'),('S-missing','C')]

OWNER_SCHEMA = {
 'type':'object','properties':{
  'action':{'type':'string','enum':['handoff','refine','need_input','stop']},
  'reason':{'type':'string'},
  'artifact':{'type':'string'},
  'remaining':{'type':'array','items':{'type':'string'}},
  'work_performed':{'type':'string'}},
 'required':['action','reason','artifact','remaining','work_performed'],
 'additionalProperties':False}
RECEIVER_SCHEMA = {
 'type':'object','properties':{
  'content':{'type':'string'},
  'unresolved':{'type':'array','items':{'type':'string'}}},
 'required':['content','unresolved'],'additionalProperties':False}
