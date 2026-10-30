/* ============================================
   KAVACH – Camera Module
   Handles getUserMedia and live capture
   ============================================ */

const KavachCamera = {
    stream: null,
    onCapture: null,
    videoDevices: [],
    currentDeviceIndex: 0,
    playTimeout: null,

    async open(callback) {
        this.onCapture = callback;
        const modal = document.getElementById('camera-modal');
        const video = document.getElementById('camera-video');
        const captureBtn = document.getElementById('camera-capture-btn');
        const closeBtn = document.getElementById('camera-close-btn');
        const switchBtn = document.getElementById('camera-switch-btn');
        const fallbackBtn = document.getElementById('camera-fallback-btn');
        const loading = document.getElementById('camera-loading');

        modal.classList.remove('hidden');
        modal.classList.add('flex');
        if (loading) {
            loading.classList.remove('hidden');
            loading.classList.add('flex');
        }

        // Show loading/starting state
        video.onplaying = () => {
            if (loading) loading.classList.add('hidden');
            if (this.playTimeout) clearTimeout(this.playTimeout);
        };

        // Enumerate devices
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.videoDevices = devices.filter(d => d.kind === 'videoinput');
            
            // Prioritize Integrated/Built-in cameras
            const laptopCameraIndex = this.videoDevices.findIndex(d => 
                d.label.toLowerCase().includes('integrated') || 
                d.label.toLowerCase().includes('built-in') ||
                d.label.toLowerCase().includes('front') ||
                d.label.toLowerCase().includes('webcam')
            );

            if (laptopCameraIndex !== -1) {
                this.currentDeviceIndex = laptopCameraIndex;
            }

            if (this.videoDevices.length > 1) {
                switchBtn.classList.remove('hidden');
            } else {
                switchBtn.classList.add('hidden');
            }
        } catch (e) {
            console.warn('Device enumeration failed:', e);
        }

        await this.startStream();

        // Button actions
        captureBtn.onclick = () => this.capture();
        closeBtn.onclick = () => this.close();
        switchBtn.onclick = () => this.switchCamera();
        fallbackBtn.onclick = () => {
            this.close();
            // Trigger the native file input capture instead
            const tab = KavachApp.currentTab;
            const inputId = tab === 'qrcode' ? 'qr-file' : 'screenshot-file';
            const input = document.getElementById(inputId);
            if (input) input.click();
        };

        // Set a timeout if camera doesn't start
        this.playTimeout = setTimeout(() => {
            if (modal.classList.contains('flex') && !video.paused) return; // Already playing
            alert('Camera is taking too long to connect. If you see a "Connecting..." popup, try switching cameras or use the "File Upload" option.');
        }, 8000);
    },

    async startStream() {
        if (this.stream) {
            this.stream.getTracks().forEach(t => t.stop());
        }

        const video = document.getElementById('camera-video');
        const device = this.videoDevices[this.currentDeviceIndex];
        
        let constraints = {
            video: { 
                facingMode: { ideal: 'environment' },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        };

        if (device) {
            constraints.video.deviceId = { exact: device.deviceId };
            // If we use exact deviceId, remove facingMode
            delete constraints.video.facingMode;
        }

        try {
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = this.stream;
            video.muted = true;
            await video.play();
        } catch (err) {
            console.error('Stream start failed:', err);
            // Fallback to generic if specific failed
            if (device) {
                try {
                    this.stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    video.srcObject = this.stream;
                    video.muted = true;
                    await video.play();
                } catch (e2) {
                    console.error('Generic fallback failed:', e2);
                }
            }
        }
    },

    async switchCamera() {
        if (this.videoDevices.length < 2) return;
        this.currentDeviceIndex = (this.currentDeviceIndex + 1) % this.videoDevices.length;
        const loading = document.getElementById('camera-loading');
        if (loading) loading.classList.remove('hidden');
        await this.startStream();
    },

    capture() {
        const video = document.getElementById('camera-video');
        const canvas = document.getElementById('camera-canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
        
        canvas.toBlob((blob) => {
            const file = new File([blob], "camera_capture.jpg", { type: "image/jpeg" });
            if (this.onCapture) this.onCapture(file);
            this.close();
        }, 'image/jpeg', 0.9);
    },

    close() {
        const modal = document.getElementById('camera-modal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');

        if (this.playTimeout) clearTimeout(this.playTimeout);

        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        const video = document.getElementById('camera-video');
        video.srcObject = null;
        
        const loading = document.getElementById('camera-loading');
        if (loading) loading.classList.remove('hidden');
    }
};
