import { type ClassValue, clsx } from "clsx"
// Optional: If using tailwind-merge
// import { twMerge } from "tailwind-merge" 

// export function cn(...inputs: ClassValue[]) {
//   return twMerge(clsx(inputs))
// }

// Using only clsx for now
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}
