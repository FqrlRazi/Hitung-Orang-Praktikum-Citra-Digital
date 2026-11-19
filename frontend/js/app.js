const fileInput = document.querySelector("#image-file");
const dropzone = document.querySelector("#dropzone");
const previewImage = document.querySelector("#preview-image");
const uploadIcon = document.querySelector("#upload-icon");
const fileName = document.querySelector("#file-name");
const fileHint = document.querySelector("#file-hint");
const analyzeButton = document.querySelector("#analyze-button");
const buttonLabel = document.querySelector("#button-label");
const buttonSpinner = document.querySelector("#button-spinner");
const buttonArrow = document.querySelector("#button-arrow");
const errorMessage = document.querySelector("#error-message");
const resultCount = document.querySelector("#result-count");
const resultHeading = document.querySelector("#result-heading");
const resultUnit = document.querySelector("#result-unit");
const resultMeta = document.querySelector("#result-meta");
const visualTitle = document.querySelector("#visual-title");
const visualDescription = document.querySelector("#visual-description");
const resultPlaceholder = document.querySelector("#result-placeholder");
const resultImage = document.querySelector("#result-image");
const maskImage = document.querySelector("#mask-image");
const viewTabs = document.querySelector("#view-tabs");
const detectionTab = document.querySelector("#detection-tab");
const maskTab = document.querySelector("#mask-tab");
const faceMaskTab = document.querySelector("#face-mask-tab");
const faceMaskImage = document.querySelector("#face-mask-image");
const visualNote = document.querySelector("#visual-note");
const downloadButton = document.querySelector("#download-button");
const analysisReport = document.querySelector("#analysis-report");
const reportStatus = document.querySelector("#report-status");
const reportSegmentation = document.querySelector("#report-segmentation");
const reportMethod = document.querySelector("#report-method");
const reportBackground = document.querySelector("#report-background");
const reportRows = document.querySelector("#report-rows");
const reportConclusion = document.querySelector("#report-conclusion");

let selectedFile = null;
let previewUrl = null;
let annotatedUrl = null;
let maskUrl = null;
let faceMaskUrl = null;

function showVisualization(view) {
  const showingDetection = view === "detection";
  const showingFaceMask = view === "face-mask";
  resultImage.classList.toggle("hidden", !showingDetection);
  maskImage.classList.toggle("hidden", view !== "mask");
  faceMaskImage.classList.toggle("hidden", !showingFaceMask);
  detectionTab.setAttribute("aria-pressed", String(showingDetection));
  maskTab.setAttribute("aria-pressed", String(view === "mask"));
  faceMaskTab.setAttribute("aria-pressed", String(showingFaceMask));
  visualNote.classList.toggle("hidden", view === "detection");
  if (view === "mask") {
    visualNote.textContent =
      "Ini mask foreground dari segmentasi warna: putih = area yang berbeda dari latar, hitam = area yang dianggap latar. Mask ini bukan segmentasi wajah dan tidak menentukan kotak deteksi wajah.";
  } else if (showingFaceMask) {
    visualNote.textContent =
      "Ini mask kotak wajah: area putih berasal dari kotak deteksi wajah YuNet dan area hitam berada di luar kotak wajah.";
  }
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.classList.remove("hidden");
}

function clearError() {
  errorMessage.textContent = "";
  errorMessage.classList.add("hidden");
}

async function readApiJson(response, fallbackMessage) {
  const body = await response.text();
  let data;
  try {
    data = JSON.parse(body);
  } catch {
    throw new Error(
      response.ok
        ? fallbackMessage
        : `Server error (${response.status}). Periksa log deployment Vercel.`,
    );
  }
  if (!response.ok) throw new Error(data.detail || fallbackMessage);
  return data;
}

