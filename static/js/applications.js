"use strict";


/* =========================================================
   ICONS
========================================================= */

function refreshIcons() {

    if (typeof lucide !== "undefined") {

        lucide.createIcons();

    }

}


/* =========================================================
   CREATE APPLICATION MODAL
========================================================= */

function openCreateApplicationModal() {

    const modal =
        document.getElementById(
            "createApplicationModal"
        );

    if (!modal) {
        return;
    }


    modal.hidden = false;

    modal.setAttribute(
        "aria-hidden",
        "false"
    );


    document.body.classList.add(
        "modal-open"
    );


    document.body.style.overflow =
        "hidden";


    refreshIcons();

}


function closeCreateApplicationModal() {

    const modal =
        document.getElementById(
            "createApplicationModal"
        );

    if (!modal) {
        return;
    }


    modal.hidden = true;

    modal.setAttribute(
        "aria-hidden",
        "true"
    );


    document.body.classList.remove(
        "modal-open"
    );


    document.body.style.overflow = "";

}


/* =========================================================
   APPLICATION DETAILS
========================================================= */

function viewApplication(applicationId) {

    const dataElement =
        document.getElementById(
            "application-data-" + applicationId
        );


    if (!dataElement) {

        console.error(
            "Application data not found:",
            applicationId
        );

        return;

    }


    let application;


    try {

        application =
            JSON.parse(
                dataElement.textContent
            );

    } catch (error) {

        console.error(
            "Unable to read application data:",
            error
        );

        return;

    }


    setText(
        "detailApplicationCode",
        application.code
    );


    setText(
        "detailApplicationStatus",
        formatStatus(application.status)
    );


    setText(
        "detailMatchScore",
        application.match_score !== null &&
        application.match_score !== undefined
            ? Number(application.match_score).toFixed(0) + "%"
            : "—"
    );


    setText(
        "detailApplicationSource",
        formatStatus(application.source)
    );


    setText(
        "detailCreated",
        application.created_at || "—"
    );


    /* =============================================
       REQUIREMENT
    ============================================== */

    const requirement =
        application.requirement || {};


    setText(
        "detailRequirementCode",
        requirement.code || "—"
    );


    setText(
        "detailRequirementTitle",
        requirement.title || "—"
    );


    setText(
        "detailClient",
        requirement.client || "—"
    );


    setText(
        "detailSkill",
        requirement.skill || "—"
    );


    setText(
        "detailTrainerCount",
        requirement.trainer_count !== undefined
            ? requirement.trainer_count
            : "—"
    );


    setText(
        "detailRequirementLocation",
        requirement.location || "—"
    );


    setText(
        "detailStartDate",
        requirement.start_date || "—"
    );


    setText(
        "detailDuration",
        requirement.duration || "—"
    );


    /* =============================================
       TRAINER
    ============================================== */

    const trainer =
        application.trainer || {};


    setText(
        "detailTrainer",
        trainer.name || "—"
    );


    setText(
        "detailTrainerLocation",
        trainer.location || "—"
    );


    setText(
        "detailTrainerPhone",
        trainer.phone || "—"
    );


    setText(
        "detailExperience",
        trainer.experience !== undefined &&
        trainer.experience !== null
            ? trainer.experience + " years"
            : "—"
    );


    setText(
        "detailTrainerSkills",
        trainer.skills || "—"
    );


    /* =============================================
       MESSAGE
    ============================================== */

    setText(
        "detailMessage",
        application.message || "No message provided."
    );


    setText(
        "detailResponse",
        application.response_note || "No response yet."
    );


    /* =============================================
       OPEN MODAL
    ============================================== */

    const modal =
        document.getElementById(
            "applicationDetailsModal"
        );


    if (!modal) {
        return;
    }


    modal.hidden = false;

    modal.setAttribute(
        "aria-hidden",
        "false"
    );


    document.body.classList.add(
        "modal-open"
    );


    document.body.style.overflow =
        "hidden";


    refreshIcons();

}


/* =========================================================
   CLOSE DETAILS MODAL
========================================================= */

function closeApplicationDetailsModal() {

    const modal =
        document.getElementById(
            "applicationDetailsModal"
        );


    if (!modal) {
        return;
    }


    modal.hidden = true;

    modal.setAttribute(
        "aria-hidden",
        "true"
    );


    document.body.classList.remove(
        "modal-open"
    );


    document.body.style.overflow = "";

}


/* =========================================================
   SET TEXT SAFELY
========================================================= */

function setText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) {
        return;
    }


    element.textContent =
        value !== null &&
        value !== undefined &&
        String(value).trim() !== ""
            ? value
            : "—";

}


/* =========================================================
   FORMAT STATUS / SOURCE
========================================================= */

function formatStatus(value) {

    if (!value) {
        return "—";
    }


    return String(value)
        .replace(/_/g, " ")
        .toLowerCase()
        .replace(
            /\b\w/g,
            function (character) {

                return character.toUpperCase();

            }
        );

}


/* =========================================================
   SEARCH + FILTER
========================================================= */

function applyApplicationFilters() {

    const searchInput =
        document.getElementById(
            "applicationSearch"
        );


    const statusFilter =
        document.getElementById(
            "statusFilter"
        );


    const searchTerm =
        searchInput
            ? searchInput.value
                .toLowerCase()
                .trim()
            : "";


    const selectedStatus =
        statusFilter
            ? statusFilter.value
                .toUpperCase()
            : "";


    const rows =
        document.querySelectorAll(
            "#applicationsTable tbody tr.application-row"
        );


    rows.forEach(function (row) {

        const rowText =
            row.textContent
                .toLowerCase();


        const rowStatus =
            (
                row.dataset.status ||
                ""
            ).toUpperCase();


        const matchesSearch =
            !searchTerm ||
            rowText.includes(
                searchTerm
            );


        const matchesStatus =
            !selectedStatus ||
            rowStatus === selectedStatus;


        row.style.display =
            matchesSearch &&
            matchesStatus
                ? ""
                : "none";

    });

}


/* =========================================================
   ESCAPE KEY
========================================================= */

function setupEscapeKey() {

    document.addEventListener(
        "keydown",
        function (event) {

            if (event.key !== "Escape") {
                return;
            }


            closeCreateApplicationModal();

            closeApplicationDetailsModal();

        }
    );

}


/* =========================================================
   MODAL BACKDROP CLICK
========================================================= */

function setupModalBackdrop() {

    const createModal =
        document.getElementById(
            "createApplicationModal"
        );


    const detailsModal =
        document.getElementById(
            "applicationDetailsModal"
        );


    if (createModal) {

        createModal.addEventListener(
            "click",
            function (event) {

                if (
                    event.target === createModal
                ) {

                    closeCreateApplicationModal();

                }

            }
        );

    }


    if (detailsModal) {

        detailsModal.addEventListener(
            "click",
            function (event) {

                if (
                    event.target === detailsModal
                ) {

                    closeApplicationDetailsModal();

                }

            }
        );

    }

}


/* =========================================================
   INITIALIZATION
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        refreshIcons();


        const searchInput =
            document.getElementById(
                "applicationSearch"
            );


        const statusFilter =
            document.getElementById(
                "statusFilter"
            );


        if (searchInput) {

            searchInput.addEventListener(
                "input",
                applyApplicationFilters
            );

        }


        if (statusFilter) {

            statusFilter.addEventListener(
                "change",
                applyApplicationFilters
            );

        }


        setupEscapeKey();

        setupModalBackdrop();

    }
);