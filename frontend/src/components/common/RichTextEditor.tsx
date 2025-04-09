import React, { useCallback } from 'react';
import { useEditor, EditorContent, Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Link as LinkIcon,
} from 'lucide-react';

interface MenuBarProps {
  editor: Editor | null;
}

const MenuBar: React.FC<MenuBarProps> = ({ editor }) => {
  const setLink = useCallback(() => {
    if (!editor) return;
    const previousUrl = editor.getAttributes('link').href;
    const url = window.prompt('URL', previousUrl);

    // cancelled
    if (url === null) {
      return;
    }

    // empty
    if (url === '') {
      editor.chain().focus().extendMarkRange('link').unsetLink().run();
      return;
    }

    // update link
    editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
  }, [editor]);

  if (!editor) {
    return null;
  }

  const buttonClass = (isActive: boolean) =>
    `p-1 rounded hover:bg-gray-200 ${
      isActive ? 'bg-gray-300 text-blue-600' : 'text-gray-700'
    }`;

  return (
    <div className="flex flex-wrap gap-1 border border-gray-300 rounded-t-md p-2 bg-gray-50">
      <button
        type="button"
        onClick={() => editor.chain().focus().toggleBold().run()}
        disabled={!editor.can().chain().focus().toggleBold().run()}
        className={buttonClass(editor.isActive('bold'))}
        title="Bold"
      >
        <Bold className="w-4 h-4" />
      </button>
      <button
        type="button"
        onClick={() => editor.chain().focus().toggleItalic().run()}
        disabled={!editor.can().chain().focus().toggleItalic().run()}
        className={buttonClass(editor.isActive('italic'))}
        title="Italic"
      >
        <Italic className="w-4 h-4" />
      </button>
      <button
        type="button"
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        className={buttonClass(editor.isActive('bulletList'))}
        title="Bullet List"
      >
        <List className="w-4 h-4" />
      </button>
      <button
        type="button"
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        className={buttonClass(editor.isActive('orderedList'))}
        title="Ordered List"
      >
        <ListOrdered className="w-4 h-4" />
      </button>
      <button
        type="button"
        onClick={setLink}
        className={buttonClass(editor.isActive('link'))}
        title="Set Link"
      >
        <LinkIcon className="w-4 h-4" />
      </button>
    </div>
  );
};

interface RichTextEditorProps {
  id?: string;
  value: string; // Expecting HTML string
  onChange: (htmlValue: string) => void;
  minHeight?: number;
  required?: boolean; // Keep for form validation if needed
}

const RichTextEditor: React.FC<RichTextEditorProps> = ({
  id,
  value,
  onChange,
  minHeight = 300,
  required = false, // Although Tiptap doesn't directly use it, keep for potential form logic
}) => {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        // Configure StarterKit options if needed, e.g., disable heading levels
        heading: false, // Disable headings for simpler LinkedIn output
        codeBlock: false, // Disable code blocks
        blockquote: false, // Disable blockquotes
      }),
      Link.configure({
        openOnClick: false, // Don't open links when clicking in the editor
        autolink: true, // Automatically detect links
      }),
    ],
    content: value, // Initial content (HTML)
    editorProps: {
      attributes: {
        class:
          'prose prose-sm sm:prose lg:prose-lg xl:prose-xl focus:outline-none p-4 border border-t-0 border-gray-300 rounded-b-md min-h-[--min-h] bg-white',
        // Use CSS variable for dynamic min-height
        style: `--min-h: ${minHeight}px;`,
      },
    },
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML()); // Pass HTML back up
    },
  });

  // Add a hidden input for potential form validation based on content length
  // Tiptap content might be just <p></p> when empty
  const isEmpty = editor?.getText().trim().length === 0;

  return (
    <div className="rich-text-editor">
      <MenuBar editor={editor} />
      <EditorContent editor={editor} id={id} />
      {/* Hidden input for basic required validation */}
      {required && (
         <input
           type="text"
           value={isEmpty ? '' : 'filled'} // Simple value to indicate content presence
           required
           style={{
             position: 'absolute',
             opacity: 0,
             height: 0,
             width: 0,
             pointerEvents: 'none',
           }}
           aria-hidden="true"
           tabIndex={-1}
         />
       )}
    </div>
  );
};

export default RichTextEditor;
