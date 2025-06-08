import React from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';

interface TipTapEditorProps {
  content: string;
  onChange: (content: string) => void;
  className?: string;
}

const TipTapEditor: React.FC<TipTapEditorProps> = ({ content, onChange, className }) => {
  const editor = useEditor({
    extensions: [StarterKit],
    content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
  });

  return (
    <EditorContent editor={editor} className={className} />
  );
};

export default TipTapEditor; 