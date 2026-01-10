import { FC, ReactNode } from "react";
import "./GlassCard.css";

interface GlassCardProps {
  children: ReactNode;
  header?: ReactNode;
  footer?: ReactNode;
  withBackground?: boolean;
  className?: string;
}

export const GlassCard: FC<GlassCardProps> = ({
  children,
  header,
  footer,
  withBackground = true,
  className = "",
}) => {
  return (
    <div className={`glass-page ${className}`}>
      {/* Background Blobs */}
      {withBackground && (
        <>
          <div className="blob blob-1" />
          <div className="blob blob-2" />
          <div className="blob blob-3" />
        </>
      )}

      {/* Main Card */}
      <main className="glass-card">
        {/* Header */}
        {header && <header className="glass-card-header">{header}</header>}

        {/* Content */}
        <section className="glass-card-content">{children}</section>

        {/* Footer */}
        {footer && <footer className="glass-card-footer">{footer}</footer>}
      </main>
    </div>
  );
};
