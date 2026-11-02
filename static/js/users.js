/* =========================================================
   QT PLATFORM - USER MANAGEMENT JS
   Complete Modal + Search + Filter
========================================================= */

"use strict";


/* =========================================================
   HELPERS
========================================================= */

function refreshIcons() {

    if (
        typeof lucide !== "undefined"
    ) {
        lucide.createIcons();
    }

}


/* =========================================================
   MOVE MODAL TO BODY
========================================================= */

function moveUserModalToBody() {

    const modal =
        document.getElementById(
            "createUserModal"
        );

    if (!modal) {
        return null;
    }


    /*
     * This is the critical fix.
     *
     * The modal must not remain inside
     * .users-page because .users-page
     * creates its own stacking context.
     */

    if (
        modal.parentElement !==
        document.body
    ) {

        document.body.appendChild(
            modal
        );

    }


    return modal;

}


/* =========================================================
   OPEN CREATE USER MODAL
========================================================= */

function openCreateUserModal() {

    const modal =
        moveUserModalToBody();

    if (!modal) {
        return;
    }


    resetCreateUserForm();


    /*
     * Remove hidden state.
     */

    modal.hidden = false;


    /*
     * Accessibility.
     */

    modal.setAttribute(
        "aria-hidden",
        "false"
    );


    /*
     * Body scroll lock.
     */

    document.body.classList.add(
        "modal-open"
    );


    document.body.style.overflow =
        "hidden";


    /*
     * Refresh icons after modal
     * becomes visible.
     */

    refreshIcons();


    /*
     * Focus first field.
     */

    setTimeout(function () {

        const role =
            document.getElementById(
                "role"
            );

        if (role) {
            role.focus();
        }

    }, 100);

}


/* =========================================================
   CLOSE CREATE USER MODAL
========================================================= */

function closeCreateUserModal() {

    const modal =
        document.getElementById(
            "createUserModal"
        );

    if (!modal) {
        return;
    }


    /*
     * Hide modal.
     */

    modal.hidden = true;


    /*
     * Accessibility.
     */

    modal.setAttribute(
        "aria-hidden",
        "true"
    );


    /*
     * Restore body scrolling.
     */

    document.body.classList.remove(
        "modal-open"
    );


    document.body.style.overflow =
        "";

}


/* =========================================================
   RESET CREATE USER FORM
========================================================= */

function resetCreateUserForm() {

    const form =
        document.getElementById(
            "createUserForm"
        );

    if (form) {
        form.reset();
    }


    const trainerField =
        document.getElementById(
            "trainerSelectionField"
        );


    const trainerSelect =
        document.getElementById(
            "trainer_id"
        );


    const fullName =
        document.getElementById(
            "full_name"
        );


    const trainerNameHelp =
        document.getElementById(
            "trainerNameHelp"
        );


    if (trainerField) {

        trainerField.style.display =
            "none";

    }


    if (trainerSelect) {

        trainerSelect.required =
            false;

        trainerSelect.value =
            "";

    }


    if (fullName) {

        fullName.readOnly =
            false;

        fullName.placeholder =
            "Enter full name";

        fullName.value =
            "";

    }


    if (trainerNameHelp) {

        trainerNameHelp.style.display =
            "none";

    }

}


/* =========================================================
   ROLE CHANGE
========================================================= */

