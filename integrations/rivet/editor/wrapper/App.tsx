import 'core-js/actual';
import { isRivetWebAppPreviewWindow } from './components/rivetWebApps/RivetWebAppPreviewWindow.js';
import { WrightEditorBridge } from './WrightEditorBridge.js';

function App() {
  if (isRivetWebAppPreviewWindow()) {
    return null;
  }

  return <WrightEditorBridge />;
}

export default App;
