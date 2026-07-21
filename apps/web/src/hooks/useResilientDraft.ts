import { useEffect, useMemo, useRef, useState } from "react";

const DRAFT_VERSION = 1;

interface StoredDraft<T> {
  version: number;
  values: T;
  savedAt: string;
  clientSubmissionId: string;
}

function createSubmissionId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function readDraft<T>(storageKey: string): StoredDraft<T> | null {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(storageKey) || "null") as StoredDraft<T> | null;
    return parsed?.version === DRAFT_VERSION && parsed.values ? parsed : null;
  } catch {
    return null;
  }
}

function savedLabel(savedAt: string): string {
  if (!savedAt) return "尚未保存草稿";
  const date = new Date(savedAt);
  return Number.isNaN(date.getTime()) ? "草稿已保存在本机" : `草稿已于 ${date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })} 保存在本机`;
}

export function useResilientDraft<T>({
  storageKey,
  submissionPrefix,
  value,
  restore,
  hasContent,
}: {
  storageKey: string;
  submissionPrefix: string;
  value: T;
  restore: (values: T) => void;
  hasContent: (values: T) => boolean;
}) {
  const initial = useMemo(() => readDraft<T>(storageKey), [storageKey]);
  const submissionId = useRef(initial?.clientSubmissionId || createSubmissionId(submissionPrefix));
  const restoreRef = useRef(restore);
  const hasContentRef = useRef(hasContent);
  const skipFirstPersist = useRef(true);
  const [restored, setRestored] = useState(Boolean(initial));
  const [saveStatus, setSaveStatus] = useState(initial ? savedLabel(initial.savedAt) : "尚未填写");
  const serialized = JSON.stringify(value);

  useEffect(() => {
    if (initial) restoreRef.current(initial.values);
  }, [initial]);

  useEffect(() => {
    if (skipFirstPersist.current) {
      skipFirstPersist.current = false;
      return;
    }
    const timer = window.setTimeout(() => {
      if (!hasContentRef.current(value)) {
        try {
          window.localStorage.removeItem(storageKey);
        } catch {
          // Restricted storage must not interrupt the form flow.
        }
        setSaveStatus("尚未填写");
        return;
      }
      const savedAt = new Date().toISOString();
      try {
        window.localStorage.setItem(storageKey, JSON.stringify({ version: DRAFT_VERSION, values: value, savedAt, clientSubmissionId: submissionId.current }));
        setSaveStatus(savedLabel(savedAt));
      } catch {
        setSaveStatus("本机空间不足，暂时无法保存草稿");
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [serialized, storageKey]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (!hasContentRef.current(value)) return;
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [serialized]);

  function flush() {
    if (!hasContentRef.current(value)) return;
    const savedAt = new Date().toISOString();
    try {
      window.localStorage.setItem(storageKey, JSON.stringify({ version: DRAFT_VERSION, values: value, savedAt, clientSubmissionId: submissionId.current }));
      setSaveStatus(savedLabel(savedAt));
    } catch {
      setSaveStatus("本机空间不足，暂时无法保存草稿");
    }
  }

  function clear() {
    try {
      window.localStorage.removeItem(storageKey);
    } catch {
      // Submission success takes precedence over local cleanup failures.
    }
    submissionId.current = createSubmissionId(submissionPrefix);
    setRestored(false);
    setSaveStatus("已提交");
  }

  return { clientSubmissionId: submissionId.current, clear, flush, restored, saveStatus };
}