function updateTrainerSelection() {

    const role =
        document.getElementById(
            "role"
        );


    const trainerField =
        document.getElementById(
            "trainerSelectionField"
        );


    const trainerSelect =
        document.getElementById(
            "trainer_id"
        );


    const fullName =
        document.getElementById(
            "full_name"
        );


    const trainerHint =
        document.getElementById(
            "trainerNameHelp"
        );


    if (
        !role ||
        !trainerField ||
        !trainerSelect ||
        !fullName
    ) {
        return;
    }


    /*
     * TRAINER
     */

    if (
        role.value === "TRAINER"
    ) {

        trainerField.style.display =
            "flex";

        trainerSelect.required =
            true;

        fullName.readOnly =
            true;

        fullName.placeholder =
            "Select a trainer profile";


        if (trainerHint) {

            trainerHint.style.display =
                "block";

        }

    }


    /*
     * OTHER ROLES
     */

    else {

        trainerField.style.display =
            "none";

        trainerSelect.required =
            false;

        trainerSelect.value =
            "";

        fullName.readOnly =
            false;

        fullName.placeholder =
            "Enter full name";

        fullName.value =
            "";


        if (trainerHint) {

            trainerHint.style.display =
                "none";

        }

    }

}


/* =========================================================
   TRAINER SELECTION
========================================================= */

function updateTrainerName() {

    const trainerSelect =
        document.getElementById(
            "trainer_id"
        );


    const fullName =
        document.getElementById(
            "full_name"
        );


    if (
        !trainerSelect ||
        !fullName
    ) {
        return;
    }


    const selectedOption =
        trainerSelect.options[
            trainerSelect.selectedIndex
        ];


    if (
        selectedOption &&
        selectedOption.value
    ) {

        fullName.value =
            selectedOption.dataset.name ||
            "";

    }

    else {

        fullName.value =
            "";

    }

}


/* =========================================================
   BACKWARD COMPATIBILITY
========================================================= */

function handleUserRoleChange() {

    updateTrainerSelection();

}


function handleTrainerSelection() {

    updateTrainerName();

}


/* =========================================================
   SEARCH USERS
========================================================= */

function searchUsers() {

    const input =
        document.getElementById(
            "userSearch"
        );


    const table =
        document.getElementById(
            "usersTable"
        );


    if (
        !input ||
        !table
    ) {
        return;
    }


    const search =
        input.value
            .toLowerCase()
            .trim();


    const selectedRole =
        document.getElementById(
            "roleFilter"
        );


    const role =
        selectedRole
            ? selectedRole.value
            : "";


    const rows =
        table.querySelectorAll(
            "tbody tr.user-row"
        );


    let visibleCount =
        0;


    rows.forEach(
        function (row) {

            const text =
                row.textContent
                    .toLowerCase();


            const rowRole =
                row.dataset.role ||
                "";


            const matchesSearch =
                !search ||
                text.includes(search);


            const matchesRole =
                !role ||
                rowRole === role;


            if (
                matchesSearch &&
                matchesRole
            ) {

                row.style.display =
                    "";

                visibleCount++;

            }

            else {

                row.style.display =
                    "none";

            }

        }
    );


    updateSearchResultMessage(
        visibleCount,
        rows.length
    );

}


/* =========================================================
   SEARCH RESULT MESSAGE
========================================================= */

function updateSearchResultMessage(
    visibleCount,
    totalCount
) {

    const message =
        document.getElementById(
            "searchResultMessage"
        );


    if (!message) {
        return;
    }


    if (
        visibleCount ===
        totalCount
    ) {

        message.textContent =
            "Showing all " +
            totalCount +
            " users";

    }

    else {

        message.textContent =
            "Showing " +
            visibleCount +
            " of " +
            totalCount +
            " users";

    }

}


/* =========================================================
   PREPARE USER ROWS
========================================================= */

function prepareUserRows() {

    const table =
        document.getElementById(
            "usersTable"
        );


    if (!table) {
        return;
    }


    const rows =
        table.querySelectorAll(
            "tbody tr"
        );


    rows.forEach(
        function (row) {

            /*
             * Skip empty state.
             */

            if (
                row.querySelector(
                    ".empty-table"
                )
            ) {
                return;
            }


            row.classList.add(
                "user-row"
            );


            const roleElement =
                row.querySelector(
                    ".role-badge"
                );


            const statusElement =
                row.querySelector(
                    ".status-badge"
                );


            if (roleElement) {

                const roleText =
                    roleElement.textContent
                        .trim()
                        .replace(
                            /\s+/g,
                            "_"
                        )
                        .toUpperCase();


                row.dataset.role =
                    roleText;

            }


            if (statusElement) {

                if (
                    statusElement.classList.contains(
                        "active"
                    )
                ) {

                    row.dataset.status =
                        "active";

                }

                else {

                    row.dataset.status =
                        "inactive";

                }

            }

        }
    );

}


