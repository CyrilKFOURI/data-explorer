type PageHeaderProps = {
  title: string;
  description?: string;
};

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <header className="max-w-prose">
      <h1 className="text-xl font-semibold tracking-tight text-ink-1">{title}</h1>
      {description && <p className="mt-1.5 text-ink-2">{description}</p>}
    </header>
  );
}
