class SignatureMark extends HTMLElement {
    #animations = [];
    #observer;
    #motion = matchMedia('(prefers-reduced-motion: reduce)');
    #onReplay = () => this.replay();
    #onMotion = () => { if (this.#motion.matches)
        this.#finish(); };
    connectedCallback() {
        this.addEventListener('signature:replay', this.#onReplay);
        this.#motion.addEventListener('change', this.#onMotion);
        if (this.dataset.animate !== 'true' || this.#motion.matches)
            return;
        this.#observer = new IntersectionObserver(entries => {
            if (!entries.some(entry => entry.isIntersecting))
                return;
            this.#observer?.disconnect();
            this.replay();
        }, { threshold: 0.2 });
        this.#observer.observe(this);
    }
    disconnectedCallback() {
        this.#observer?.disconnect();
        this.#finish();
        this.removeEventListener('signature:replay', this.#onReplay);
        this.#motion.removeEventListener('change', this.#onMotion);
    }
    replay() {
        this.#finish();
        if (this.#motion.matches)
            return;
        this.#animations = [...this.querySelectorAll('[data-signature-pen]')].map(path => path.animate([
            { strokeDashoffset: 1, opacity: 0, offset: 0 },
            { strokeDashoffset: 1, opacity: 1, offset: .001 },
            { strokeDashoffset: 0, opacity: 1, offset: 1 }
        ], {
            duration: Number(path.dataset.duration),
            delay: Number(path.dataset.delay),
            easing: 'cubic-bezier(.33, 0, .36, 1)',
            fill: 'both'
        }));
        this.#animations.push(...[...this.querySelectorAll('[data-signature-ornament]')].map(path => path.animate([
            { opacity: 0, transform: 'scale(.65) rotate(-10deg)', offset: 0 },
            { opacity: 1, transform: 'scale(1.08) rotate(2deg)', offset: .68 },
            { opacity: 1, transform: 'scale(1) rotate(0deg)', offset: 1 }
        ], { duration: Number(path.dataset.duration), delay: Number(path.dataset.delay), easing: 'cubic-bezier(.16,1,.3,1)', fill: 'both' })));
        Promise.all(this.#animations.map(animation => animation.finished)).then(() => {
            this.dispatchEvent(new CustomEvent('signature:complete'));
        }).catch(() => { });
    }
    #finish() {
        this.#animations.forEach(animation => animation.cancel());
        this.#animations = [];
    }
}
if (!customElements.get('signature-mark'))
    customElements.define('signature-mark', SignatureMark);

