import { useEffect, useRef, useState } from "react";

/** True once the element has been near the viewport (charts load lazily, then stay). */
export function useInView<T extends Element>(margin = "200px") {
  const ref = useRef<T>(null);
  const [seen, setSeen] = useState(() => typeof IntersectionObserver === "undefined");
  useEffect(() => {
    const element = ref.current;
    if (seen || !element) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setSeen(true);
          observer.disconnect();
        }
      },
      { rootMargin: margin },
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, [seen, margin]);
  return { ref, seen };
}
