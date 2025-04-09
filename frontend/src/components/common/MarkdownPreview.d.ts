import React from 'react';

interface MarkdownPreviewProps {
  content: string;
  className?: string;
}

declare const MarkdownPreview: React.FC<MarkdownPreviewProps>;

export default MarkdownPreview;