/* =========================================================
   ESCAPE KEY
========================================================= */

function setupEscapeKey() {

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key !==
                "Escape"
            ) {
                return;
            }


            const modal =
                document.getElementById(
                    "createUserModal"
                );


            if (
                modal &&
                !modal.hidden
            ) {

                closeCreateUserModal();

            }

        }
    );

}


/* =========================================================
   MODAL BACKDROP
========================================================= */

function setupModalBackdrop() {

    const modal =
        document.getElementById(
            "createUserModal"
        );


    if (!modal) {
        return;
    }


    modal.addEventListener(
        "click",
        function (event) {

            /*
             * Only close when the actual
             * dark backdrop is clicked.
             */

            if (
                event.target ===
                modal
            ) {

                closeCreateUserModal();

            }

        }
    );

}


/* =========================================================
   ROLE EVENTS
========================================================= */

function setupRoleEvents() {

    const role =
        document.getElementById(
            "role"
        );


    const trainerSelect =
        document.getElementById(
            "trainer_id"
        );


    if (role) {

        role.addEventListener(
            "change",
            updateTrainerSelection
        );

    }


    if (trainerSelect) {

        trainerSelect.addEventListener(
            "change",
            updateTrainerName
        );

    }

}


/* =========================================================
   SEARCH EVENTS
========================================================= */

function setupSearchEvents() {

    const searchInput =
        document.getElementById(
            "userSearch"
        );


    const roleFilter =
        document.getElementById(
            "roleFilter"
        );


    if (searchInput) {

        searchInput.addEventListener(
            "input",
            searchUsers
        );

    }


    if (roleFilter) {

        roleFilter.addEventListener(
            "change",
            searchUsers
        );

    }

}


/* =========================================================
   FORM SUBMIT
========================================================= */

function setupFormSubmit() {

    const form =
        document.getElementById(
            "createUserForm"
        );


    if (!form) {
        return;
    }


    form.addEventListener(
        "submit",
        function () {

            const submitButton =
                form.querySelector(
                    'button[type="submit"]'
                );


            if (!submitButton) {
                return;
            }


            submitButton.disabled =
                true;


            submitButton.style.opacity =
                "0.7";


            submitButton.style.cursor =
                "wait";

        }
    );

}


/* =========================================================
   INITIALIZE MODAL
========================================================= */

function initializeUserModal() {

    const modal =
        moveUserModalToBody();


    if (!modal) {
        return;
    }


    /*
     * Always start hidden.
     */

    modal.hidden =
        true;


    modal.setAttribute(
        "aria-hidden",
        "true"
    );


    /*
     * Remove accidental show class
     * from previous versions.
     */

    modal.classList.remove(
        "show"
    );


    /*
     * Make sure body is unlocked.
     */

    document.body.classList.remove(
        "modal-open"
    );


    document.body.style.overflow =
        "";


    setupModalBackdrop();

}


/* =========================================================
   DOM READY
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        /*
         * CRITICAL:
         * Move modal directly into BODY.
         */

        initializeUserModal();


        /*
         * Form behaviour.
         */

        setupRoleEvents();


        /*
         * Search/filter.
         */

        setupSearchEvents();


        /*
         * Table.
         */

        prepareUserRows();


        /*
         * Escape key.
         */

        setupEscapeKey();


        /*
         * Form submit.
         */

        setupFormSubmit();


        /*
         * Icons.
         */

        refreshIcons();

    }
);