function selectFile(file) {
  clearError();
  if (!file) return;
  const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
  if (!allowedTypes.includes(file.type)) {
    showError("Pilih file gambar JPG, PNG, atau WebP.");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showError("Ukuran file maksimal 10 MB.");
    return;
  }

  selectedFile = file;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  previewImage.src = previewUrl;
  previewImage.classList.remove("hidden");
  uploadIcon.classList.add("hidden");
  fileName.textContent = file.name;
  fileHint.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB · klik untuk mengganti`;
  analyzeButton.disabled = false;
  buttonLabel.textContent = "Mulai analisis";
  resultCount.textContent = "—";
  resultUnit.textContent = "menunggu analisis";
  resultMeta.textContent = "Hasil segmentasi dan kontur akan tampil di sini.";
  resultImage.classList.add("hidden");
  resultPlaceholder.classList.remove("hidden");
  viewTabs.classList.add("hidden");
  downloadButton.classList.add("hidden");
  visualNote.classList.add("hidden");
  analysisReport.classList.add("hidden");
}

fileInput.addEventListener("change", (event) => selectFile(event.target.files[0]));

for (const eventName of ["dragenter", "dragover"]) {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add("drag-over");
  });
}
for (const eventName of ["dragleave", "drop"]) {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove("drag-over");
  });
}
dropzone.addEventListener("drop", (event) => {
  const [file] = event.dataTransfer.files;
  selectFile(file);
});

analyzeButton.addEventListener("click", async () => {
  if (!selectedFile) return;
  clearError();
  analyzeButton.disabled = true;
  buttonSpinner.classList.remove("hidden");
  buttonArrow.classList.add("hidden");
  buttonLabel.textContent = "Sedang menganalisis...";

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const response = await fetch("/api/analyze", { method: "POST", body: formData });
    const data = await readApiJson(response, "Gagal memproses gambar.");

    annotatedUrl = `data:image/png;base64,${data.annotated_image}`;
    maskUrl = `data:image/png;base64,${data.mask_image}`;
    faceMaskUrl = `data:image/png;base64,${data.face_mask_image}`;
    resultImage.src = annotatedUrl;
    resultImage.classList.remove("hidden");
    resultPlaceholder.classList.add("hidden");
    maskImage.src = maskUrl;
    faceMaskImage.src = faceMaskUrl;
    viewTabs.classList.remove("hidden");
    viewTabs.classList.add("flex");
    const usesFaceDetection = data.detection_method === "wajah";
    resultHeading.textContent = usesFaceDetection ? "Wajah terdeteksi" : "Objek terdeteksi";
    visualTitle.textContent = usesFaceDetection ? "Hasil deteksi wajah" : "Hasil kontur objek";
    visualDescription.textContent = usesFaceDetection
      ? "Kotak hijau berasal dari detektor wajah YuNet."
      : "Kotak hijau berasal dari analisis kontur.";
    resultImage.alt = usesFaceDetection
      ? "Deteksi wajah YuNet dengan kotak penanda"
      : "Deteksi kontur objek dengan kotak penanda";
    detectionTab.textContent = usesFaceDetection ? "Deteksi wajah" : "Deteksi kontur";
    maskTab.textContent = "Mask latar";
    showVisualization("detection");
    downloadButton.classList.remove("hidden");
    resultCount.textContent = data.count;
    resultUnit.textContent = usesFaceDetection ? "wajah terdeteksi" : "objek terdeteksi";
    const methodLabel = usesFaceDetection
      ? "dihitung oleh detektor wajah YuNet"
      : `${data.detections.length} kontur lolos penyaringan`;
    resultMeta.textContent = `${data.image_width} × ${data.image_height} piksel · ${methodLabel}`;
    analysisReport.classList.remove("hidden");
    reportStatus.textContent = `${data.count} objek`;
    reportSegmentation.textContent = data.segmentation_method;
    reportMethod.textContent = usesFaceDetection
      ? "YuNet Face Detection"
      : "External Contour Analysis";
    reportBackground.textContent = `RGB (${data.background_color.join(", ")})`;
    const reportedDetections = usesFaceDetection
      ? data.detections
      : (data.contour_detections || data.detections);
    reportRows.innerHTML = reportedDetections
      .map((detection, index) => {
        const shape = detection.shape || "Tidak diketahui";
        const aspectRatio = Number(detection.aspect_ratio || 0).toFixed(2);
        const shapeSource = detection.shape_source || "Analisis kontur";
        const confidence = Number(detection.confidence ?? detection.shape_confidence ?? 0).toFixed(1);
        const confidenceLabel = detection.confidence !== undefined
          ? "confidence wajah"
          : "kecocokan bentuk";
        return `<tr class="border-t border-black/5"><td class="py-3 pr-4 font-semibold">#${index + 1}</td><td class="py-3 pr-4">${shape}</td><td class="py-3 pr-4">${detection.width} × ${detection.height} px</td><td class="py-3 text-black/55">rasio aspek ${aspectRatio}<br><span class="text-[11px]">${confidenceLabel} ${confidence}%</span><br><span class="text-[11px]">${shapeSource}</span></td></tr>`;
      })
      .join("");
    reportConclusion.textContent = usesFaceDetection
      ? `Sistem mendeteksi ${data.count} wajah dengan model YuNet. Hasil kontur latar tetap tersedia pada mask untuk menjelaskan proses segmentasi.`
      : `Sistem segmentasi menghasilkan ${data.count} kontur yang lolos luas minimum. Bentuk diklasifikasikan dari pendekatan poligon dan rasio aspek batas kontur.`;
  } catch (error) {
    showError(error instanceof Error ? error.message : "Terjadi kesalahan saat memproses gambar.");
  } finally {
    analyzeButton.disabled = false;
    buttonSpinner.classList.add("hidden");
    buttonArrow.classList.remove("hidden");
    buttonLabel.textContent = "Analisis ulang";
  }
});

detectionTab.addEventListener("click", () => showVisualization("detection"));
maskTab.addEventListener("click", () => showVisualization("mask"));
faceMaskTab.addEventListener("click", () => showVisualization("face-mask"));

downloadButton.addEventListener("click", async () => {
  if (!selectedFile) return;
  clearError();

  const previousText = downloadButton.textContent;
  downloadButton.disabled = true;
  downloadButton.textContent = "Membuat PDF...";

  try {
    const formData = new FormData();
    formData.append("file", selectedFile);
    const response = await fetch("/api/report/pdf", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      await readApiJson(response, "Gagal membuat laporan PDF.");
    }

    const pdfBlob = await response.blob();
    const pdfUrl = URL.createObjectURL(pdfBlob);
    const anchor = document.createElement("a");
    const sourceName = selectedFile.name.replace(/\.[^.]+$/, "") || "hasil";
    anchor.href = pdfUrl;
    anchor.download = `laporan-${sourceName}.pdf`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(pdfUrl);
  } catch (error) {
    showError(error instanceof Error ? error.message : "Gagal mengunduh laporan PDF.");
  } finally {
    downloadButton.disabled = false;
    downloadButton.textContent = previousText;
  }
});
