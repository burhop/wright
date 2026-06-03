import React, { useState, useEffect } from 'react';

interface ImagePreviewerProps {
  arrayBuffer: ArrayBuffer;
  fileName: string;
}

export const ImagePreviewer: React.FC<ImagePreviewerProps> = ({ arrayBuffer, fileName }) => {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    let mimeType = 'image/png';
    if (ext === 'jpg' || ext === 'jpeg') mimeType = 'image/jpeg';
    else if (ext === 'svg') mimeType = 'image/svg+xml';
    else if (ext === 'gif') mimeType = 'image/gif';

    const blob = new Blob([arrayBuffer], { type: mimeType });
    const url = URL.createObjectURL(blob);
    setObjectUrl(url);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [arrayBuffer, fileName]);

  if (!objectUrl) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--color-secondary)', fontFamily: 'var(--font-ui)', fontSize: '0.8rem' }}>
        Loading preview...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', backgroundColor: 'var(--color-neutral)', overflow: 'auto', padding: 'var(--space-md)' }}>
      <img
        src={objectUrl}
        alt={fileName}
        style={{
          maxWidth: '100%',
          maxHeight: '100%',
          objectFit: 'contain',
          borderRadius: 'var(--radius-sm)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        }}
      />
    </div>
  );
};

export default ImagePreviewer;