class ChineseWordmark extends HTMLElement {
    #animations = [];
    #observer;
    #motion = matchMedia('(prefers-reduced-motion: reduce)');
    #onReplay = () => this.replay();
    #onMotion = () => { if (this.#motion.matches)
        this.#settle(); };
    connectedCallback() {
        this.addEventListener('wordmark:replay', this.#onReplay);
        this.#motion.addEventListener('change', this.#onMotion);
        this.dataset.inkState = 'settled';
        if (this.#motion.matches)
            return;
        this.#observer = new IntersectionObserver(entries => {
            if (entries.some(entry => entry.isIntersecting))
                this.replay();
        }, { threshold: .1 });
        this.#observer.observe(this);
    }
    disconnectedCallback() {
        this.#observer?.disconnect();
        this.#settle();
        this.removeEventListener('wordmark:replay', this.#onReplay);
        this.#motion.removeEventListener('change', this.#onMotion);
    }
    replay() {
        this.#observer?.disconnect();
        this.#settle();
        if (this.#motion.matches)
            return;
        this.dataset.inkState = 'writing';
        const guide = this.querySelector('.chinese-wordmark-guide');
        const animations = [...this.querySelectorAll('[data-ink-letter]')].map((letter, index) => letter.animate([
            { opacity: .18, transform: 'scale(1.2)', filter: 'blur(2px)' },
            { opacity: 1, transform: 'scale(1)', filter: 'blur(0px)' }
        ], { duration: 350, delay: 75 + index * 80, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'both' }));
        this.querySelectorAll('[data-ink-guide]').forEach((path, index) => animations.push(path.animate([{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }], { duration: 150, delay: index * 75, easing: 'ease-out', fill: 'both' })));
        if (guide)
            animations.push(guide.animate([
                { opacity: 0, offset: 0 },
                { opacity: .3, offset: .25 },
                { opacity: .3, offset: .55 },
                { opacity: 0, offset: 1 }
            ], { duration: 520, fill: 'both' }));
        this.#animations = animations;
        Promise.all(animations.map(animation => animation.finished)).then(() => {
            if (this.#animations !== animations)
                return;
            this.#settle();
            this.dispatchEvent(new CustomEvent('wordmark:complete'));
        }).catch(() => { });
    }
    #settle() {
        this.#animations.forEach(animation => animation.cancel());
        this.#animations = [];
        this.dataset.inkState = 'settled';
    }
}
if (!customElements.get('chinese-wordmark'))
    customElements.define('chinese-wordmark', ChineseWordmark);

class IconField extends HTMLElement {
    #animations = [];
    #animatedMarks = [];
    #observer;
    #themeObserver;
    #motion = matchMedia('(prefers-reduced-motion: reduce)');
    #compact = matchMedia('(max-width: 760px)');
    #visible = false;
    #cycleTimer;
    #cycleRemaining = 0;
    #cycleStarted = 0;
    #onReplay = () => this.replay();
    #onMotion = () => this.#sync();
    #onVisibility = () => this.#sync();
    #onViewport = () => {
        if (this.dataset.fieldVariant !== 'page' || !this.#animations.length)
            return;
        this.#build(true);
        this.#sync();
    };
    #onSwap = () => {
        this.#visible = false;
        this.#observer?.disconnect();
        this.#stop();
    };
    connectedCallback() {
        this.addEventListener('icon-field:replay', this.#onReplay);
        this.#motion.addEventListener('change', this.#onMotion);
        this.#compact.addEventListener('change', this.#onViewport);
        document.addEventListener('visibilitychange', this.#onVisibility);
        document.addEventListener('astro:before-swap', this.#onSwap);
        this.#observer = new IntersectionObserver(entries => {
            this.#visible = entries.some(entry => entry.isIntersecting);
            this.#sync();
        }, { threshold: .12 });
        this.#observer.observe(this);
        this.#themeObserver = new MutationObserver(() => {
            if (!this.#animations.length || this.#motion.matches)
                return;
            this.#build(true);
            this.#sync();
        });
        this.#themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
        this.#sync();
    }
    disconnectedCallback() {
        this.#observer?.disconnect();
        this.#themeObserver?.disconnect();
        this.#stop();
        this.removeEventListener('icon-field:replay', this.#onReplay);
        this.#motion.removeEventListener('change', this.#onMotion);
        this.#compact.removeEventListener('change', this.#onViewport);
        document.removeEventListener('visibilitychange', this.#onVisibility);
        document.removeEventListener('astro:before-swap', this.#onSwap);
    }
    replay() {
        this.#stop();
        if (!this.#motion.matches)
            this.#build();
        this.#sync();
    }
    #build(preservePhase = false) {
        const phases = new Map(preservePhase ? this.#animations.map((animation, index) => [this.#animatedMarks[index], Number(animation.currentTime ?? 0)]) : []);
        const continuingPhase = phases.values().next().value ?? 0;
        this.#animations.forEach(animation => animation.cancel());
        const styles = getComputedStyle(this);
        const gray = `rgb(${styles.getPropertyValue('--studio-muted').trim()})`;
        const accent = `rgb(${styles.getPropertyValue('--studio-accent').trim()})`;
        const channels = styles.getPropertyValue('--studio-accent').trim().split(/\s+/).map(Number);
        const night = channels[0] > 120;
        const mix = (other, weight) => `rgb(${other.map((value, index) => Math.round(value * weight + channels[index] * (1 - weight))).join(' ')})`;
        const cyan = mix(night ? [133, 218, 220] : [37, 152, 166], .74);
        const lilac = mix(night ? [208, 184, 237] : [147, 113, 180], .58);
        const keyframes = [
            { color: gray, opacity: .17, transform: 'scale(.96)', offset: 0 },
            { color: gray, opacity: .17, transform: 'scale(.96)', offset: .07 },
            { color: accent, opacity: .46, transform: 'scale(1.16)', offset: .115 },
            { color: accent, opacity: .28, transform: 'scale(1)', offset: .17 },
            { color: accent, opacity: .28, transform: 'scale(1)', offset: .32 },
            { color: cyan, opacity: .45, transform: 'scale(1.12)', offset: .365 },
            { color: cyan, opacity: .29, transform: 'scale(1)', offset: .42 },
            { color: cyan, opacity: .29, transform: 'scale(1)', offset: .56 },
            { color: lilac, opacity: .43, transform: 'scale(1.1)', offset: .605 },
            { color: lilac, opacity: .25, transform: 'scale(1)', offset: .66 },
            { color: lilac, opacity: .25, transform: 'scale(1)', offset: .8 },
            { color: accent, opacity: .4, transform: 'scale(1.08)', offset: .845 },
            { color: gray, opacity: .17, transform: 'scale(.96)', offset: .94 },
            { color: gray, opacity: .17, transform: 'scale(.96)', offset: 1 }
        ];
        const marks = [...this.querySelectorAll('[data-field-mark]')].filter(mark => this.dataset.fieldVariant !== 'page' || !this.#compact.matches || mark.dataset.fieldCompact === 'true');
        this.#animatedMarks = marks;
        let lastDelay = 0;
        this.#animations = marks.map(mark => {
            const row = Number(mark.dataset.row);
            const column = Number(mark.dataset.column);
            const delay = row * 165 + column * 27 + (row * 13 + column * 7) % 35;
            lastDelay = Math.max(lastDelay, delay);
            const animation = mark.animate(keyframes, { duration: 5200, delay, iterations: Infinity, easing: 'linear', fill: 'both' });
            animation.pause();
            if (preservePhase)
                animation.currentTime = phases.get(mark) ?? continuingPhase;
            return animation;
        });
        if (!preservePhase)
            this.#cycleRemaining = 5200 + lastDelay;
    }
    #sync() {
        if (this.#motion.matches) {
            this.#stop();
            this.dataset.fieldState = 'colored';
            return;
        }
        const running = this.#visible && document.visibilityState === 'visible';
        if (!this.#animations.length && running)
            this.#build();
        this.#animations.forEach(animation => {
            if (running && animation.playState !== 'running')
                animation.play();
            else if (!running && animation.playState !== 'paused')
                animation.pause();
        });
        this.dataset.fieldState = running ? 'coloring' : this.#animations.length ? 'paused' : 'waiting';
        if (running && this.#cycleRemaining > 0 && this.#cycleTimer === undefined) {
            this.#cycleStarted = performance.now();
            this.#cycleTimer = window.setTimeout(() => {
                this.#cycleTimer = undefined;
                this.#cycleRemaining = 0;
                this.dispatchEvent(new CustomEvent('icon-field:complete', { detail: { looping: true } }));
            }, this.#cycleRemaining);
        }
        else if (!running)
            this.#pauseCycleTimer();
    }
    #pauseCycleTimer() {
        if (this.#cycleTimer === undefined)
            return;
        window.clearTimeout(this.#cycleTimer);
        this.#cycleTimer = undefined;
        this.#cycleRemaining = Math.max(0, this.#cycleRemaining - (performance.now() - this.#cycleStarted));
    }
    #stop() {
        this.#pauseCycleTimer();
        this.#animations.forEach(animation => animation.cancel());
        this.#animations = [];
        this.#animatedMarks = [];
        this.#cycleRemaining = 0;
        this.dataset.fieldState = 'colored';
    }
}
if (!customElements.get('icon-field'))
    customElements.define('icon-field', IconField);
