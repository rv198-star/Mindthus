// Node layout backend. It consumes prepared graph geometry, never Markdown or prose.
import dagre from './_vendor/dagre.mjs';

const PROTOCOL = 'explain.geometry.v2';
let input = '';
for await (const chunk of process.stdin) {
  input += chunk;
  if (Buffer.byteLength(input) > 4_000_000) throw new Error('input_limit');
}
try {
  const payload = JSON.parse(input);
  if (payload.protocol !== PROTOCOL || !Array.isArray(payload.graphs)) throw new Error('protocol_mismatch');
  const graphs = payload.graphs.map((src) => {
    const g = new dagre.graphlib.Graph({multigraph: true});
    g.setGraph({rankdir: src.direction, nodesep: 40, ranksep: 76, edgesep: 24, marginx: 28, marginy: 28});
    g.setDefaultEdgeLabel(() => ({}));
    for (const n of src.nodes) g.setNode(n.id, {width: n.width, height: n.height});
    for (const e of src.edges) g.setEdge(e.from, e.to,
      {width: e.width, height: e.height, labelpos: 'c'}, e.id);
    dagre.layout(g);
    return {id: src.id, width: g.graph().width, height: g.graph().height,
      nodes: src.nodes.map((n) => ({id: n.id, x: g.node(n.id).x, y: g.node(n.id).y})),
      edges: src.edges.map((e) => {
        const v = g.edge({v: e.from, w: e.to, name: e.id});
        const mid = v.points[Math.floor(v.points.length / 2)];
        return {id: e.id, points: v.points, x: v.x ?? mid.x, y: v.y ?? mid.y};
      })};
  });
  process.stdout.write(JSON.stringify({protocol: PROTOCOL, graphs}));
} catch (error) {
  // Never echo the source/IR. Errors are program failures, not a fallback invitation.
  process.stderr.write('Explain Node layout failed: ' + error.name + '\n');
  process.exitCode = 3;
}
