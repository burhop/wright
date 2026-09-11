import type { WorkspaceEngineeringResult } from "../../services/workspace-service";

export function EngineeringResults({results,onOpenFile}: {results: WorkspaceEngineeringResult[]; onOpenFile?: (path:string)=>void}) {
  return <section aria-label="Engineering results" data-testid="workflow-engineering-results">
    {results.map(result=><article key={result.id} className="recovery-engineering-result">
      <b>{result.name}</b>
      {result.kind==="cad_model"&&<small> · CAD model</small>}
      {result.kind==="analysis"&&<small> · Analysis result</small>}
      {!result.representations.some(r=>r.durability==="persistent")&&result.representations.some(r=>r.durability==="session")&&<p>Available in the current application session. Save or export it to keep a durable result.</p>}
      {result.representations.filter(r=>r.kind==="workspace_file").map(r=><p key={r.location}>
        {onOpenFile?<button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-native-run-output-link" onClick={()=>onOpenFile(r.location)}>Open {r.location}</button>:r.location}
        {r.size_bytes!==null&&<small> · {r.size_bytes.toLocaleString()} bytes</small>}
      </p>)}
      {result.representations.filter(r=>r.kind==="cloud_resource"&&/^https?:\/\//i.test(r.location)).map(r=><p key={r.location}><a href={r.location} target="_blank" rel="noreferrer">Open {result.name}</a>{r.revision&&<small> · Revision {r.revision}</small>}</p>)}
      {result.exports.length>0&&<section aria-label={`${result.name} exports`}><h4>Exports</h4><EngineeringResults results={result.exports} onOpenFile={onOpenFile}/></section>}
    </article>)}
  </section>;
}
