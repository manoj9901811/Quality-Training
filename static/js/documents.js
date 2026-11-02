/* =========================================================
   QT PLATFORM - DOCUMENTS JS
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    initFileUpload();
    formatFileSizes();
    initLucide();

});


/* =========================================================
   LUCIDE
   ========================================================= */

function initLucide() {

    if (typeof lucide !== "undefined") {
        lucide.createIcons();
    }

}


/* =========================================================
   UPLOAD MODAL
   ========================================================= */

window.openUploadModal = function () {

    const modal = document.getElementById("uploadModal");

    if (!modal) return;

    modal.classList.add("active");

    document.body.classList.add("modal-open");

    initLucide();

};


window.closeUploadModal = function () {

    const modal = document.getElementById("uploadModal");

    if (!modal) return;

    modal.classList.remove("active");

    document.body.classList.remove("modal-open");

};


window.closeModalOnOverlay = function (event) {

    if (event.target === event.currentTarget) {
        closeUploadModal();
    }

};


/* =========================================================
   FILE UPLOAD
   ========================================================= */

function initFileUpload() {

    const fileInput = document.getElementById("document_file");

    const dropzone = document.getElementById("uploadDropzone");

    if (!fileInput || !dropzone) return;


    fileInput.addEventListener("change", function () {

        if (this.files && this.files.length > 0) {
            handleSelectedFile(this.files[0]);
        }

    });


    dropzone.addEventListener("dragover", function (event) {

        event.preventDefault();

        dropzone.classList.add("dragover");

    });


    dropzone.addEventListener("dragleave", function () {

        dropzone.classList.remove("dragover");

    });


    dropzone.addEventListener("drop", function (event) {

        event.preventDefault();

        dropzone.classList.remove("dragover");

        const files = event.dataTransfer.files;

        if (!files || !files.length) return;

        const file = files[0];

        const dataTransfer = new DataTransfer();

        dataTransfer.items.add(file);

        fileInput.files = dataTransfer.files;

        handleSelectedFile(file);

    });

}


/* =========================================================
   SELECT FILE
   ========================================================= */

function handleSelectedFile(file) {

    const maxSize = 10 * 1024 * 1024;

    if (file.size > maxSize) {

        alert("File size cannot exceed 10 MB.");

        clearSelectedFile();

        return;
    }


    const allowedExtensions = [
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "csv",
        "ppt",
        "pptx",
        "txt",
        "jpg",
        "jpeg",
        "png"
    ];


    const extension = file.name
        .split(".")
        .pop()
        .toLowerCase();


    if (!allowedExtensions.includes(extension)) {

        alert(
            "This file type is not allowed.\n\n" +
            "Allowed: PDF, DOC, DOCX, XLS, XLSX, CSV, PPT, PPTX, TXT, JPG, JPEG, PNG."
        );

        clearSelectedFile();

        return;
    }


    const placeholder =
        document.getElementById("uploadPlaceholder");

    const selectedFile =
        document.getElementById("selectedFile");

    const selectedFileName =
        document.getElementById("selectedFileName");

    const selectedFileSize =
        document.getElementById("selectedFileSize");


    if (placeholder) {
        placeholder.style.display = "none";
    }


    if (selectedFile) {
        selectedFile.style.display = "flex";
    }


    if (selectedFileName) {
        selectedFileName.textContent = file.name;
    }


    if (selectedFileSize) {
        selectedFileSize.textContent =
            formatBytes(file.size);
    }


    initLucide();

}


/* =========================================================
   CLEAR FILE
   ========================================================= */

window.clearSelectedFile = function (event) {

    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }


    const fileInput =
        document.getElementById("document_file");

    const placeholder =
        document.getElementById("uploadPlaceholder");

    const selectedFile =
        document.getElementById("selectedFile");


    if (fileInput) {
        fileInput.value = "";
    }


    if (placeholder) {
        placeholder.style.display = "flex";
    }


    if (selectedFile) {
        selectedFile.style.display = "none";
    }

};


/* =========================================================
   FILE SIZE
   ========================================================= */

function formatBytes(bytes) {

    if (!bytes || bytes === 0) {
        return "0 Bytes";
    }


    const units = [
        "Bytes",
        "KB",
        "MB",
        "GB"
    ];


    const index =
        Math.floor(
            Math.log(bytes) / Math.log(1024)
        );


    const value =
        bytes / Math.pow(1024, index);


    return (
        value.toFixed(index === 0 ? 0 : 2) +
        " " +
        units[index]
    );

}


function formatFileSizes() {

    const elements =
        document.querySelectorAll(
            ".file-size[data-size]"
        );


    elements.forEach(function (element) {

        const bytes =
            parseInt(
                element.getAttribute("data-size"),
                10
            );


        if (!isNaN(bytes)) {
            element.textContent =
                formatBytes(bytes);
        }

    });

}


/* =========================================================
   DELETE MODAL
   ========================================================= */

let deleteDocumentId = null;


window.confirmDelete = function (
    documentId,
    documentName
) {

    deleteDocumentId = documentId;


    const hiddenInput =
        document.getElementById("deleteDocumentId");

    const message =
        document.getElementById("deleteMessage");

    const modal =
        document.getElementById("deleteModal");


    if (hiddenInput) {
        hiddenInput.value = documentId;
    }


    if (message) {

        message.textContent =
            "Are you sure you want to delete \"" +
            documentName +
            "\"? This action cannot be undone.";

    }


    if (modal) {
        modal.classList.add("active");
    }


    document.body.classList.add("modal-open");

    initLucide();

};


window.closeDeleteModal = function () {

    const modal =
        document.getElementById("deleteModal");


    if (modal) {
        modal.classList.remove("active");
    }


    document.body.classList.remove("modal-open");

    deleteDocumentId = null;

};


window.closeDeleteModalOnOverlay = function (event) {

    if (event.target === event.currentTarget) {
        closeDeleteModal();
    }

};


window.submitDelete = function () {

    const form =
        document.getElementById("deleteDocumentForm");


    if (!form) return;


    if (!deleteDocumentId) return;


    form.submit();

};


/* =========================================================
   ESCAPE KEY
   ========================================================= */

document.addEventListener("keydown", function (event) {

    if (event.key !== "Escape") return;


    const uploadModal =
        document.getElementById("uploadModal");

    const deleteModal =
        document.getElementById("deleteModal");


    if (
        uploadModal &&
        uploadModal.classList.contains("active")
    ) {

        closeUploadModal();

        return;
    }


    if (
        deleteModal &&
        deleteModal.classList.contains("active")
    ) {

        closeDeleteModal();

    }

});


/* =========================================================
   FORM SUBMIT PROTECTION
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const form =
        document.getElementById("uploadDocumentForm");

    const submitButton =
        document.getElementById("uploadSubmitBtn");


    if (!form || !submitButton) return;


    form.addEventListener("submit", function () {

        submitButton.disabled = true;

        submitButton.style.opacity = "0.7";

        submitButton.innerHTML =
            '<i data-lucide="loader-circle"></i> Uploading...';

        initLucide();

    });

});