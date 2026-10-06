/* AUTHENTIX Camera QR Scanner & Manual Input Manager */

document.addEventListener('DOMContentLoaded', () => {
    const scannerRegion = document.getElementById('qr-reader');
    const startCamBtn = document.getElementById('start-camera-btn');
    const stopCamBtn = document.getElementById('stop-camera-btn');
    const qrRefInput = document.getElementById('qr_reference');
    const fileScanInput = document.getElementById('qr-file-input');

    let html5QrCode = null;

    if (startCamBtn && scannerRegion) {
        startCamBtn.addEventListener('click', () => {
            initCameraScanner();
        });
    }

    if (stopCamBtn) {
        stopCamBtn.addEventListener('click', () => {
            stopCameraScanner();
        });
    }

    function initCameraScanner() {
        if (typeof Html5Qrcode === 'undefined') {
            alert('HTML5 QR Scanner library is loading. Please try again in a moment or upload a QR image below.');
            return;
        }

        if (!html5QrCode) {
            html5QrCode = new Html5Qrcode("qr-reader");
        }

        scannerRegion.style.display = 'block';
        if (startCamBtn) startCamBtn.style.display = 'none';
        if (stopCamBtn) stopCamBtn.style.display = 'inline-block';

        const config = { fps: 10, qrbox: { width: 250, height: 250 } };

        html5QrCode.start(
            { facingMode: "environment" },
            config,
            onScanSuccess,
            onScanFailure
        ).catch(err => {
            console.warn("Camera start failed, prompting permission:", err);
            alert("Camera access denied or unavailable. You can upload a QR image or enter reference manually.");
            stopCameraScanner();
        });
    }

    function stopCameraScanner() {
        if (html5QrCode && html5QrCode.isScanning) {
            html5QrCode.stop().then(() => {
                scannerRegion.style.display = 'none';
                if (startCamBtn) startCamBtn.style.display = 'inline-block';
                if (stopCamBtn) stopCamBtn.style.display = 'none';
            }).catch(err => console.error(err));
        } else {
            if (scannerRegion) scannerRegion.style.display = 'none';
            if (startCamBtn) startCamBtn.style.display = 'inline-block';
            if (stopCamBtn) stopCamBtn.style.display = 'none';
        }
    }

    function onScanSuccess(decodedText, decodedResult) {
        console.log("QR Scanned successfully:", decodedText);
        stopCameraScanner();

        // Extract QR reference token from URL or text
        let refToken = decodedText;
        if (decodedText.includes('?t=')) {
            const urlObj = new URL(decodedText);
            refToken = urlObj.searchParams.get('t');
        } else if (decodedText.includes('/verify?t=')) {
            refToken = decodedText.split('?t=')[1].split('&')[0];
        }

        if (refToken) {
            window.location.href = `/verify?t=${encodeURIComponent(refToken)}`;
        } else {
            alert("Scanned QR does not contain a valid AUTHENTIX reference URL.");
        }
    }

    function onScanFailure(error) {
        // Silent loop handler for frames without QR code
    }

    // Handle File upload QR decoding
    if (fileScanInput) {
        fileScanInput.addEventListener('change', (e) => {
            if (e.target.files.length === 0) return;
            const imageFile = e.target.files[0];
            
            if (typeof Html5Qrcode === 'undefined') {
                alert('QR Scanner library not loaded. Please refresh page.');
                return;
            }

            const html5QrCodeFile = new Html5Qrcode("qr-reader-file-temp");
            html5QrCodeFile.scanFile(imageFile, true)
                .then(decodedText => {
                    onScanSuccess(decodedText, null);
                })
                .catch(err => {
                    alert("Could not detect a clear QR code in uploaded image. Please try another image or camera scan.");
                });
        });
    }
});
