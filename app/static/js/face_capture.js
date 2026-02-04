document.addEventListener("DOMContentLoaded", () => {
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const photo = document.getElementById("photo");
    const startBtn = document.getElementById("start-camera");
    const stopBtn = document.getElementById("stop-camera");
    const captureBtn = document.getElementById("capture-btn");
    const retakeBtn = document.getElementById("retake-btn");
    const saveBtn = document.getElementById("save-btn");
    const loading = document.getElementById("loading");
    let stream;

    startBtn.addEventListener("click", async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            video.style.display = 'block';
            photo.style.display = 'none';
            captureBtn.disabled = false;

            // UI Toggle
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-block';
            captureBtn.style.display = 'inline-block';
            retakeBtn.style.display = 'none';
            saveBtn.style.display = 'none';
        } catch (err) {
            console.error("Webcam Error:", err);
            alert("Could not access webcam. Please check permissions.");
        }
    });

    stopBtn.addEventListener("click", () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            video.srcObject = null;
        }

        // UI Reset
        startBtn.style.display = 'inline-block';
        stopBtn.style.display = 'none';
        captureBtn.style.display = 'inline-block';
        captureBtn.disabled = true;
        retakeBtn.style.display = 'none';
        saveBtn.style.display = 'none';

        // Reset View
        video.style.display = 'block';
        photo.style.display = 'none';
    });

    captureBtn.addEventListener("click", () => {
        const context = canvas.getContext("2d");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);

        const dataUrl = canvas.toDataURL("image/jpeg");
        photo.src = dataUrl;

        video.style.display = "none";
        photo.style.display = "block";

        captureBtn.style.display = "none";
        stopBtn.style.display = "none"; // Hide stop when captured
        retakeBtn.style.display = "inline-block";
        saveBtn.style.display = "inline-block";
    });

    retakeBtn.addEventListener("click", () => {
        photo.style.display = "none";
        video.style.display = "block";

        captureBtn.style.display = "inline-block";
        stopBtn.style.display = "inline-block"; // Show stop again
        retakeBtn.style.display = "none";
        saveBtn.style.display = "none";
    });

    saveBtn.addEventListener("click", () => {
        const dataUrl = photo.src;
        const studentId = document.getElementById("student-id").value;
        const uploadUrl = document.getElementById("upload-url").value;
        const csrfToken = document.getElementById("csrf-token").value;

        // Show loading spinner
        loading.classList.remove("d-none");
        loading.classList.add("d-flex");
        saveBtn.disabled = true;
        retakeBtn.disabled = true;

        fetch(uploadUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                image: dataUrl,
                student_id: studentId
            })
        })
            .then(response => {
                if (!response.ok) {
                    // If server returns 500 or 400
                    return response.json().then(errData => {
                        throw new Error(errData.message || "Server Error: " + response.status);
                    }).catch(e => {
                        // Fallback if json parse fails
                        throw new Error("Server Error: " + response.statusText);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    alert("Face Data Registered Successfully!");
                    window.location.href = "/admin/dashboard";
                } else {
                    throw new Error(data.message);
                }
            })
            .catch(err => {
                console.error(err);
                alert("Registration Failed: " + err.message);
                loading.classList.remove("d-flex");
                loading.classList.add("d-none");
                saveBtn.disabled = false;
                retakeBtn.disabled = false;
            });
    });
});
