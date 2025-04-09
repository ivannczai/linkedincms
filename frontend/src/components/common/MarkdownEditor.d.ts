import React from 'react';

interface MarkdownEditorProps {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  minHeight?: number;
  placeholder?: string;
  required?: boolean;
}

declare const MarkdownEditor: React.FC<MarkdownEditorProps>;

export default MarkdownEditor;
