"use client";
import { useEffect, useState } from "react";

export function useAudiencePreferences() {
  const [language, setLanguage] = useState("en");
  const [detail, setDetail] = useState("simple");
  const [focus, setFocus] = useState("");
  useEffect(() => {
    try {
      const saved = JSON.parse(
        localStorage.getItem("why-now-preferences") || "{}",
      );
      if (["en", "es"].includes(saved.language)) setLanguage(saved.language);
      if (["simple", "detail"].includes(saved.detail)) setDetail(saved.detail);
      if (typeof saved.focus === "string") setFocus(saved.focus);
    } catch {
      /* Preferences are optional in storage-restricted browsers. */
    }
  }, []);
  useEffect(() => {
    try {
      localStorage.setItem(
        "why-now-preferences",
        JSON.stringify({ language, detail, focus }),
      );
    } catch {}
  }, [language, detail, focus]);
  return { language, setLanguage, detail, setDetail, focus, setFocus };
}
