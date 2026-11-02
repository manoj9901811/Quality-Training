(function () {
    "use strict";

    /*
     * =========================================================
     * REQUIREMENTS MANAGEMENT
     * =========================================================
     *
     * Important:
     * Modal elements are moved directly under <body>.
     *
     * This avoids:
     * - sidebar stacking problems
     * - navbar not getting blurred
     * - popup appearing behind content
     * - parent transform/filter issues
     * =========================================================
     */

    let currentRequirementId = null;

    /* ---------------------------------------------------------
       DATA
       --------------------------------------------------------- */

    const requirements =
        Array.isArray(window.requirementData)
            ? window.requirementData
            : [];

    const urls =
        window.requirementUrls || {};

    /* ---------------------------------------------------------
       DOM HELPERS
       --------------------------------------------------------- */

    function getElement(id) {
        return document.getElementById(id);
    }

    function refreshIcons() {
        if (
            window.lucide &&
            typeof window.lucide.createIcons === "function"
        ) {
            window.lucide.createIcons();
        }
    }

    /* ---------------------------------------------------------
       MOVE MODAL TO BODY
       --------------------------------------------------------- */

    function moveModalToBody(modal) {

        if (!modal) {
            return;
        }

        if (modal.parentElement !== document.body) {
            document.body.appendChild(modal);
        }
    }

    /* ---------------------------------------------------------
       OPEN MODAL
       --------------------------------------------------------- */

    function openModal(id) {

        const modal = getElement(id);

        if (!modal) {
            console.error(
                "Requirements modal not found:",
                id
            );
            return;
        }

        moveModalToBody(modal);

        modal.hidden = false;
        modal.classList.add("show");
        modal.setAttribute("aria-hidden", "false");

        document.body.classList.add("modal-open");
        document.body.style.overflow = "hidden";

        refreshIcons();

        /*
         * Focus first usable element.
         */
        window.setTimeout(function () {

            const firstInput =
                modal.querySelector(
                    "input:not([type='hidden']), select, textarea, button"
                );

            if (firstInput) {
                try {
                    firstInput.focus();
                } catch (error) {
                    // Ignore focus errors
                }
            }

        }, 50);
    }

    /* ---------------------------------------------------------
       CLOSE MODAL
       --------------------------------------------------------- */

    function closeModal(id) {

        const modal = getElement(id);

        if (!modal) {
            return;
        }

        modal.classList.remove("show");
        modal.hidden = true;
        modal.setAttribute("aria-hidden", "true");

        /*
         * Check whether another modal is still open.
         */
        const openModals =
            document.querySelectorAll(
                ".modal-overlay.show:not([hidden])"
            );

        if (openModals.length === 0) {

            document.body.classList.remove(
                "modal-open"
            );

            document.body.style.overflow = "";
        }
    }

    /* ---------------------------------------------------------
       CLOSE ALL MODALS
       --------------------------------------------------------- */

    function closeAllModals() {

        document
            .querySelectorAll(".modal-overlay")
            .forEach(function (modal) {

                modal.classList.remove("show");
                modal.hidden = true;
                modal.setAttribute(
                    "aria-hidden",
                    "true"
                );
            });

        document.body.classList.remove(
            "modal-open"
        );

        document.body.style.overflow = "";
    }

    /* ---------------------------------------------------------
       RESET CREATE / EDIT FORM
       --------------------------------------------------------- */

    function resetRequirementForm() {

        const form =
            getElement("requirementForm");

        if (!form) {
            return;
        }

        form.reset();

        const statusSection =
            getElement("editStatusSection");

        if (statusSection) {
            statusSection.hidden = true;
            statusSection.style.display = "none";
        }

        const statusSelect =
            getElement("requirementStatus");

        if (statusSelect) {
            statusSelect.value = "OPEN";
        }

        const submitButton =
            getElement("formSubmitButton");

        if (submitButton) {
            submitButton.textContent =
                "Create Requirement";
        }
    }

    /* ---------------------------------------------------------
       OPEN CREATE MODAL
       --------------------------------------------------------- */

    function openCreateModal() {

        resetRequirementForm();

        currentRequirementId = null;

        const form =
            getElement("requirementForm");

        if (form && urls.create) {
            form.action = urls.create;
        }

        const title =
            document.querySelector(
                "#requirementFormModal .modal-header h2"
            );

        if (title) {
            title.textContent =
                "Create Requirement";
        }

        const submitButton =
            getElement("formSubmitButton");

        if (submitButton) {
            submitButton.textContent =
                "Create Requirement";
        }

        openModal(
            "requirementFormModal"
        );
    }

    /* ---------------------------------------------------------
       OPEN EDIT MODAL
       --------------------------------------------------------- */

    function openEditModal(id) {

        const requirement =
            requirements.find(function (item) {

                return String(item.id) === String(id);

            });

        if (!requirement) {

            console.error(
                "Requirement not found:",
                id
            );

            return;
        }

        currentRequirementId = requirement.id;

        const form =
            getElement("requirementForm");

        if (!form) {
            return;
        }

        /*
         * Build edit URL.
         */
        if (urls.editBase) {

            form.action =
                buildUrl(
                    urls.editBase,
                    requirement.id
                );
        }

        setValue(
            "title",
            requirement.title
        );

        setValue(
            "client_name",
            requirement.client_name
        );

        setValue(
            "skill",
            requirement.skill
        );

        setValue(
            "trainer_count",
            requirement.trainer_count
        );

        setValue(
            "location",
            requirement.location
        );

        setValue(
            "start_date",
            requirement.start_date
        );

        setValue(
            "duration",
            requirement.duration
        );

        setValue(
            "budget",
            requirement.budget
        );

        setValue(
            "notes",
            requirement.notes
        );

        const statusSelect =
            getElement("requirementStatus");

        if (statusSelect) {

            statusSelect.value =
                requirement.status || "OPEN";
        }

        const statusSection =
            getElement("editStatusSection");

        if (statusSection) {

            statusSection.hidden = false;
            statusSection.style.display = "";
        }

        const title =
            document.querySelector(
                "#requirementFormModal .modal-header h2"
            );

        if (title) {
            title.textContent =
                "Edit Requirement";
        }

        const submitButton =
            getElement("formSubmitButton");

        if (submitButton) {
            submitButton.textContent =
                "Update Requirement";
        }

        openModal(
            "requirementFormModal"
        );
    }

    /* ---------------------------------------------------------
       SET INPUT VALUE
       --------------------------------------------------------- */

    function setValue(id, value) {

        const element = getElement(id);

        if (!element) {
            return;
        }

        if (
            value === null ||
            value === undefined
        ) {
            element.value = "";
        } else {
            element.value = value;
        }
    }

    /* ---------------------------------------------------------
       BUILD URL
       --------------------------------------------------------- */

    function buildUrl(baseUrl, id) {

        if (!baseUrl) {
            return "";
        }

        /*
         * Flask URL generated with ID 0 normally looks like:
         *
         * /requirements/0/edit
         * /requirements/0/status
         * /requirements/0/delete
         *
         * Replace only the /0/ segment.
         */

        if (baseUrl.indexOf("/0/") !== -1) {

            return baseUrl.replace(
                "/0/",
                "/" + encodeURIComponent(id) + "/"
            );
        }

        /*
         * Fallback:
         * replace trailing /0
         */
        if (
            baseUrl.endsWith("/0")
        ) {

            return baseUrl.slice(
                0,
                -2
            ) + "/" +
                encodeURIComponent(id);
        }

        /*
         * Final fallback.
         */
        return baseUrl.replace(
            /0(?=\/?$)/,
            String(id)
        );
    }

    /* ---------------------------------------------------------
       OPEN VIEW MODAL
       --------------------------------------------------------- */

    function openViewModal(id) {

        const requirement =
            requirements.find(function (item) {

                return String(item.id) === String(id);

            });

        if (!requirement) {

            console.error(
                "Requirement not found:",
                id
            );

            return;
        }

        currentRequirementId =
            requirement.id;

        setText(
            "viewCode",
            requirement.requirement_code
        );

        setText(
            "viewTitle",
            requirement.title
        );

        setText(
            "viewCreated",
            formatDateTime(
                requirement.created_at
            )
        );

        setText(
            "viewClient",
            requirement.client_name
        );

        setText(
            "viewSkill",
            requirement.skill
        );

        setText(
            "viewTrainerCount",
            requirement.trainer_count
        );

        setText(
            "viewLocation",
            requirement.location || "—"
        );

        setText(
            "viewStartDate",
            formatDate(
                requirement.start_date
            )
        );

        setText(
            "viewDuration",
            requirement.duration || "—"
        );

        setText(
            "viewBudget",
            formatCurrency(
                requirement.budget
            )
        );

        setText(
            "viewNotes",
            requirement.notes || "—"
        );

        setText(
            "viewCreatorName",
            requirement.creator_name ||
                requirement.created_by_name ||
                "—"
        );

        setText(
            "viewCreatorEmail",
            requirement.creator_email ||
                "—"
        );

        setText(
            "viewCreatorRole",
            requirement.creator_role ||
                "—"
        );

        renderViewStatus(
            requirement.status
        );

        const statusSelect =
            getElement("viewStatusSelect");

        if (statusSelect) {

            statusSelect.value =
                requirement.status || "OPEN";
        }

        const statusForm =
            getElement("statusForm");

        if (
            statusForm &&
            urls.statusBase
        ) {

            statusForm.action =
                buildUrl(
                    urls.statusBase,
                    requirement.id
                );
        }

        openModal(
            "requirementViewModal"
        );
    }

    /* ---------------------------------------------------------
       SET TEXT
       --------------------------------------------------------- */

    function setText(id, value) {

        const element =
            getElement(id);

        if (!element) {
            return;
        }

        element.textContent =
            value === null ||
            value === undefined ||
            value === ""
                ? "—"
                : String(value);
    }

    /* ---------------------------------------------------------
       FORMAT DATE
       --------------------------------------------------------- */

    function formatDate(value) {

        if (!value) {
            return "—";
        }

        try {

            const date =
                new Date(value);

            if (Number.isNaN(
                date.getTime()
            )) {
                return value;
            }

            return date.toLocaleDateString(
                "en-IN",
                {
                    day: "2-digit",
                    month: "short",
                    year: "numeric"
                }
            );

        } catch (error) {

            return value;
        }
    }

    /* ---------------------------------------------------------
       FORMAT DATE TIME
       --------------------------------------------------------- */

    function formatDateTime(value) {

        if (!value) {
            return "—";
        }

        try {

            const date =
                new Date(value);

            if (Number.isNaN(
                date.getTime()
            )) {
                return value;
            }

            return date.toLocaleString(
                "en-IN",
                {
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit"
                }
            );

        } catch (error) {

            return value;
        }
    }

    /* ---------------------------------------------------------
       FORMAT CURRENCY
       --------------------------------------------------------- */

    function formatCurrency(value) {

        if (
            value === null ||
            value === undefined ||
            value === ""
        ) {
            return "—";
        }

        const number =
            Number(value);

        if (Number.isNaN(number)) {
            return value;
        }

        return "₹" +
            number.toLocaleString(
                "en-IN",
                {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }
            );
    }

    /* ---------------------------------------------------------
       STATUS DISPLAY
       --------------------------------------------------------- */

    function renderViewStatus(status) {

        const badge =
            getElement("viewStatus");

        if (!badge) {
            return;
        }

        const normalized =
            String(status || "OPEN")
                .toUpperCase();

        badge.textContent =
            normalized.replace(
                /_/g,
                " "
            );

        badge.className =
            "status-badge " +
            statusClass(normalized);

        const description =
            getElement(
                "viewStatusDescription"
            );

        if (!description) {
            return;
        }

        const descriptions = {

            OPEN:
                "Requirement is open and available for trainer assignment.",

            IN_PROGRESS:
                "Requirement is currently being processed.",

            ASSIGNED:
                "Trainer assignment has been completed.",

            COMPLETED:
                "Requirement has been completed.",

            CANCELLED:
                "Requirement has been cancelled."
        };

        description.textContent =
            descriptions[normalized] ||
            "";
    }

    /* ---------------------------------------------------------
       STATUS CLASS
       --------------------------------------------------------- */

    function statusClass(status) {

        switch (status) {

            case "OPEN":
                return "status-open";

            case "IN_PROGRESS":
                return "status-in-progress";

            case "ASSIGNED":
                return "status-assigned";

            case "COMPLETED":
                return "status-completed";

            case "CANCELLED":
                return "status-cancelled";

            default:
                return "status-open";
        }
    }

    /* ---------------------------------------------------------
       SEARCH
       --------------------------------------------------------- */

    function searchRequirements() {

        const searchInput =
            getElement(
                "requirementSearch"
            );

        const statusFilter =
            getElement(
                "statusFilter"
            );

        const table =
            getElement(
                "requirementsTable"
            );

        if (!table) {
            return;
        }

        const search =
            (
                searchInput
                    ? searchInput.value
                    : ""
            )
                .trim()
                .toLowerCase();

        const status =
            statusFilter
                ? statusFilter.value
                : "";

        const rows =
            table.querySelectorAll(
                "tbody tr"
            );

        rows.forEach(function (row) {

            /*
             * Empty state row.
             */
            if (
                row.querySelector(
                    ".empty-state"
                )
            ) {
                return;
            }

            const rowText =
                row.textContent
                    .toLowerCase();

            const rowStatus =
                row.dataset.status ||
                "";

            const matchesSearch =
                !search ||
                rowText.includes(search);

            const matchesStatus =
                !status ||
                rowStatus === status;

            row.style.display =
                matchesSearch &&
                matchesStatus
                    ? ""
                    : "none";
        });
    }

    /* ---------------------------------------------------------
       SETUP SEARCH
       --------------------------------------------------------- */

    function setupSearch() {

        const searchInput =
            getElement(
                "requirementSearch"
            );

        const statusFilter =
            getElement(
                "statusFilter"
            );

        if (searchInput) {

            searchInput.addEventListener(
                "input",
                searchRequirements
            );
        }

        if (statusFilter) {

            statusFilter.addEventListener(
                "change",
                searchRequirements
            );
        }
    }

    /* ---------------------------------------------------------
       DELETE
       --------------------------------------------------------- */

    function prepareDelete() {

        if (!currentRequirementId) {
            return;
        }

        const deleteForm =
            getElement(
                "deleteRequirementForm"
            );

        if (
            deleteForm &&
            urls.deleteBase
        ) {

            deleteForm.action =
                buildUrl(
                    urls.deleteBase,
                    currentRequirementId
                );

            deleteForm.submit();
        }
    }

    /* ---------------------------------------------------------
       SETUP BUTTONS
       --------------------------------------------------------- */

    function setupButtons() {

        /*
         * Create button
         */
        const createButton =
            getElement(
                "openCreateModal"
            );

        if (createButton) {

            createButton.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    openCreateModal();
                }
            );
        }

        /*
         * Empty state create button
         */
        const emptyCreateButton =
            getElement(
                "openCreateModalEmpty"
            );

        if (emptyCreateButton) {

            emptyCreateButton.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    openCreateModal();
                }
            );
        }

        /*
         * View buttons
         */
        document
            .querySelectorAll(
                ".view-requirement"
            )
            .forEach(function (button) {

                button.addEventListener(
                    "click",
                    function (event) {

                        event.preventDefault();

                        const id =
                            button.dataset.id;

                        openViewModal(id);
                    }
                );
            });

        /*
         * Close buttons
         */
        document
            .querySelectorAll(
                "[data-close-modal]"
            )
            .forEach(function (button) {

                button.addEventListener(
                    "click",
                    function (event) {

                        event.preventDefault();

                        const modalId =
                            button.dataset
                                .closeModal;

                        if (modalId) {
                            closeModal(modalId);
                        }
                    }
                );
            });

        /*
         * Edit from view
         */
        const editFromView =
            getElement(
                "editFromView"
            );

        if (editFromView) {

            editFromView.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    if (!currentRequirementId) {
                        return;
                    }

                    closeModal(
                        "requirementViewModal"
                    );

                    openEditModal(
                        currentRequirementId
                    );
                }
            );
        }

        /*
         * Delete
         */
        const deleteButton =
            getElement(
                "deleteRequirement"
            );

        if (deleteButton) {

            deleteButton.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    prepareDelete();
                }
            );
        }
    }

    /* ---------------------------------------------------------
       SETUP MODALS
       --------------------------------------------------------- */

    function setupModals() {

        document
            .querySelectorAll(
                ".modal-overlay"
            )
            .forEach(function (modal) {

                /*
                 * Move modal outside page/content.
                 */
                moveModalToBody(modal);

                /*
                 * Always start closed.
                 */
                modal.hidden = true;

                modal.classList.remove(
                    "show"
                );

                modal.setAttribute(
                    "aria-hidden",
                    "true"
                );

                /*
                 * Clicking backdrop closes modal.
                 */
                modal.addEventListener(
                    "click",
                    function (event) {

                        if (
                            event.target === modal
                        ) {

                            closeModal(
                                modal.id
                            );
                        }
                    }
                );
            });
    }

    /* ---------------------------------------------------------
       ESC KEY
       --------------------------------------------------------- */

    function setupEscapeKey() {

        document.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key !== "Escape"
                ) {
                    return;
                }

                const openModalElement =
                    document.querySelector(
                        ".modal-overlay.show:not([hidden])"
                    );

                if (
                    openModalElement
                ) {

                    closeModal(
                        openModalElement.id
                    );
                }
            }
        );
    }

    /* ---------------------------------------------------------
       FORM SUBMIT PROTECTION
       --------------------------------------------------------- */

    function setupFormSubmit() {

        const form =
            getElement(
                "requirementForm"
            );

        if (!form) {
            return;
        }

        form.addEventListener(
            "submit",
            function () {

                const button =
                    getElement(
                        "formSubmitButton"
                    );

                if (button) {

                    button.disabled = true;

                    /*
                     * Keep text understandable while
                     * request is being processed.
                     */
                    if (
                        button.textContent
                            .toLowerCase()
                            .includes("create")
                    ) {

                        button.textContent =
                            "Creating...";

                    } else {

                        button.textContent =
                            "Updating...";
                    }
                }
            }
        );
    }

    /* ---------------------------------------------------------
       INITIALIZATION
       --------------------------------------------------------- */

    function initialize() {

        setupModals();

        setupButtons();

        setupSearch();

        setupEscapeKey();

        setupFormSubmit();

        refreshIcons();
    }

    /* ---------------------------------------------------------
       PUBLIC API
       --------------------------------------------------------- */

    window.openCreateRequirementModal =
        openCreateModal;

    window.openEditRequirementModal =
        openEditModal;

    window.openViewRequirementModal =
        openViewModal;

    window.closeRequirementModal =
        closeModal;

    window.closeAllRequirementModals =
        closeAllModals;

    /* ---------------------------------------------------------
       DOM READY
       --------------------------------------------------------- */

    if (
        document.readyState === "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initialize
        );

    } else {

        initialize();
    }

})();