import {render,screen,fireEvent} from '@testing-library/react';
import {expect,it,vi} from 'vitest';
import {EngineeringResults} from './EngineeringResults';
import type {WorkspaceEngineeringResult} from '../../services/workspace-service';

it('opens the native model and individual exports through the existing file action',()=>{
 const rep={kind:'workspace_file' as const,location:'part.psm',format:'psm',durability:'persistent' as const,provider_id:'',resource_id:'',revision:null,sha256:null,size_bytes:100};
 const model:WorkspaceEngineeringResult={schema_version:1,id:'model',kind:'cad_model',name:'Bracket',representations:[rep],provenance:{run_id:'run',task_id:'cad',output_port:'model',input_revisions:[]},exports:[]};
 model.exports=[{...model,id:'step',kind:'file',name:'part.step',representations:[{...rep,location:'part.step',format:'step'}],exports:[]}];
 const open=vi.fn();render(<EngineeringResults results={[model]} onOpenFile={open}/>);
 expect(screen.getAllByText(/CAD model/)).toHaveLength(1);
 expect(screen.getByRole('heading',{name:'Exports'})).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Open part.step'}));
 expect(open).toHaveBeenCalledWith('part.step');
});
