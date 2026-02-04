document.addEventListener("DOMContentLoaded", () => {
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const context = canvas.getContext("2d");
    const logWindow = document.getElementById("log-window");
    const presentCount = document.getElementById("present-count");

    // Config
    const sessionId = document.getElementById("session-id").value;
    const csrfToken = document.getElementById("csrf-token").value;

    const refreshBtn = document.getElementById("refresh-db-btn");

    // State
    let isProcessing = false;

    // Refresh DB Handler
    if (refreshBtn) {
        refreshBtn.addEventListener("click", async () => {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Reloading...';

            try {
                const response = await fetch(`/faculty/refresh_cache_manual/${sessionId}`, {
                    method: 'POST',
                    headers: { "X-CSRFToken": csrfToken }
                });
                const data = await response.json();
                if (data.success) {
                    logEvent("Database Refreshed: " + data.count + " students loaded.", "success");
                } else {
                    logEvent("Refresh Failed: " + data.message, "error");
                }
            } catch (e) {
                logEvent("Refresh Error: " + e.message, "error");
            } finally {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-1"></i> Refresh DB';
            }
        });
    }

    // 1. Initialize Camera
    navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } })
        .then(stream => {
            video.srcObject = stream;
            logEvent("Camera stream acquired.", "system");
        })
        .catch(err => {
            console.error("Camera Error:", err);
            logEvent("CRITICAL: Camera access denied.", "error");
        });

    // 2. Loop
    video.addEventListener('play', () => {
        // Main canvas for drawing boxes (overlay)
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // Offscreen canvas for sending data (smaller = faster)
        const sendCanvas = document.createElement('canvas');
        const sendWidth = 800; // Balanced: 800px is good for RetinaFace speed vs accuracy

        setInterval(async () => {
            if (video.paused || video.ended || isProcessing) return;

            // Sync Main Canvas size if window resized
            if (canvas.width !== video.videoWidth) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
            }

            // Sync Send Canvas size (maintain aspect ratio)
            const aspectRatio = video.videoWidth / video.videoHeight;
            const sendHeight = sendWidth / aspectRatio;
            sendCanvas.width = sendWidth;
            sendCanvas.height = sendHeight;

            // Draw video to OFFSCREEN canvas for sending
            const sendContext = sendCanvas.getContext("2d");
            sendContext.drawImage(video, 0, 0, sendCanvas.width, sendCanvas.height);

            // Capture Data (smaller image)
            const dataUrl = sendCanvas.toDataURL("image/jpeg", 0.7);

            // Send to Backend
            isProcessing = true;
            try {
                const response = await fetch("/faculty/process_frame", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken
                    },
                    body: JSON.stringify({ image: dataUrl, session_id: sessionId })
                });

                const data = await response.json();

                // 3. Draw Bounding Boxes on MAIN canvas
                // Clear the main canvas to show the video underneath
                context.clearRect(0, 0, canvas.width, canvas.height);

                if (data.detected_faces && data.detected_faces.length > 0) {
                    // Calculate Scale Factors (Main / Sent)
                    const scaleX = canvas.width / sendCanvas.width;
                    const scaleY = canvas.height / sendCanvas.height;

                    data.detected_faces.forEach(face => {
                        // Rescale box to match video display
                        const x = face.box.x * scaleX;
                        const y = face.box.y * scaleY;
                        const w = face.box.w * scaleX;
                        const h = face.box.h * scaleY;

                        const name = face.name;
                        const isMatch = face.match;

                        // Style
                        context.lineWidth = 3;
                        context.strokeStyle = isMatch ? "#00ff88" : "#ff3366"; // Green vs Red
                        context.strokeRect(x, y, w, h);

                        // Label
                        context.fillStyle = isMatch ? "#00ff88" : "#ff3366";
                        context.font = "bold 18px Courier New";
                        context.fillText(name, x, y - 10);
                    });
                }

                // 4. Handle New Attendance
                if (data.new_students && data.new_students.length > 0) {
                    data.new_students.forEach(student => {
                        logEvent(`New Attendance: ${student.name} (${student.roll_no})`, "success");
                        // Play Beep
                        playBeep();

                        // Update Counter
                        let count = parseInt(presentCount.innerText) || 0;
                        presentCount.innerText = count + 1;
                    });
                }

            } catch (err) {
                console.error("Processing Error:", err);
            } finally {
                isProcessing = false;
            }

        }, 500); // 500ms loop (2 FPS) - Reduced from 300ms for performance
    });

    function logEvent(msg, type = "info") {
        const div = document.createElement("div");
        div.className = "log-entry";
        const time = new Date().toLocaleTimeString();

        if (type === "success") div.classList.add("log-success");
        if (type === "error") div.classList.add("log-error");

        div.innerText = `[${time}] ${msg}`;
        logWindow.appendChild(div);
        logWindow.scrollTop = logWindow.scrollHeight; // Auto scroll
    }

    function playBeep() {
        // Simple oscillator beep
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        oscillator.type = "sine";
        oscillator.frequency.value = 880; // A5
        gainNode.gain.value = 0.1;

        oscillator.start();
        setTimeout(() => oscillator.stop(), 200);
    }
});
