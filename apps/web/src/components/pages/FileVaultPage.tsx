import { useEffect } from 'react';
import Placeholder from '../common/Placeholder';
import useLogger from '../../hooks/useLogger';

export function FileVaultPage() {
  const logger = useLogger('FileVaultPage');

  useEffect(() => {
    logger.info('File Vault Page loaded');
  }, [logger]);

  return (
    <div data-testid="page-file-vault" style={{ height: '100%' }}>
      <Placeholder
        title="File Vault"
        description="Secure local-first document storage for design sheets, compliance records, calculations, and FEA outputs. All raw engineering artifacts are kept safely offline on this spark unit."
        data-testid="file-vault-placeholder"
      />
    </div>
  );
}

export default FileVaultPage;
