import React, { useState, useEffect, useRef } from 'react';

export default function CameraModal({ isOpen, onClose, onCapture, title = 'Camera Scan' }) {
  const videoRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [devices, setDevices] = useState([]);
  const [currentDeviceIndex, setCurrentDeviceIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [cameraError, setCameraError] = useState(null);

  // Initialize camera and enumerate devices when opened
  useEffect(() => {
    if (!isOpen) return;

    let activeStream = null;
    let isCancelled = false;

    async function initCamera() {
      setIsLoading(true);
      setCameraError(null);

      try {
        // Enumerate video devices
        let videoDevices = [];
        try {
          const allDevices = await navigator.mediaDevices.enumerateDevices();
          videoDevices = allDevices.filter((d) => d.kind === 'videoinput');
          setDevices(videoDevices);
        } catch (enumErr) {
          console.warn('Could not enumerate video devices:', enumErr);
        }

        const device = videoDevices[currentDeviceIndex];
        const constraints = {
          video: device
            ? { deviceId: { exact: device.deviceId }, width: { ideal: 1280 }, height: { ideal: 720 } }
            : { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } },
        };

        const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
        if (isCancelled) {
          mediaStream.getTracks().forEach((track) => track.stop());
          return;
        }

        activeStream = mediaStream;
        setStream(mediaStream);

        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
          videoRef.current.play().catch((playErr) => console.warn('Video play error:', playErr));
        }
        setIsLoading(false);
      } catch (err) {
        if (!isCancelled) {
          console.error('Camera access error:', err);
          setCameraError(err.message || 'Unable to access camera. Please verify camera permissions.');
          setIsLoading(false);
        }
      }
    }

    initCamera();

    return () => {
      isCancelled = true;
      if (activeStream) {
        activeStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [isOpen, currentDeviceIndex]);

  const handleSwitchCamera = () => {
    if (devices.length > 1) {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
      setCurrentDeviceIndex((prev) => (prev + 1) % devices.length);
    }
  };

  const handleCapture = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          const file = new File([blob], 'camera_capture.jpg', { type: 'image/jpeg' });
          onCapture(file);
          handleClose();
        }
      },
      'image/jpeg',
      0.92
    );
  };

  const handleClose = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
    setStream(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(36, 50, 71, 0.45)',
      backdropFilter: 'blur(3px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      zIndex: 100,
    }}>
      <div style={{
        backgroundColor: '#FFFFFF',
        border: '1px solid #E5EAF1',
        borderRadius: '16px',
        maxWidth: '560px',
        width: '100%',
        padding: '24px',
        boxShadow: 'var(--shadow-modal)',
        position: 'relative',
      }}>
        {/* Modal Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '16px',
          paddingBottom: '12px',
          borderBottom: '1px solid #E5EAF1',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="material-symbols-outlined" style={{ color: '#2563EB', fontSize: '20px' }}>
              photo_camera
            </span>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#243247' }}>
              {title}
            </h3>
          </div>

          <button
            onClick={handleClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#68778D',
              cursor: 'pointer',
              padding: '4px',
              borderRadius: '6px',
            }}
            aria-label="Close camera"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        {/* Video Viewport Container */}
        <div style={{
          width: '100%',
          height: '320px',
          backgroundColor: '#0F172A',
          borderRadius: '12px',
          overflow: 'hidden',
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '1px solid #E2E8F0',
        }}>
          {isLoading && (
            <div style={{ color: '#FFFFFF', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
              <span className="material-symbols-outlined spin-icon" style={{ fontSize: '28px', color: '#60A5FA' }}>
                sync
              </span>
              <span style={{ fontSize: '13px' }}>Initializing camera...</span>
            </div>
          )}

          {cameraError ? (
            <div style={{
              padding: '20px',
              textAlign: 'center',
              color: '#F87171',
              fontSize: '13px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '32px' }}>videocam_off</span>
              <p>{cameraError}</p>
            </div>
          ) : (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                display: isLoading ? 'none' : 'block',
              }}
            />
          )}

          {/* Alignment Target Reticle */}
          {!isLoading && !cameraError && (
            <div style={{
              position: 'absolute',
              width: '180px',
              height: '180px',
              border: '2px dashed rgba(255, 255, 255, 0.65)',
              borderRadius: '12px',
              pointerEvents: 'none',
            }} />
          )}
        </div>

        {/* Action Controls */}
        <div style={{
          marginTop: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
        }}>
          {devices.length > 1 ? (
            <button
              onClick={handleSwitchCamera}
              className="btn-secondary"
              style={{ fontSize: '13px' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>flip_camera_ios</span>
              <span>Switch Camera</span>
            </button>
          ) : (
            <div />
          )}

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={handleClose}
              className="btn-secondary"
              style={{ fontSize: '13px' }}
            >
              Cancel
            </button>

            <button
              onClick={handleCapture}
              className="btn-primary"
              disabled={isLoading || !!cameraError}
              style={{ fontSize: '13.5px', padding: '10px 20px' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>camera</span>
              <span>Capture Photo</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
