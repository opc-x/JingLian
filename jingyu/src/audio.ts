/** 发音：优先缓存 MP3，否则 Web Speech API */
let speaking: SpeechSynthesisUtterance | null = null;

export function stopSpeaking() {
  if (typeof speechSynthesis !== "undefined") {
    speechSynthesis.cancel();
  }
  speaking = null;
}

export function speakWord(word: string, audioUrl?: string) {
  stopSpeaking();
  if (audioUrl) {
    const audio = new Audio(audioUrl);
    audio.play().catch(() => speakWithBrowser(word));
    return;
  }
  speakWithBrowser(word);
}

function speakWithBrowser(text: string) {
  if (typeof speechSynthesis === "undefined") return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-GB";
  u.rate = 0.92;
  speaking = u;
  speechSynthesis.speak(u);
}

export function bindSpeakButtons(root: ParentNode = document) {
  root.querySelectorAll("[data-speak]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const el = btn as HTMLElement;
      const text = el.dataset.speak ?? "";
      const audio = el.dataset.audio;
      if (text) speakWord(text, audio || undefined);
    });
  });
}
