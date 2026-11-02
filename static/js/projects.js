/* =========================================================
   QT PLATFORM
   PROJECT MANAGEMENT JAVASCRIPT
========================================================= */

(function () {

    "use strict";


    /* =====================================================
       DATA
    ====================================================== */

    const projects = Array.isArray(window.projectData)
        ? window.projectData
        : [];


    const urls = window.projectUrls || {};


    let activeProjectId = null;



    /* =====================================================
       HELPERS
    ====================================================== */

    function getProject(projectId) {

        return projects.find(function (project) {

            return Number(project.id) === Number(projectId);

        });

    }



    function buildUrl(baseUrl, projectId) {

        if (!baseUrl) {
            return "#";
        }

        return baseUrl.replace(
            /\/0(?=\/|$)/,
            "/" + encodeURIComponent(projectId)
        );

    }



    function setFormAction(
        formId,
        baseUrl,
        projectId
    ) {

        const form =
            document.getElementById(formId);

        if (!form || !baseUrl) {
            return;
        }

        form.action =
            buildUrl(baseUrl, projectId);

    }



    function formatDate(value) {

        if (!value) {
            return "—";
        }

        const date =
            new Date(value + "T00:00:00");

        if (Number.isNaN(date.getTime())) {
            return value;
        }

        return date.toLocaleDateString(
            "en-GB",
            {
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        );

    }



    function formatCurrency(value) {

        const amount =
            Number(value || 0);

        return "₹" +
            amount.toLocaleString(
                "en-IN",
                {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }
            );

    }



    function statusLabel(status) {

        const labels = {

            PLANNING:
                "Planning",

            ACTIVE:
                "Active",

            COMPLETED:
                "Completed",

            CANCELLED:
                "Cancelled"

        };

        return labels[status]
            || status
            || "—";

    }



    function refreshIcons() {

        if (
            window.lucide &&
            typeof lucide.createIcons === "function"
        ) {

            lucide.createIcons();

        }

    }



    /* =====================================================
       MODAL CONTROL
    ====================================================== */

    function openModal(modalId) {

        const modal =
            document.getElementById(modalId);

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


        refreshIcons();

    }



    function closeModal(modalId) {

        const modal =
            document.getElementById(modalId);

        if (!modal) {
            return;
        }


        modal.hidden = true;

        modal.setAttribute(
            "aria-hidden",
            "true"
        );


        const visibleModals =
            document.querySelectorAll(
                ".modal-overlay:not([hidden])"
            );


        if (!visibleModals.length) {

            document.body.classList.remove(
                "modal-open"
            );

        }

    }



    function closeAllModals() {

        document
            .querySelectorAll(".modal-overlay")
            .forEach(function (modal) {

                modal.hidden = true;

                modal.setAttribute(
                    "aria-hidden",
                    "true"
                );

            });


        document.body.classList.remove(
            "modal-open"
        );


        activeProjectId = null;

    }



    /* =====================================================
       CREATE PROJECT
    ====================================================== */

    window.openCreateProjectModal =
        function () {

            const form =
                document.getElementById(
                    "createProjectForm"
                );


            if (form) {
                form.reset();
            }


            const client =
                document.getElementById(
                    "createClient"
                );

            const skill =
                document.getElementById(
                    "createSkill"
                );

            const location =
                document.getElementById(
                    "createLocation"
                );

            const budget =
                document.getElementById(
                    "createBudget"
                );

            const startDate =
                document.getElementById(
                    "createStartDate"
                );

            const endDate =
                document.getElementById(
                    "createEndDate"
                );

            const requirement =
                document.getElementById(
                    "createRequirement"
                );


            if (client) {
                client.value = "";
            }

            if (skill) {
                skill.value = "";
            }

            if (location) {
                location.value = "";
            }

            if (budget) {
                budget.value = "0";
            }

            if (startDate) {
                startDate.value = "";
            }

            if (endDate) {
                endDate.value = "";
            }

            if (requirement) {
                requirement.value = "";
            }


            openModal(
                "createProjectModal"
            );

        };



    window.closeCreateProjectModal =
        function () {

            closeModal(
                "createProjectModal"
            );

        };



    /* =====================================================
       REQUIREMENT AUTO FILL
    ====================================================== */

    function updateCreateRequirementFields() {

        const select =
            document.getElementById(
                "createRequirement"
            );


        if (!select) {
            return;
        }


        const selectedOption =
            select.options[
                select.selectedIndex
            ];


        const client =
            document.getElementById(
                "createClient"
            );

        const skill =
            document.getElementById(
                "createSkill"
            );

        const location =
            document.getElementById(
                "createLocation"
            );

        const budget =
            document.getElementById(
                "createBudget"
            );

        const startDate =
            document.getElementById(
                "createStartDate"
            );


        if (
            !selectedOption ||
            !selectedOption.value
        ) {

            if (client) {
                client.value = "";
            }

            if (skill) {
                skill.value = "";
            }

            if (location) {
                location.value = "";
            }

            if (budget) {
                budget.value = "0";
            }

            if (startDate) {
                startDate.value = "";
            }

            return;

        }


        if (client) {

            client.value =
                selectedOption.dataset.client
                || "";

        }


        if (skill) {

            skill.value =
                selectedOption.dataset.skill
                || "";

        }


        if (location) {

            location.value =
                selectedOption.dataset.location
                || "";

        }


        if (budget) {

            const requirementBudget =
                selectedOption.dataset.budget;

            if (
                requirementBudget !==
                undefined
            ) {

                budget.value =
                    requirementBudget || "0";

            }

        }


        if (startDate) {

            startDate.value =
                selectedOption.dataset.startDate
                || "";

        }

    }



    /* =====================================================
       EDIT PROJECT
    ====================================================== */

    window.openEditProjectModal =
        function (projectId) {

            const project =
                getProject(projectId);


            if (!project) {
                return;
            }


            activeProjectId =
                project.id;


            const form =
                document.getElementById(
                    "editProjectForm"
                );


            if (form) {
                form.reset();
            }


            setFormAction(
                "editProjectForm",
                urls.editBase,
                project.id
            );


            const code =
                document.getElementById(
                    "editProjectCode"
                );

            const name =
                document.getElementById(
                    "editProjectName"
                );

            const requirement =
                document.getElementById(
                    "editProjectRequirement"
                );

            const client =
                document.getElementById(
                    "editClient"
                );

            const skill =
                document.getElementById(
                    "editSkill"
                );

            const location =
                document.getElementById(
                    "editLocation"
                );

            const budget =
                document.getElementById(
                    "editBudget"
                );

            const startDate =
                document.getElementById(
                    "editStartDate"
                );

            const endDate =
                document.getElementById(
                    "editEndDate"
                );

            const status =
                document.getElementById(
                    "editProjectStatus"
                );

            const notes =
                document.getElementById(
                    "editNotes"
                );


            if (code) {

                code.value =
                    project.project_code
                    || "";

            }


            if (name) {

                name.value =
                    project.project_name
                    || "";

            }


            if (requirement) {

                if (project.requirement_code) {

                    requirement.value =
                        project.requirement_code +
                        (
                            project.requirement_title
                                ? " — " +
                                  project.requirement_title
                                : ""
                        );

                } else {

                    requirement.value =
                        "Not linked";

                }

            }


            if (client) {

                client.value =
                    project.client_name
                    || "";

            }


            if (skill) {

                skill.value =
                    project.skill
                    || "";

            }


            if (location) {

                location.value =
                    project.location
                    || "";

            }


            if (budget) {

                budget.value =
                    Number(
                        project.budget || 0
                    );

            }


            if (startDate) {

                startDate.value =
                    project.start_date
                    || "";

            }


            if (endDate) {

                endDate.value =
                    project.end_date
                    || "";

            }


            if (status) {

                status.value =
                    project.status
                    || "PLANNING";

            }


            if (notes) {

                notes.value =
                    project.notes
                    || "";

            }


            openModal(
                "editProjectModal"
            );

        };



    window.closeEditProjectModal =
        function () {

            closeModal(
                "editProjectModal"
            );

        };



    /* =====================================================
       VIEW PROJECT
    ====================================================== */

    window.openViewProjectModal =
        function (projectId) {

            const project =
                getProject(projectId);


            if (!project) {
                return;
            }


            activeProjectId =
                project.id;


            const code =
                document.getElementById(
                    "viewProjectCode"
                );

            const title =
                document.getElementById(
                    "viewProjectTitle"
                );

            const client =
                document.getElementById(
                    "viewProjectClient"
                );

            const requirement =
                document.getElementById(
                    "viewProjectRequirement"
                );

            const skill =
                document.getElementById(
                    "viewProjectSkill"
                );

            const location =
                document.getElementById(
                    "viewProjectLocation"
                );

            const status =
                document.getElementById(
                    "viewProjectStatus"
                );

            const startDate =
                document.getElementById(
                    "viewProjectStartDate"
                );

            const endDate =
                document.getElementById(
                    "viewProjectEndDate"
                );

            const budget =
                document.getElementById(
                    "viewProjectBudget"
                );

            const creator =
                document.getElementById(
                    "viewProjectCreator"
                );

            const notes =
                document.getElementById(
                    "viewProjectNotes"
                );


            if (code) {

                code.textContent =
                    project.project_code
                    || "—";

            }


            if (title) {

                title.textContent =
                    project.project_name
                    || "Project";

            }


            if (client) {

                client.textContent =
                    project.client_name
                    || "—";

            }


            if (requirement) {

                requirement.textContent =
                    project.requirement_code

                        ? project.requirement_code +
                          (
                              project.requirement_title
                                  ? " — " +
                                    project.requirement_title
                                  : ""
                          )

                        : "Not linked";

            }


            if (skill) {

                skill.textContent =
                    project.skill
                    || "—";

            }


            if (location) {

                location.textContent =
                    project.location
                    || "—";

            }


            if (status) {

                status.textContent =
                    statusLabel(
                        project.status
                    );

            }


            if (startDate) {

                startDate.textContent =
                    formatDate(
                        project.start_date
                    );

            }


            if (endDate) {

                endDate.textContent =
                    formatDate(
                        project.end_date
                    );

            }


            if (budget) {

                budget.textContent =
                    formatCurrency(
                        project.budget
                    );

            }


            if (creator) {

                creator.textContent =
                    project.creator_name
                    ||
                    project.creator_email
                    ||
                    "—";

            }


            if (notes) {

                notes.textContent =
                    project.notes
                    ||
                    "No notes added.";

            }


            const editButton =
                document.getElementById(
                    "editFromViewProject"
                );


            if (editButton) {

                editButton.onclick =
                    function () {

                        closeModal(
                            "viewProjectModal"
                        );

                        window.openEditProjectModal(
                            project.id
                        );

                    };

            }


            openModal(
                "viewProjectModal"
            );

        };



    window.closeViewProjectModal =
        function () {

            closeModal(
                "viewProjectModal"
            );

        };



    /* =====================================================
       STATUS MODAL
    ====================================================== */

    window.openProjectStatusModal =
        function (projectId) {

            const project =
                getProject(projectId);


            if (!project) {
                return;
            }


            activeProjectId =
                project.id;


            setFormAction(
                "projectStatusForm",
                urls.statusBase,
                project.id
            );


            const projectName =
                document.getElementById(
                    "projectStatusProjectName"
                );


            const select =
                document.getElementById(
                    "projectStatusSelect"
                );


            if (projectName) {

                projectName.textContent =
                    (
                        project.project_code
                            ? project.project_code +
                              " — "
                            : ""
                    ) +
                    (
                        project.project_name
                        || "Project"
                    );

            }


            if (select) {

                select.value =
                    project.status
                    || "PLANNING";

            }


            openModal(
                "projectStatusModal"
            );

        };



    window.closeProjectStatusModal =
        function () {

            closeModal(
                "projectStatusModal"
            );

        };



    /* =====================================================
       DELETE PROJECT
    ====================================================== */

    window.openDeleteProjectModal =
        function (projectId) {

            const project =
                getProject(projectId);


            if (!project) {
                return;
            }


            activeProjectId =
                project.id;


            setFormAction(
                "deleteProjectForm",
                urls.deleteBase,
                project.id
            );


            const name =
                document.getElementById(
                    "deleteProjectName"
                );


            if (name) {

                name.textContent =
                    (
                        project.project_code
                            ? project.project_code +
                              " — "
                            : ""
                    ) +
                    (
                        project.project_name
                        || "this project"
                    );

            }


            openModal(
                "deleteProjectModal"
            );

        };



    window.closeDeleteProjectModal =
        function () {

            closeModal(
                "deleteProjectModal"
            );

        };



    /* =====================================================
       TRAINER ASSIGNMENT
    ====================================================== */

    function buildAssignTrainerUrl(projectId) {

        if (!urls.assignTrainerBase) {
            return "#";
        }

        return urls.assignTrainerBase.replace(
            /\/0(?=\/|$)/,
            "/" + encodeURIComponent(projectId)
        );

    }



    function buildRemoveTrainerUrl(
        projectId,
        assignmentId
    ) {

        if (!urls.removeTrainerBase) {
            return "#";
        }

        let url =
            urls.removeTrainerBase.replace(
                /\/0(?=\/|$)/,
                "/" + encodeURIComponent(projectId)
            );


        return url.replace(
            /\/0(?=\/|$)/,
            "/" + encodeURIComponent(assignmentId)
        );

    }



    function assignmentStatusLabel(status) {

        const labels = {

            PENDING:
                "Pending",

            ASSIGNED:
                "Assigned",

            ACTIVE:
                "Active",

            COMPLETED:
                "Completed",

            CANCELLED:
                "Cancelled"

        };


        return labels[status]
            || status
            || "Pending";

    }



    function assignmentStatusClass(status) {

        const classes = {

            PENDING:
                "status-pending",

            ASSIGNED:
                "status-assigned",

            ACTIVE:
                "status-active",

            COMPLETED:
                "status-completed",

            CANCELLED:
                "status-cancelled"

        };


        return classes[status]
            || "status-pending";

    }



    function escapeHtml(value) {

        if (
            value === null ||
            value === undefined
        ) {

            return "";

        }


        return String(value)
            .replace(
                /&/g,
                "&amp;"
            )
            .replace(
                /</g,
                "&lt;"
            )
            .replace(
                />/g,
                "&gt;"
            )
            .replace(
                /"/g,
                "&quot;"
            )
            .replace(
                /'/g,
                "&#039;"
            );

    }



    function renderProjectTrainers(project) {

        const container =
            document.getElementById(
                "viewProjectTrainers"
            );


        if (!container) {
            return;
        }


        const assignments =
            Array.isArray(
                project.trainer_assignments
            )
                ? project.trainer_assignments
                : [];


        if (!assignments.length) {

            container.innerHTML = `
                <div class="project-trainer-empty">
                    <span>
                        No trainers assigned to this project.
                    </span>
                </div>
            `;


            refreshIcons();

            return;

        }


        container.innerHTML =
            assignments
                .map(
                    function (assignment) {

                        const name =
                            escapeHtml(
                                assignment.trainer_name
                                || "Trainer"
                            );


                        const location =
                            escapeHtml(
                                assignment.trainer_location
                                || ""
                            );


                        const status =
                            assignmentStatusLabel(
                                assignment.assignment_status
                            );


                        const statusClass =
                            assignmentStatusClass(
                                assignment.assignment_status
                            );


                        const assignedAt =
                            escapeHtml(
                                assignment.assigned_at
                                || ""
                            );


                        return `
                            <div
                                class="project-trainer-item"
                            >

                                <div
                                    class="project-trainer-avatar"
                                >
                                    <i
                                        data-lucide="user"
                                    ></i>
                                </div>


                                <div
                                    class="project-trainer-info"
                                >

                                    <div
                                        class="project-trainer-name"
                                    >
                                        ${name}
                                    </div>


                                    ${
                                        location
                                            ? `
                                                <div
                                                    class="project-trainer-location"
                                                >
                                                    <i
                                                        data-lucide="map-pin"
                                                    ></i>

                                                    ${location}
                                                </div>
                                              `
                                            : ""
                                    }


                                    ${
                                        assignedAt
                                            ? `
                                                <div
                                                    class="project-trainer-date"
                                                >
                                                    Added
                                                    ${assignedAt}
                                                </div>
                                              `
                                            : ""
                                    }

                                </div>


                                <div
                                    class="project-trainer-status"
                                >

                                    <span
                                        class="trainer-status ${statusClass}"
                                    >
                                        ${escapeHtml(status)}
                                    </span>

                                </div>


                                <button
                                    type="button"
                                    class="icon-btn icon-btn-danger remove-trainer-btn"
                                    title="Remove trainer"
                                    data-project-id="${project.id}"
                                    data-assignment-id="${assignment.id}"
                                >

                                    <i
                                        data-lucide="user-minus"
                                    ></i>

                                </button>

                            </div>
                        `;

                    }
                )
                .join("");


        container
            .querySelectorAll(
                ".remove-trainer-btn"
            )
            .forEach(
                function (button) {

                    button.addEventListener(
                        "click",
                        function () {

                            openRemoveTrainerModal(
                                button.dataset.projectId,
                                button.dataset.assignmentId
                            );

                        }
                    );

                }
            );


        refreshIcons();

    }



    /* =====================================================
       OPEN ASSIGN TRAINER MODAL
    ====================================================== */

    window.openAssignTrainerModal =
        function (projectId) {

            const project =
                getProject(projectId);


            if (!project) {

                console.error(
                    "Project details are not found:",
                    projectId
                );

                return;

            }


            activeProjectId =
                project.id;


            const projectCode =
                document.getElementById(
                    "assignTrainerProjectCode"
                );


            const projectName =
                document.getElementById(
                    "assignTrainerProjectName"
                );


            if (projectCode) {

                projectCode.textContent =
                    project.project_code
                    || "—";

            }


            if (projectName) {

                projectName.textContent =
                    project.project_name
                    || "Project";

            }


            const form =
                document.getElementById(
                    "assignTrainerForm"
                );


            if (form) {

                form.action =
                    buildAssignTrainerUrl(
                        project.id
                    );

            }


            renderProjectTrainers(
                project
            );


            const select =
                document.getElementById(
                    "assignTrainerSelect"
                );


            if (select) {

                const assignments =
                    Array.isArray(
                        project.trainer_assignments
                    )
                        ? project.trainer_assignments
                        : [];


                const assignedIds =
                    new Set(
                        assignments.map(
                            function (assignment) {

                                return Number(
                                    assignment.trainer_id
                                );

                            }
                        )
                    );


                Array.from(
                    select.options
                ).forEach(
                    function (option) {

                        if (!option.value) {
                            return;
                        }


                        const originalText =
                            option.dataset.originalText
                            ||
                            option.textContent.replace(
                                " — Already assigned",
                                ""
                            );


                        option.dataset.originalText =
                            originalText;


                        const alreadyAssigned =
                            assignedIds.has(
                                Number(
                                    option.value
                                )
                            );


                        option.disabled =
                            alreadyAssigned;


                        option.textContent =
                            alreadyAssigned
                                ? originalText +
                                  " — Already assigned"
                                : originalText;

                    }
                );


                select.value = "";

            }


            openModal(
                "assignTrainerModal"
            );

        };



    window.closeAssignTrainerModal =
        function () {

            closeModal(
                "assignTrainerModal"
            );

        };



    /* =====================================================
       REMOVE TRAINER MODAL
    ====================================================== */

    function openRemoveTrainerModal(
        projectId,
        assignmentId
    ) {

        const project =
            getProject(projectId);


        if (!project) {
            return;
        }


        const assignments =
            Array.isArray(
                project.trainer_assignments
            )
                ? project.trainer_assignments
                : [];


        const assignment =
            assignments.find(
                function (item) {

                    return Number(item.id) ===
                        Number(assignmentId);

                }
            );


        if (!assignment) {
            return;
        }


        const form =
            document.getElementById(
                "removeTrainerForm"
            );


        if (!form) {
            return;
        }


        form.action =
            buildRemoveTrainerUrl(
                projectId,
                assignmentId
            );


        const trainerName =
            document.getElementById(
                "removeTrainerName"
            );


        if (trainerName) {

            trainerName.textContent =
                assignment.trainer_name
                || "Trainer";

        }


        openModal(
            "removeTrainerModal"
        );

    }



    window.openRemoveTrainerModal =
        openRemoveTrainerModal;



    window.closeRemoveTrainerModal =
        function () {

            closeModal(
                "removeTrainerModal"
            );

        };



    /* =====================================================
       SEARCH + FILTER
    ====================================================== */

    function filterProjects() {

        const searchInput =
            document.getElementById(
                "projectSearch"
            );


        const statusFilter =
            document.getElementById(
                "projectStatusFilter"
            );


        const rows =
            document.querySelectorAll(
                "#projectsTableBody .project-row"
            );


        const searchTerm =
            searchInput
                ? searchInput.value
                    .trim()
                    .toLowerCase()
                : "";


        const selectedStatus =
            statusFilter
                ? statusFilter.value
                : "ALL";


        let visibleCount = 0;


        rows.forEach(
            function (row) {

                const searchableText =
                    (
                        row.dataset.search
                        || ""
                    ).toLowerCase();


                const rowStatus =
                    row.dataset.status
                    || "";


                const matchesSearch =
                    !searchTerm
                    ||
                    searchableText.includes(
                        searchTerm
                    );


                const matchesStatus =
                    selectedStatus === "ALL"
                    ||
                    !selectedStatus
                    ||
                    rowStatus === selectedStatus;


                const visible =
                    matchesSearch &&
                    matchesStatus;


                row.style.display =
                    visible
                        ? ""
                        : "none";


                if (visible) {

                    visibleCount += 1;

                }

            }
        );


        const noResults =
            document.getElementById(
                "noProjectSearchResults"
            );


        const emptyRow =
            document.getElementById(
                "emptyProjectsRow"
            );


        const visibleCountElement =
            document.getElementById(
                "visibleProjectCount"
            );


        if (visibleCountElement) {

            visibleCountElement.textContent =
                visibleCount;

        }


        if (noResults) {

            noResults.hidden =
                rows.length > 0 &&
                visibleCount === 0;

        }


        if (emptyRow) {

            emptyRow.style.display =
                rows.length === 0
                    ? ""
                    : "none";

        }

    }



    /* =====================================================
       DATE VALIDATION
    ====================================================== */

    function validateDateRange(
        startInput,
        endInput
    ) {

        if (
            !startInput ||
            !endInput
        ) {

            return true;

        }


        if (
            startInput.value &&
            endInput.value &&
            endInput.value <
            startInput.value
        ) {

            endInput.setCustomValidity(
                "End date cannot be earlier than the start date."
            );


            return false;

        }


        endInput.setCustomValidity("");


        return true;

    }



    /* =====================================================
       INITIALIZATION
    ====================================================== */

    document.addEventListener(
        "DOMContentLoaded",
        function () {


            /* ---------------------------------------------
               FORCE ALL MODALS CLOSED INITIALLY
            ---------------------------------------------- */

            document
                .querySelectorAll(
                    ".modal-overlay"
                )
                .forEach(
                    function (modal) {

                        modal.hidden = true;

                        modal.setAttribute(
                            "aria-hidden",
                            "true"
                        );

                    }
                );



            /* ---------------------------------------------
               CREATE BUTTON
            ---------------------------------------------- */

            const createButton =
                document.getElementById(
                    "openCreateProjectBtn"
                );


            if (createButton) {

                createButton.addEventListener(
                    "click",
                    function (event) {

                        event.preventDefault();

                        window.openCreateProjectModal();

                    }
                );

            }



            /* ---------------------------------------------
               EMPTY STATE CREATE BUTTON
            ---------------------------------------------- */

            const emptyCreateButton =
                document.getElementById(
                    "emptyCreateProjectBtn"
                );


            if (emptyCreateButton) {

                emptyCreateButton.addEventListener(
                    "click",
                    function (event) {

                        event.preventDefault();

                        window.openCreateProjectModal();

                    }
                );

            }



            /* ---------------------------------------------
               SEARCH
            ---------------------------------------------- */

            const searchInput =
                document.getElementById(
                    "projectSearch"
                );


            if (searchInput) {

                searchInput.addEventListener(
                    "input",
                    filterProjects
                );

            }



            /* ---------------------------------------------
               STATUS FILTER
            ---------------------------------------------- */

            const statusFilter =
                document.getElementById(
                    "projectStatusFilter"
                );


            if (statusFilter) {

                statusFilter.addEventListener(
                    "change",
                    filterProjects
                );

            }



            /* ---------------------------------------------
               REQUIREMENT
            ---------------------------------------------- */

            const requirementSelect =
                document.getElementById(
                    "createRequirement"
                );


            if (requirementSelect) {

                requirementSelect.addEventListener(
                    "change",
                    updateCreateRequirementFields
                );

            }



            /* ---------------------------------------------
               DATE INPUTS
            ---------------------------------------------- */

            const createStart =
                document.getElementById(
                    "createStartDate"
                );


            const createEnd =
                document.getElementById(
                    "createEndDate"
                );


            const editStart =
                document.getElementById(
                    "editStartDate"
                );


            const editEnd =
                document.getElementById(
                    "editEndDate"
                );


            if (
                createStart &&
                createEnd
            ) {

                createStart.addEventListener(
                    "change",
                    function () {

                        validateDateRange(
                            createStart,
                            createEnd
                        );

                    }
                );


                createEnd.addEventListener(
                    "change",
                    function () {

                        validateDateRange(
                            createStart,
                            createEnd
                        );

                    }
                );

            }


            if (
                editStart &&
                editEnd
            ) {

                editStart.addEventListener(
                    "change",
                    function () {

                        validateDateRange(
                            editStart,
                            editEnd
                        );

                    }
                );


                editEnd.addEventListener(
                    "change",
                    function () {

                        validateDateRange(
                            editStart,
                            editEnd
                        );

                    }
                );

            }



            /* ---------------------------------------------
               TABLE ACTION BUTTONS
            ---------------------------------------------- */

            document
                .querySelectorAll(
                    ".view-project-btn"
                )
                .forEach(
                    function (button) {

                        button.addEventListener(
                            "click",
                            function () {

                                window.openViewProjectModal(
                                    button.dataset.projectId
                                );

                            }
                        );

                    }
                );



            document
                .querySelectorAll(
                    ".edit-project-btn"
                )
                .forEach(
                    function (button) {

                        button.addEventListener(
                            "click",
                            function () {

                                window.openEditProjectModal(
                                    button.dataset.projectId
                                );

                            }
                        );

                    }
                );



            document
                .querySelectorAll(
                    ".status-project-btn"
                )
                .forEach(
                    function (button) {

                        button.addEventListener(
                            "click",
                            function () {

                                window.openProjectStatusModal(
                                    button.dataset.projectId
                                );

                            }
                        );

                    }
                );



            document
                .querySelectorAll(
                    ".delete-project-btn"
                )
                .forEach(
                    function (button) {

                        button.addEventListener(
                            "click",
                            function () {

                                window.openDeleteProjectModal(
                                    button.dataset.projectId
                                );

                            }
                        );

                    }
                );



            /* ---------------------------------------------
               TRAINER ASSIGNMENT BUTTONS
            ---------------------------------------------- */

            document
                .querySelectorAll(
                    ".trainer-project-btn"
                )
                .forEach(
                    function (button) {

                        button.addEventListener(
                            "click",
                            function (event) {

                                event.preventDefault();

                                window.openAssignTrainerModal(
                                    button.dataset.projectId
                                );

                            }
                        );

                    }
                );



            /* ---------------------------------------------
               CLOSE BUTTONS
            ---------------------------------------------- */

            document
                .querySelectorAll(
                    "[data-close-modal]"
                )
                .forEach(
                    function (button) {

                        button.addEventListener(
                            "click",
                            function () {

                                closeModal(
                                    button.dataset.closeModal
                                );

                            }
                        );

                    }
                );



            /* ---------------------------------------------
               CLICK OUTSIDE MODAL
            ---------------------------------------------- */

            document
                .querySelectorAll(
                    ".modal-overlay"
                )
                .forEach(
                    function (overlay) {

                        overlay.addEventListener(
                            "click",
                            function (event) {

                                if (
                                    event.target ===
                                    overlay
                                ) {

                                    closeModal(
                                        overlay.id
                                    );

                                }

                            }
                        );

                    }
                );



            /* ---------------------------------------------
               ESCAPE
            ---------------------------------------------- */

            document.addEventListener(
                "keydown",
                function (event) {

                    if (
                        event.key === "Escape"
                    ) {

                        closeAllModals();

                    }

                }
            );



            /* ---------------------------------------------
               FORM VALIDATION
            ---------------------------------------------- */

            const forms =
                document.querySelectorAll(
                    "#createProjectForm, #editProjectForm"
                );


            forms.forEach(
                function (form) {

                    form.addEventListener(
                        "submit",
                        function (event) {


                            if (
                                form.id ===
                                "createProjectForm"
                            ) {

                                if (
                                    !validateDateRange(
                                        createStart,
                                        createEnd
                                    )
                                ) {

                                    event.preventDefault();

                                    if (createEnd) {

                                        createEnd.reportValidity();

                                    }

                                    return;

                                }

                            }


                            if (
                                form.id ===
                                "editProjectForm"
                            ) {

                                if (
                                    !validateDateRange(
                                        editStart,
                                        editEnd
                                    )
                                ) {

                                    event.preventDefault();

                                    if (editEnd) {

                                        editEnd.reportValidity();

                                    }

                                }

                            }

                        }
                    );

                }
            );



            /* ---------------------------------------------
               INITIAL UI
            ---------------------------------------------- */

            refreshIcons();

            filterProjects();

        }
    );

})();