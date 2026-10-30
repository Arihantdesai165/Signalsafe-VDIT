/* ============================================
   KAVACH – URL Module
   URL input + API integration
   ============================================ */

(function () {
    const urlInput = document.getElementById('url-input');
    const analyzeBtn = document.getElementById('url-analyze-btn');
    const progressContainer = document.getElementById('url-progress-container');

    // UI Elements for steps
    const step1Icon = document.getElementById('step1-icon');
    const step1Text = document.getElementById('step1-text');
    
    const step2Icon = document.getElementById('step2-icon');
    const step2Title = document.getElementById('step2-title');
    const step2Text = document.getElementById('step2-text');
    const step2BarContainer = document.getElementById('step2-bar-container');
    const step2Bar = document.getElementById('step2-bar');
    
    const step3Icon = document.getElementById('step3-icon');
    const step3Title = document.getElementById('step3-title');
    const step3Text = document.getElementById('step3-text');

    // Enable analyze button logic if needed
    urlInput.addEventListener('input', () => {
        analyzeBtn.disabled = !urlInput.value.trim();
        // Hide progress and results on new input
        if (progressContainer) progressContainer.classList.add('hidden');
        document.getElementById('result-container').classList.add('hidden');
        document.getElementById('default-tips').classList.remove('hidden');
    });

    // Enter key shortcut
    urlInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && urlInput.value.trim()) {
            analyzeBtn.click();
        }
    });

    function resetProgressUI() {
        if (!progressContainer) return;
        progressContainer.classList.remove('hidden');
        
        // Step 1: Active
        step1Icon.className = "size-6 rounded-full bg-[#121f26] border border-[#0dc8f2] flex items-center justify-center shrink-0 z-10 shadow-[0_0_10px_rgba(13,200,242,0.4)]";
        step1Icon.innerHTML = `<span class="material-symbols-outlined text-[14px] text-[#0dc8f2] animate-spin">sync</span>`;
        step1Text.textContent = "Validating...";
        step1Text.className = "text-[11px] text-[#0dc8f2] mt-1";

        // Step 2: Inactive
        step2Icon.className = "size-6 rounded-full bg-[#0b1319] border border-[#1a2c32] flex items-center justify-center shrink-0 z-10";
        step2Icon.innerHTML = `<span class="material-symbols-outlined text-[14px] text-slate-600">dns</span>`;
        step2Title.className = "text-[13px] font-bold text-slate-400";
        step2BarContainer.classList.add('hidden');
        step2Text.classList.remove('hidden');
        step2Text.textContent = "Queued...";
        step2Bar.style.width = "0%";

        // Step 3: Inactive
        step3Icon.className = "size-6 rounded-full bg-[#0b1319] border border-[#1a2c32] flex items-center justify-center shrink-0 z-10";
        step3Icon.innerHTML = `<span class="material-symbols-outlined text-[14px] text-slate-600">database</span>`;
        step3Title.className = "text-[13px] font-bold text-slate-400";
        step3Text.textContent = "Queued...";
        step3Text.className = "text-[11px] text-slate-600 mt-1";
    }

    async function simulateProgress() {
        // Wait 500ms, then complete Step 1
        await new Promise(r => setTimeout(r, 600));
        step1Icon.className = "size-6 rounded-full bg-[#121f26] border border-[#0dc8f2] flex items-center justify-center shrink-0 z-10";
        step1Icon.innerHTML = `<span class="material-symbols-outlined text-[14px] text-[#0dc8f2]">check</span>`;
        step1Text.textContent = "Trusted Authority Verified";
        step1Text.className = "text-[11px] text-slate-400 mt-1";

        // Start Step 2
        step2Icon.className = "size-6 rounded-full bg-[#121f26] border border-[#0dc8f2] flex items-center justify-center shrink-0 z-10 shadow-[0_0_10px_rgba(13,200,242,0.4)]";
        step2Icon.innerHTML = `<span class="material-symbols-outlined text-[14px] text-[#0dc8f2] animate-spin">sync</span>`;
        step2Title.className = "text-[13px] font-bold text-[#0dc8f2]";
        step2Text.classList.add('hidden');
        step2BarContainer.classList.remove('hidden');
        
        // Animate bar
        step2Bar.style.width = "60%";
        await new Promise(r => setTimeout(r, 800));
        step2Bar.style.width = "100%";
        await new Promise(r => setTimeout(r, 400));

        // Complete Step 2
        step2Icon.className = "size-6 rounded-full bg-[#121f26] border border-[#0dc8f2] flex items-center justify-center shrink-0 z-10";
        step2Icon.innerHTML = `<span class="material-symbols-outlined text-[14px] text-[#0dc8f2]">check</span>`;
        step2Title.className = "text-[13px] font-bold text-white";
        step2BarContainer.classList.add('hidden');
        step2Text.classList.remove('hidden');
        step2Text.textContent = "Structure Analyzed";

        // Start Step 3
        step3Icon.className = "size-6 rounded-full bg-[#121f26] border border-[#0dc8f2] flex items-center justify-center shrink-0 z-10 shadow-[0_0_10px_rgba(13,200,242,0.4)]";
        step3Icon.innerHTML = `<span class="material-symbols-outlined text-[14px] text-[#0dc8f2] animate-spin">sync</span>`;
        step3Title.className = "text-[13px] font-bold text-[#0dc8f2]";
        step3Text.textContent = "Checking global threat intelligence...";
        step3Text.className = "text-[11px] text-[#0dc8f2] mt-1";
    }

    function completeProgress() {
        step3Icon.className = "size-6 rounded-full bg-[#121f26] border border-[#0dc8f2] flex items-center justify-center shrink-0 z-10";
        step3Icon.innerHTML = `<span class="material-symbols-outlined text-[14px] text-[#0dc8f2]">check</span>`;
        step3Title.className = "text-[13px] font-bold text-white";
        step3Text.textContent = "Reputation check complete";
        step3Text.className = "text-[11px] text-slate-400 mt-1";
    }

    // Analyze
    analyzeBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) {
            urlInput.focus();
            return;
        }

        KavachApp.setLoading(analyzeBtn, true);
        document.getElementById('result-container').classList.add('hidden');
        document.getElementById('default-tips').classList.add('hidden');
        
        resetProgressUI();
        
        // Start simulation in parallel with API fetch
        const progressPromise = simulateProgress();
        
        try {
            const response = await fetch('/api/url/phishing/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url }),
            });

            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const data = await response.json();
            
            // Wait for both progress animation and network to finish
            await progressPromise;
            completeProgress();
            
            // Small delay before showing result
            setTimeout(() => {
                KavachApp.displayResult('result-container', data);
                KavachApp.setLoading(analyzeBtn, false);
            }, 500);

        } catch (err) {
            console.error('URL analysis failed:', err);
            await progressPromise;
            completeProgress();
            step3Text.textContent = "Error computing database check.";
            
            KavachApp.displayResult('result-container', {
                risk_score: 90,
                status: 'suspicious',
                reasons: ['Deep scan failed or network error.', err.message],
            });
            KavachApp.setLoading(analyzeBtn, false);
        }
    });
})();
