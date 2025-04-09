declare module '*.css' {
  const content: { [className: string]: string };
  export default content;
}

// Add support for Tailwind CSS directives
declare module 'postcss-import';
declare module 'tailwindcss';
declare module 'autoprefixer';
