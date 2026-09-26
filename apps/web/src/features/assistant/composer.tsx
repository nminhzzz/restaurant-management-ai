"use client";

import { ArrowUp } from "lucide-react";
import { useLayoutEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";

const LIMIT = 500;

export function Composer({
  onSubmit,
  disabled,
  placeholder,
  size = "lg",
  autoFocus = false,
  children,
}: {
  onSubmit: (text: string) => void;
  disabled: boolean;
  placeholder: string;
  size?: "lg" | "sm";
  autoFocus?: boolean;
  children?: React.ReactNode;
}) {
  const [text, setText] = useState("");
  const area = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const el = area.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [text]);

  function submit() {
    if (disabled || !text.trim()) return;
    onSubmit(text);
    setText("");
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
      className={cn(
        "grid gap-2 border border-border-strong bg-surface shadow-float focus-within:border-ink focus-within:ring-1 focus-within:ring-ink",
        size === "lg"
          ? "rounded-overlay px-3.5 pt-3 pb-2"
          : "rounded-container px-3 pt-2 pb-1.5",
      )}
    >
      <label htmlFor={`composer-${size}`} className="sr-only">
        Câu hỏi bằng tiếng Việt
      </label>
      <textarea
        id={`composer-${size}`}
        ref={area}
        rows={1}
        autoFocus={autoFocus}
        maxLength={LIMIT}
        value={text}
        placeholder={placeholder}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
            e.preventDefault();
            submit();
          }
        }}
        className={cn(
          "w-full resize-none bg-transparent outline-none placeholder:text-subtle",
          size === "lg"
            ? "min-h-11 text-[15px] leading-[22px]"
            : "min-h-6 text-sm",
        )}
      />
      <div className="flex items-center gap-2">
        {children}
        <span className="ml-auto text-xs text-subtle tabular-nums">
          {text.length}/{LIMIT}
        </span>
        <button
          type="submit"
          aria-label="Gửi câu hỏi"
          disabled={disabled || !text.trim()}
          className="grid size-11 place-items-center rounded-control bg-primary text-white hover:bg-primary-hover disabled:opacity-40"
        >
          <ArrowUp className="size-4" aria-hidden />
        </button>
      </div>
    </form>
  );
}
