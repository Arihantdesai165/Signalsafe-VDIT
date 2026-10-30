/* ============================================
   KAVACH – Screenshot Module
   Upload/capture + API integration
   ============================================ */

(function () {
    const fileInput = document.getElementById('screenshot-file');
    const cameraInput = document.getElementById('screenshot-camera');
    const uploadBtn = document.getElementById('screenshot-upload-btn');
    const cameraBtn = document.getElementById('screenshot-camera-btn');
    const analyzeBtn = document.getElementById('screenshot-analyze-btn');
    const preview = document.getElementById('screenshot-preview');
    const previewContainer = document.getElementById('preview-container');
    const placeholder = document.getElementById('screenshot-placeholder');
    const scanningOverlay = document.getElementById('scanning-overlay');
    const dropZone = document.getElementById('screenshot-drop-zone');

    let selectedFile = null;

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

        const nameEl = document.getElementById('screenshot-filename');
        if (nameEl) nameEl.textContent = file.name;

        showPreview(file);
        analyzeBtn.disabled = false;
        
        // Clear previous results when new file is selected
        document.getElementById('result-container').classList.add('hidden');
        document.getElementById('default-tips').classList.remove('hidden');
    }

    function showPreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.src = e.target.result;
            previewContainer.classList.remove('hidden');
            dropZone.classList.add('hidden');
        };
        reader.readAsDataURL(file);
    }
    
    const changeBtn = document.getElementById('screenshot-change-btn');
    if (changeBtn) {
        changeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            selectedFile = null;
            preview.src = '';
            previewContainer.classList.add('hidden');
            dropZone.classList.remove('hidden');
            analyzeBtn.disabled = true;
            fileInput.value = '';
            cameraInput.value = '';
            // Bring back tips
            document.getElementById('result-container').classList.add('hidden');
            document.getElementById('default-tips').classList.remove('hidden');
        });
    }

    // Analyze
    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        KavachApp.setLoading(analyzeBtn, true);
        if (scanningOverlay) scanningOverlay.classList.remove('hidden');
        
        try {
            const formData = new FormData();
            formData.append('file', selectedFile);

            const response = await fetch('/api/screenshot/analyze', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const data = await response.json();
            
            KavachApp.displayResult('result-container', data);
            if (scanningOverlay) scanningOverlay.classList.add('hidden');
            KavachApp.setLoading(analyzeBtn, false);

        } catch (err) {
            console.error('Screenshot analysis failed:', err);
            KavachApp.displayResult('result-container', {
                risk_score: 99,
                status: 'suspicious',
                reasons: ['System analysis encountered an error.', err.message],
            });
            if (scanningOverlay) scanningOverlay.classList.add('hidden');
            KavachApp.setLoading(analyzeBtn, false);
        }
    });
})();
