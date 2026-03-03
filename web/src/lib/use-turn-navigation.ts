import { useCallback, useEffect, useReducer } from "react";

type NavAction =
  | { type: "prev" }
  | { type: "next"; max: number }
  | { type: "first" }
  | { type: "last"; max: number }
  | { type: "seek"; index: number };

function navReducer(
  state: { userIndex: number; following: boolean },
  action: NavAction,
) {
  switch (action.type) {
    case "prev":
      return { userIndex: Math.max(0, state.userIndex - 1), following: false };
    case "next": {
      const next = Math.min(action.max, state.userIndex + 1);
      return { userIndex: next, following: next >= action.max };
    }
    case "first":
      return { userIndex: 0, following: false };
    case "last":
      return { userIndex: action.max, following: true };
    case "seek":
      return { userIndex: action.index, following: false };
  }
}

export function useTurnNavigation(maxIdx: number) {
  const [nav, dispatch] = useReducer(navReducer, {
    userIndex: 0,
    following: true,
  });

  const index = nav.following ? maxIdx : Math.min(nav.userIndex, maxIdx);

  const goPrev = useCallback(() => dispatch({ type: "prev" }), []);
  const goNext = useCallback(
    () => dispatch({ type: "next", max: maxIdx }),
    [maxIdx],
  );
  const goFirst = useCallback(() => dispatch({ type: "first" }), []);
  const goLast = useCallback(
    () => dispatch({ type: "last", max: maxIdx }),
    [maxIdx],
  );
  const seek = useCallback(
    (i: number) => dispatch({ type: "seek", index: i }),
    [],
  );

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        goPrev();
      } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        goNext();
      } else if (e.key === "Home") {
        e.preventDefault();
        goFirst();
      } else if (e.key === "End") {
        e.preventDefault();
        goLast();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [goPrev, goNext, goFirst, goLast]);

  return { index, goPrev, goNext, goFirst, goLast, seek };
}
