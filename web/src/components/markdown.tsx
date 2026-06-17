import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Minimal, theme-aware markdown renderer (no typography plugin needed). */
export function Markdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: (p) => <h1 className="mb-3 mt-1 text-xl font-semibold tracking-tight" {...p} />,
        h2: (p) => <h2 className="mb-2 mt-6 text-base font-semibold" {...p} />,
        h3: (p) => <h3 className="mb-1 mt-4 text-sm font-semibold" {...p} />,
        p: (p) => <p className="mb-3 text-sm leading-relaxed text-muted-foreground" {...p} />,
        ul: (p) => (
          <ul className="mb-3 ml-5 list-disc space-y-1 text-sm text-muted-foreground" {...p} />
        ),
        ol: (p) => (
          <ol className="mb-3 ml-5 list-decimal space-y-1 text-sm text-muted-foreground" {...p} />
        ),
        li: (p) => <li className="leading-relaxed" {...p} />,
        strong: (p) => <strong className="font-semibold text-foreground" {...p} />,
        a: (p) => <a className="text-primary underline-offset-4 hover:underline" {...p} />,
        code: (p) => <code className="rounded bg-secondary px-1 py-0.5 font-mono text-xs" {...p} />,
      }}
    >
      {children}
    </ReactMarkdown>
  );
}
