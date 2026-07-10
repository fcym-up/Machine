export class VoiceController {
    constructor(callbacks) {
        this.cb = callbacks || {};
        this.recognition = null;
        this.isListening = false;
        this.speaking = false;
        this.silenceTimer = null;
    }

    start() {
        if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
            if (this.cb.onUnavailable) this.cb.onUnavailable();
            return;
        }
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SR();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = "zh-CN";
        this.isListening = true;

        this.recognition.onresult = (e) => {
            let finalText = "";
            for (let i = e.resultIndex; i < e.results.length; i++) {
                if (e.results[i].isFinal) {
                    finalText += e.results[i][0].transcript;
                }
            }
            if (!finalText) return;
            if (this.speaking) return;
            if (!this.isListening) return;

            // Check for wake word
            if (finalText.includes("\u7ec8\u7aef") || finalText.includes("Machine") || finalText.includes("machine")) {
                this.speaking = true;
                this.recognition.stop();
                if (this.cb.onWake) this.cb.onWake();
                this._startSpeechMode();
                return;
            }
        };

        this.recognition.onend = () => {
            if (this.isListening && !this.speaking) {
                try { this.recognition.start(); } catch(e) {}
            }
        };

        this.recognition.onerror = (e) => {
            if (e.error === "not-allowed" && this.cb.onUnavailable) this.cb.onUnavailable();
        };

        try { this.recognition.start(); } catch(e) {}
    }

    _startSpeechMode() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        const sr = new SR();
        sr.continuous = false;
        sr.interimResults = true;
        sr.lang = "zh-CN";

        sr.onresult = (e) => {
            let text = "";
            for (let i = e.resultIndex; i < e.results.length; i++) {
                if (e.results[i].isFinal) text += e.results[i][0].transcript;
            }
            if (text) {
                if (this.cb.onTranscript) this.cb.onTranscript(text);
                if (this.cb.onStateChange) this.cb.onStateChange("thinking");
                this._callLLM(text);
            }
        };

        sr.onend = () => {
            if (this.speaking) {
                setTimeout(() => {
                    if (this.speaking) {
                        try { sr.start(); } catch(e) {}
                    }
                }, 500);
            }
        };

        sr.onerror = () => {};

        // Auto-stop after 2s of silence
        this.silenceTimer = setTimeout(() => {
            this.speaking = false;
            this.sr = null;
            if (this.cb.onSilence) this.cb.onSilence();
            if (this.cb.onStateChange) this.cb.onStateChange("idle");
            // Restart continuous listening
            this.isListening = true;
            if (this.recognition) { try { this.recognition.start(); } catch(e) {} }
        }, 3000);

        try { sr.start(); } catch(e) {}
    }

    _callLLM(text) {
        const self = this;
        fetch("/api/v1/conversation/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-API-Key": "machine-dev-key-change-me" },
            body: JSON.stringify({ message: text })
        })
        .then(r => r.json())
        .then(data => {
            const reply = data.reply || "";
            if (self.cb.onLLMReply) self.cb.onLLMReply(reply);
            if (self.cb.onStateChange) self.cb.onStateChange("speaking");
            self._speak(reply);
        })
        .catch(() => {});
    }

    _speak(text) {
        if (!window.speechSynthesis) {
            this.speaking = false;
            if (this.cb.onSilence) this.cb.onSilence();
            return;
        }
        const utter = new SpeechSynthesisUtterance(text);
        utter.lang = "zh-CN";
        utter.rate = 1.1;
        utter.onend = () => {
            this.speaking = false;
            if (this.cb.onSilence) this.cb.onSilence();
            if (this.cb.onStateChange) this.cb.onStateChange("idle");
            this.isListening = true;
            if (this.recognition) { try { this.recognition.start(); } catch(e) {} }
        };
        utter.onerror = () => {
            this.speaking = false;
            this.isListening = true;
            if (this.recognition) { try { this.recognition.start(); } catch(e) {} }
        };
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utter);
    }

    stop() {
        this.isListening = false;
        this.speaking = false;
        if (this.recognition) { try { this.recognition.stop(); } catch(e) {} }
        this.recognition = null;
        window.speechSynthesis.cancel();
    }
}
