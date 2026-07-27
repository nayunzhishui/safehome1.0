import React from "react";


interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error): void {
    if (import.meta.env.DEV) {
      // 不输出message、组件props或参与者正文，只保留错误类型供本地排查。
      console.error("[SafeHome] render_failed", { errorName: error.name });
    }
  }

  render(): React.ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }
    return (
      <main className="fatalErrorPage" id="main-content">
        <section className="fatalErrorCard" role="alert" aria-labelledby="fatal-error-title">
          <p className="eyebrow">页面恢复</p>
          <h1 id="fatal-error-title">这个页面暂时没有加载出来</h1>
          <p>可能是网络波动或页面资源更新。可以重新加载；如果仍未恢复，请先返回首页。</p>
          <div className="fatalErrorActions">
            <button type="button" onClick={() => window.location.reload()}>
              重新加载
            </button>
            <a href="/">返回首页</a>
          </div>
        </section>
      </main>
    );
  }
}


function neverSettles<T>(): Promise<T> {
  return new Promise(() => undefined);
}

/**
 * 懒加载失败时每个页面最多自动刷新一次。
 * 刷新仍失败则把脱敏错误交给ErrorBoundary，避免循环刷新和空白页。
 */
// React.lazy自身以any约束组件props；这里保留相同泛型边界，调用处仍能推导实际props。
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function lazyWithRetry<T extends React.ComponentType<any>>(
  factory: () => Promise<{ default: T }>,
): React.LazyExoticComponent<T> {
  return React.lazy(async () => {
    const retryKey = `safehome:lazy-reload:${window.location.pathname}`;
    try {
      const module = await factory();
      window.sessionStorage.removeItem(retryKey);
      return module;
    } catch {
      if (window.sessionStorage.getItem(retryKey) !== "1") {
        window.sessionStorage.setItem(retryKey, "1");
        window.location.reload();
        return neverSettles<{ default: T }>();
      }
      window.sessionStorage.removeItem(retryKey);
      throw new Error("lazy_chunk_load_failed");
    }
  });
}
