import asyncio
import subprocess
import sys
import pytest
from workspace_service.workflow_resource_lease import ApplicationLease
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError


def test_another_process_cannot_acquire_the_same_application(tmp_path):
    code = """import asyncio,sys
from workspace_service.workflow_resource_lease import ApplicationLease
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError
async def test():
 try:
  async with ApplicationLease('cad',directory=sys.argv[1],timeout=.1):print('acquired')
 except WorkflowSourceExecutionError:print('busy')
asyncio.run(test())
"""

    async def scenario():
        async with ApplicationLease("cad", directory=tmp_path):
            child = await asyncio.to_thread(
                subprocess.run,
                [sys.executable, "-c", code, str(tmp_path)],
                capture_output=True,
                text=True,
                timeout=15,
            )
            assert child.returncode == 0, child.stderr
            assert child.stdout.strip() == "busy"
        async with ApplicationLease("cad", directory=tmp_path, timeout=0.1):
            pass

    asyncio.run(scenario())


def test_cancelled_waiter_does_not_release_the_owner(tmp_path):
    async def scenario():
        async with ApplicationLease("cad", directory=tmp_path):
            waiter = asyncio.create_task(
                ApplicationLease("cad", directory=tmp_path).__aenter__()
            )
            await asyncio.sleep(0.03)
            waiter.cancel()
            with pytest.raises(asyncio.CancelledError):
                await waiter
            with pytest.raises(WorkflowSourceExecutionError):
                async with ApplicationLease("cad", directory=tmp_path, timeout=0.1):
                    pass

    asyncio.run(scenario())
