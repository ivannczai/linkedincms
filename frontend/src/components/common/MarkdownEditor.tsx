import React from 'react';

interface MarkdownEditorProps {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  minHeight?: number;
  placeholder?: string;
  required?: boolean;
}

/**
 * A simple Markdown editor component
 */
const MarkdownEditor: React.FC<MarkdownEditorProps> = ({
  id,
  value,
  onChange,
  minHeight = 200,
  placeholder = 'Write your content in Markdown format...',
  required = false,
}) => {
  return (
    <div className="markdown-editor">
      <textarea
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full p-3 border rounded-md focus:ring-blue-500 focus:border-blue-500"
        style={{ minHeight: `${minHeight}px` }}
        placeholder={placeholder}
        required={required}
      />
      <div className="text-xs text-gray-500 mt-1">
        <p>
          Markdown supported: <strong>**bold**</strong>, <em>*italic*</em>,{' '}
          <code>`code`</code>, [link](url), # Heading, ## Subheading, - list item, 1. numbered item
        </p>
      </div>
    </div>
  );
};

export default MarkdownEditor;
