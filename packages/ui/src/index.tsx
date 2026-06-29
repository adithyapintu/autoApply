import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

export function Button({ children, className = "", ...props }: PropsWithChildren<ButtonHTMLAttributes<HTMLButtonElement>>) {
  return (
    <button
      className={`rounded-md bg-stone-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50 ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

