import { useEffect } from 'react';
import Placeholder from '../common/Placeholder';
import useLogger from '../../hooks/useLogger';

export function ToolRegistryPage() {
  const logger = useLogger('ToolRegistryPage');

  useEffect(() => {
    logger.info('Tool Registry Page loaded');
  }, [logger]);

  return (
    <div data-testid="page-tool-registry" style={{ height: '100%' }}>
      <Placeholder
        title="Tool Registry"
        description="Browse and configure available analytical solver tools, CAD parsers, and custom calculation scripts. Submitting engineering tools exposes them to agent invocation automatically."
        data-testid="tool-registry-placeholder"
      />
    </div>
  );
}

export default ToolRegistryPage;
