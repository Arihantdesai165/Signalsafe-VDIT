/* ============================================
   KAVACH – QR Code Module
   Upload/capture + API integration + Payment Details Display
   ============================================ */

(function () {
    const fileInput = document.getElementById('qr-file');
    const cameraInput = document.getElementById('qr-camera');
    const uploadBtn = document.getElementById('qr-upload-btn');
    const cameraBtn = document.getElementById('qr-camera-btn');
    const analyzeBtn = document.getElementById('qr-analyze-btn');
    const preview = document.getElementById('qr-preview');
    const placeholder = document.getElementById('qr-placeholder');
    const dropZone = document.getElementById('qr-drop-zone');

    let selectedFile = null;
    let lastAnalysisData = null; // Store for proceed-to-pay

    // Upload button click
    uploadBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    // Camera button click
    cameraBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        KavachCamera.open((file) => {
            handleFileSelect({ target: { files: [file] } });
        });
    });

    // Click on drop zone
    dropZone.addEventListener('click', () => {
        if (!selectedFile) fileInput.click();
    });

    // File selected
    fileInput.addEventListener('change', handleFileSelect);
    cameraInput.addEventListener('change', handleFileSelect);

    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;
        selectedFile = file;
        lastAnalysisData = null;
        
        const nameEl = document.getElementById('qr-filename');
        if (nameEl) nameEl.textContent = file.name;

        showPreview(file);
        analyzeBtn.disabled = false;
        
        // Clear previous results
        document.getElementById('result-container').classList.add('hidden');
        document.getElementById('default-tips').classList.remove('hidden');
        removePaymentCard();
    }

    const previewContainer = document.getElementById('qr-preview-container');

    function showPreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.src = e.target.result;
            previewContainer.classList.remove('hidden');
            dropZone.classList.add('hidden');
        };
        reader.readAsDataURL(file);
    }
    
    const changeBtn = document.getElementById('qr-change-btn');
    if (changeBtn) {
        changeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            selectedFile = null;
            lastAnalysisData = null;
            preview.src = '';
            previewContainer.classList.add('hidden');
            dropZone.classList.remove('hidden');
            analyzeBtn.disabled = true;
            fileInput.value = '';
            cameraInput.value = '';
            document.getElementById('result-container').classList.add('hidden');
            document.getElementById('default-tips').classList.remove('hidden');
            removePaymentCard();
        });
    }

    // ------------------------------------------------------------------
    // Remove QR-specific cards
    // ------------------------------------------------------------------
    function removePaymentCard() {
        const existing = document.getElementById('qr-payment-card');
        if (existing) existing.remove();
        const payBtn = document.getElementById('qr-proceed-pay');
        if (payBtn) payBtn.remove();
    }

    // ------------------------------------------------------------------
    // Build Payment Details Card
    // ------------------------------------------------------------------
    function buildPaymentCard(data) {
        removePaymentCard();

        const container = document.getElementById('result-container');
        if (!container) return;

        const card = document.createElement('div');
        card.id = 'qr-payment-card';
        card.className = 'mt-6 bg-[#0d181e] border border-[#1a2c32] rounded-2xl overflow-hidden shadow-xl animate-in fade-in slide-in-from-bottom-2 duration-500';

        // Header
        const header = document.createElement('div');
        header.className = 'px-6 py-4 border-b border-[#1a2c32] flex items-center gap-3';
        header.innerHTML = `
            <span class="material-symbols-outlined text-primary text-xl">account_balance_wallet</span>
            <h3 class="text-[13px] font-bold text-white uppercase tracking-widest">Payment Destination</h3>
        `;
        card.appendChild(header);

        // Details Grid
        const grid = document.createElement('div');
        grid.className = 'p-6 grid grid-cols-1 sm:grid-cols-2 gap-4';

        const fields = [
            { label: 'Pay To (UPI ID)', value: data.payment_to, icon: 'person' },
            { label: 'Payee Name', value: data.payee_name, icon: 'store' },
            { label: 'Amount', value: data.amount ? `₹${data.amount}` : 'Not specified', icon: 'currency_rupee' },
            { label: 'Processor', value: data.processor || 'Unknown', icon: 'account_balance' },
        ];

        fields.forEach(f => {
            if (!f.value && f.label !== 'Amount') return;
            const item = document.createElement('div');
            item.className = 'flex items-center gap-3 p-3 rounded-xl bg-[#121f26] border border-[#1a2c32] transition-colors hover:border-primary/20';
            item.innerHTML = `
                <div class="size-9 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20 shrink-0">
                    <span class="material-symbols-outlined text-primary text-[18px]">${f.icon}</span>
                </div>
                <div class="min-w-0">
                    <p class="text-[9px] uppercase text-primary/70 font-black tracking-widest mb-0.5">${f.label}</p>
                    <p class="text-[13px] text-white font-medium truncate">${f.value || '—'}</p>
                </div>
            `;
            grid.appendChild(item);
        });

        card.appendChild(grid);
        container.appendChild(card);

        // ---- Proceed to Pay Button (only for safe) ----
        if (data.status === 'safe' && data.upi_uri) {
            const payBtnWrapper = document.createElement('div');
            payBtnWrapper.id = 'qr-proceed-pay';
            payBtnWrapper.className = 'mt-4 animate-in fade-in slide-in-from-bottom-2 duration-500';
            payBtnWrapper.innerHTML = `
                <a href="${data.upi_uri}" 
                   class="w-full rounded-2xl h-14 bg-green-500 text-white font-black tracking-[0.1em] text-[13px] uppercase flex items-center justify-center gap-2.5 shadow-[0_4px_20px_rgba(34,197,94,0.3)] hover:shadow-[0_4px_25px_rgba(34,197,94,0.5)] hover:bg-green-400 transition-all hover:scale-[1.01] no-underline">
                    <span class="material-symbols-outlined text-[22px]">payments</span>
                    Proceed to Pay
                </a>
                <p class="text-center text-[10px] text-slate-500 mt-3 font-medium">
                    <span class="material-symbols-outlined text-[12px] align-middle mr-1">verified_user</span>
                    This payment destination has been verified as safe by SignalSafe
                </p>
            `;
            container.appendChild(payBtnWrapper);
        } else if (data.status === 'blocked') {
            const warnWrapper = document.createElement('div');
            warnWrapper.id = 'qr-proceed-pay';
            warnWrapper.className = 'mt-4 animate-in fade-in slide-in-from-bottom-2 duration-500';
            warnWrapper.innerHTML = `
                <div class="w-full rounded-2xl h-14 bg-red-500/10 border border-red-500/30 text-red-400 font-black tracking-[0.1em] text-[13px] uppercase flex items-center justify-center gap-2.5 cursor-not-allowed">
                    <span class="material-symbols-outlined text-[22px]">block</span>
                    Payment Blocked
                </div>
                <p class="text-center text-[10px] text-red-400/70 mt-3 font-medium">
                    <span class="material-symbols-outlined text-[12px] align-middle mr-1">warning</span>
                    SignalSafe has identified this as a potentially fraudulent payment destination
                </p>
            `;
            container.appendChild(warnWrapper);
        } else if (data.status === 'suspicious') {
            const warnWrapper = document.createElement('div');
            warnWrapper.id = 'qr-proceed-pay';
            warnWrapper.className = 'mt-4 animate-in fade-in slide-in-from-bottom-2 duration-500';
            warnWrapper.innerHTML = `
                <div class="w-full rounded-2xl h-14 bg-yellow-500/10 border border-yellow-500/30 text-yellow-400 font-black tracking-[0.1em] text-[13px] uppercase flex items-center justify-center gap-2.5 cursor-not-allowed">
                    <span class="material-symbols-outlined text-[22px]">gpp_maybe</span>
                    Payment Not Recommended
                </div>
                <p class="text-center text-[10px] text-yellow-400/70 mt-3 font-medium">
                    <span class="material-symbols-outlined text-[12px] align-middle mr-1">warning</span>
                    Suspicious indicators detected — proceed with extreme caution
                </p>
            `;
            container.appendChild(warnWrapper);
        }
    }

    // ------------------------------------------------------------------
    // Analyze
    // ------------------------------------------------------------------
    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        KavachApp.setLoading(analyzeBtn, true);
        removePaymentCard();

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);

            const response = await fetch('/api/qrcode/analyze', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const data = await response.json();
            lastAnalysisData = data;
            
            KavachApp.displayResult('result-container', data);
            buildPaymentCard(data);
            KavachApp.setLoading(analyzeBtn, false);

        } catch (err) {
            console.error('QR analysis failed:', err);
            KavachApp.displayResult('result-container', {
                risk_score: 95,
                status: 'blocked',
                reasons: ['QR decoding failed or server error.', err.message],
            });
            KavachApp.setLoading(analyzeBtn, false);
        }
    });
})();
