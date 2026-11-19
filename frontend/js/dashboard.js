const listElement = document.querySelector("#history-list");
const errorElement = document.querySelector("#history-error");

function escapeText(value) {
  const element = document.createElement("span");
  element.textContent = value;
  return element.innerHTML;
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

async function loadHistory() {
  try {
    const response = await fetch("/api/history?limit=100");
    const data = await readApiJson(response, "Gagal memuat riwayat.");

    const records = data.records || [];
    const average = records.length
      ? records.reduce((sum, record) => sum + Number(record.count || 0), 0) / records.length
      : 0;
    const faceRecords = records.filter((record) => record.detection_method === "wajah").length;

    document.querySelector("#total-records").textContent = records.length;
    document.querySelector("#average-count").textContent = average.toFixed(1);
    document.querySelector("#face-records").textContent = faceRecords;

    if (!records.length) {
      listElement.innerHTML = '<p class="px-5 py-8 text-sm text-black/45">Belum ada hasil analisis.</p>';
      return;
    }

    listElement.innerHTML = records.map((record) => {
      const date = new Date(record.created_at);
      const dateText = Number.isNaN(date.getTime())
        ? record.created_at
        : date.toLocaleString("id-ID");
      const method = record.detection_method === "wajah"
        ? "Deteksi wajah YuNet"
        : "Analisis kontur";
      return `
        <article class="grid gap-4 px-5 py-5 sm:grid-cols-[90px_1fr_auto] sm:items-center">
          <img class="h-16 w-20 rounded-lg bg-[#f6f7f2] object-cover" src="/api/history/${encodeURIComponent(record.id)}/image/annotated" alt="Citra hasil ${escapeText(record.file_name)}" />
          <div>
            <p class="font-semibold">${escapeText(record.file_name)}</p>
            <p class="mt-1 text-xs text-black/45">${escapeText(dateText)} · ${escapeText(method)}</p>
            <p class="mt-2 text-sm">${record.count} hasil · ${record.image_width} × ${record.image_height} piksel</p>
          </div>
          <a class="rounded-lg border border-[#1d5948]/20 px-3 py-2 text-center text-xs font-semibold text-[#1d5948]" href="/api/history/${encodeURIComponent(record.id)}/report/pdf">Unduh PDF</a>
        </article>
      `;
    }).join("");
  } catch (error) {
    errorElement.textContent = error instanceof Error ? error.message : "Gagal memuat riwayat.";
    errorElement.classList.remove("hidden");
  }
}

loadHistory();
