"""Monitor provider-declared operations inside one application task block.

The wright/operation tool metadata is a Wright adapter contract, not a claim
that every MCP server implements MCP Tasks. No job semantics are inferred from
AI prose. Submission happens once; only identified status reads are polled.
"""
import asyncio
from dataclasses import replace
from .workflow_source_execution import _error, _invalid


def validate_operation_profile(runtime,step,profile):
    if not isinstance(profile,dict) or profile.get('version')!=1:
        raise _invalid('The application operation adapter is unsupported.')
    tools={t.tool_name:t for t in runtime.task_tools(step)}
    for role in ('status_tool','result_tool','cancel_tool'):
        name=profile.get(role)
        if not name and role!='status_tool':continue
        tool=tools.get(name)
        if tool is None or (role!='cancel_tool' and not tool.annotations.get('readOnlyHint',False)):
            raise _invalid(f'The application operation adapter needs a valid {role}.')
        argument=profile.get('id_argument','operation_id')
        properties=tool.input_schema.get('properties',{})
        if argument not in properties or set(tool.input_schema.get('required',[]))-{argument}:
            raise _invalid(f'The application {role} must accept the pinned operation identity without additional required inputs.')
    try:
        if not .05<=float(profile.get('poll_seconds',1))<=30:raise ValueError()
    except (ValueError,TypeError):raise _invalid('The operation polling interval is invalid.') from None


async def monitor_operation(runtime, step, submitted, profile, emit):
    from .workflow_mcp_execution import schema_digest
    if not isinstance(profile, dict) or profile.get('version')!=1:
        raise _invalid('The application operation adapter is unsupported.')
    id_field=profile.get('id_field','operation_id')
    if not isinstance(submitted,dict) or not isinstance(submitted.get(id_field),str) or not submitted[id_field]:
        raise _invalid('The application did not return a stable operation identity.')
    operation_id=submitted[id_field]
    argument=profile.get('id_argument','operation_id')
    async def event(state,**extra):
        if emit:await emit('operation_progress',task_id=step.id,task_title=step.title,operation_id=operation_id,state=state,**extra)
    async def invoke(role,readonly=False):
        name=profile.get(role)
        tool=next((t for t in runtime.task_tools(step) if t.tool_name==name),None)
        if tool is None or (readonly and not tool.annotations.get('readOnlyHint',False)):
            raise _invalid(f'The application needs an available {"read-only " if readonly else ""}{role} operation.')
        invocation=replace(step,tool_name=tool.name,schema_digest=schema_digest(tool),agent_task=False)
        args={argument:operation_id}
        runtime.validate(invocation,args,tool.input_schema)
        return await runtime.call(invocation,args,monitor=False)
    try:
        interval=float(profile.get('poll_seconds',1))
        if not .05<=interval<=30:raise ValueError()
    except (ValueError,TypeError):raise _invalid('The operation polling interval is invalid.') from None
    states=profile.get('states',{'working':'working','completed':'completed','failed':'failed','cancelled':'cancelled','input_required':'input_required'})
    await event('submitted',message='Application job submitted; waiting for verified completion.')
    try:
        async with asyncio.timeout(step.timeout_seconds):
            while True:
                value,text=await invoke('status_tool',readonly=True)
                if not isinstance(value,dict):raise _invalid('The application returned an invalid job status.')
                state=states.get(value.get(profile.get('status_field','status')))
                if state not in {'working','completed','failed','cancelled','input_required'}:
                    raise _invalid('The application returned an unknown job state; inspect the operation before retrying.')
                await event(state,message=str(value.get('message',state))[:1000])
                if state=='completed':
                    if profile.get('result_tool'):
                        result=await invoke('result_tool',readonly=True)
                    else:
                        if 'result' not in value:raise _invalid('The application completed without returning its result.')
                        import json
                        result=(value['result'],json.dumps(value['result'],ensure_ascii=False))
                    await event('results_collected')
                    return result
                if state in {'failed','cancelled','input_required'}:
                    raise _error('APPLICATION_'+state.upper(),f'{step.title}: application job {state.replace("_"," ")}.',
                                 str(value.get('message','Inspect the identified operation before starting another run.'))[:1000])
                await asyncio.sleep(interval)
    except (asyncio.CancelledError,TimeoutError):
        # A cancellation request is not proof that a remote mutation stopped.
        if profile.get('cancel_tool'):
            try:
                async with asyncio.timeout(10):await invoke('cancel_tool')
                await event('cancellation_requested',message='Cancellation requested; verify the remote job state before rerunning.')
            except Exception:
                await event('cancellation_unconfirmed',message='The application may still be working. Inspect its job before rerunning.')
        else:
            await event('cancellation_unavailable',message='This application cannot cancel this job; it may still be working.')
        raise
