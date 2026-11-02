/* ============================================================
   QT PLATFORM
   TRAINING SCHEDULE JAVASCRIPT
============================================================ */

(function () {

    "use strict";


    /* ========================================================
       BASIC HELPERS
    ======================================================== */

    function byId(id) {

        return document.getElementById(id);

    }


    function refreshIcons() {

        if (
            typeof lucide !== "undefined" &&
            typeof lucide.createIcons === "function"
        ) {

            lucide.createIcons();

        }

    }


    function setValue(id, value) {

        const element = byId(id);

        if (!element) {
            return;
        }

        element.value =
            value === undefined ||
            value === null
                ? ""
                : value;

    }


    function setText(id, value) {

        const element = byId(id);

        if (element) {

            element.textContent =
                String(value);

        }

    }


    function getSchedule(id) {

        const schedules =
            Array.isArray(window.scheduleData)
                ? window.scheduleData
                : [];


        return schedules.find(
            schedule =>
                Number(schedule.id) ===
                Number(id)
        );

    }


    /* ========================================================
       FORM ERRORS
    ======================================================== */

    function clearErrors() {

        document
            .querySelectorAll(
                ".form-field.has-error"
            )
            .forEach(function (field) {

                field.classList.remove(
                    "has-error"
                );

            });


        document
            .querySelectorAll(
                ".field-error"
            )
            .forEach(function (error) {

                error.textContent = "";

            });

    }


    function showError(
        fieldId,
        errorId,
        message
    ) {

        const field =
            byId(fieldId);


        if (field) {

            const wrapper =
                field.closest(
                    ".form-field"
                );


            if (wrapper) {

                wrapper.classList.add(
                    "has-error"
                );

            }

        }


        if (errorId) {

            const error =
                byId(errorId);


            if (error) {

                error.textContent =
                    message;

            }

        }

    }


    /* ========================================================
       TRAINER LOADING
    ======================================================== */

    function updateTrainers(
        selectedTrainerId
    ) {

        const projectSelect =
            byId("project_id");


        const trainerSelect =
            byId("trainer_id");


        if (
            !projectSelect ||
            !trainerSelect
        ) {

            return;

        }


        const projectId =
            String(
                projectSelect.value || ""
            ).trim();


        /* ---------------------------------------------
           Clear current options
        --------------------------------------------- */

        trainerSelect.innerHTML = "";


        const defaultOption =
            document.createElement(
                "option"
            );


        defaultOption.value = "";


        defaultOption.textContent =
            projectId
                ? "Select trainer"
                : "Select project first";


        trainerSelect.appendChild(
            defaultOption
        );


        if (!projectId) {

            trainerSelect.disabled = true;

            return;

        }


        trainerSelect.disabled = false;


        /* ---------------------------------------------
           Read trainer map
        --------------------------------------------- */

        const trainerMap =
            window.scheduleTrainerMap || {};


        console.log(
            "[Schedule] Trainer map:",
            trainerMap
        );


        console.log(
            "[Schedule] Project:",
            projectId
        );


        let trainers = [];


        /*
         * Normal Flask/Jinja structure:
         *
         * {
         *     "1": [
         *         {
         *             "id": 4,
         *             "name": "John"
         *         }
         *     ]
         * }
         */

        if (
            Object.prototype.hasOwnProperty.call(
                trainerMap,
                projectId
            )
        ) {

            trainers =
                trainerMap[projectId];

        }


        /*
         * Numeric key fallback
         */

        else if (
            Object.prototype.hasOwnProperty.call(
                trainerMap,
                Number(projectId)
            )
        ) {

            trainers =
                trainerMap[
                    Number(projectId)
                ];

        }


        /*
         * Some backends may return:
         *
         * [
         *   {
         *      project_id: 1,
         *      id: 4,
         *      name: "John"
         *   }
         * ]
         */

        else if (
            Array.isArray(trainerMap)
        ) {

            trainers =
                trainerMap.filter(
                    function (trainer) {

                        if (!trainer) {
                            return false;
                        }


                        const trainerProjectId =
                            trainer.project_id ??
                            trainer.projectId;


                        return String(
                            trainerProjectId
                        ) === projectId;

                    }
                );

        }


        if (!Array.isArray(trainers)) {

            trainers = [];

        }


        console.log(
            "[Schedule] Trainers:",
            trainers
        );


        /* ---------------------------------------------
           No trainer
        --------------------------------------------- */

        if (trainers.length === 0) {

            const noTrainer =
                document.createElement(
                    "option"
                );


            noTrainer.value = "";


            noTrainer.textContent =
                "No trainers available";


            noTrainer.disabled = true;


            trainerSelect.appendChild(
                noTrainer
            );


            return;

        }


        /* ---------------------------------------------
           Add trainers
        --------------------------------------------- */

        trainers.forEach(
            function (trainer) {

                if (!trainer) {
                    return;
                }


                const trainerId =
                    trainer.id ??
                    trainer.trainer_id ??
                    trainer.user_id;


                const trainerName =
                    trainer.name ??
                    trainer.full_name ??
                    trainer.trainer_name ??
                    "Unnamed Trainer";


                if (
                    trainerId === undefined ||
                    trainerId === null
                ) {

                    return;

                }


                const option =
                    document.createElement(
                        "option"
                    );


                option.value =
                    trainerId;


                option.textContent =
                    trainerName;


                /*
                 * Add location if available
                 */

                if (
                    trainer.location
                ) {

                    option.textContent +=
                        " — " +
                        trainer.location;

                }


                if (
                    selectedTrainerId !==
                        undefined &&
                    selectedTrainerId !==
                        null &&
                    String(trainerId) ===
                        String(selectedTrainerId)
                ) {

                    option.selected = true;

                }


                trainerSelect.appendChild(
                    option
                );

            }
        );


        /*
         * If selected trainer wasn't found,
         * keep normal default.
         */

        if (
            selectedTrainerId !==
                undefined &&
            selectedTrainerId !==
                null
        ) {

            trainerSelect.value =
                String(
                    selectedTrainerId
                );

        }

    }


    /* ========================================================
       MODE FIELDS
    ======================================================== */

    function updateModeFields() {

        const mode =
            byId("mode");


        const locationField =
            byId("locationField");


        const meetingLinkField =
            byId("meetingLinkField");


        const location =
            byId("location");


        const meetingLink =
            byId("meeting_link");


        const locationRequired =
            byId("locationRequired");


        const meetingRequired =
            byId("meetingRequired");


        if (!mode) {
            return;
        }


        const selectedMode =
            String(
                mode.value || ""
            ).toUpperCase();


        /* ---------------------------------------------
           OFFLINE
        --------------------------------------------- */

        if (
            selectedMode ===
            "OFFLINE"
        ) {

            if (locationField) {

                locationField.style.display =
                    "flex";

            }


            if (meetingLinkField) {

                meetingLinkField.style.display =
                    "none";

            }


            if (location) {

                location.required =
                    true;

            }


            if (meetingLink) {

                meetingLink.required =
                    false;

            }


            if (locationRequired) {

                locationRequired.textContent =
                    "*";

            }


            if (meetingRequired) {

                meetingRequired.textContent =
                    "";

            }

        }


        /* ---------------------------------------------
           ONLINE
        --------------------------------------------- */

        else if (
            selectedMode ===
            "ONLINE"
        ) {

            if (locationField) {

                locationField.style.display =
                    "none";

            }


            if (meetingLinkField) {

                meetingLinkField.style.display =
                    "flex";

            }


            if (location) {

                location.required =
                    false;

            }


            if (meetingLink) {

                meetingLink.required =
                    true;

            }


            if (locationRequired) {

                locationRequired.textContent =
                    "";

            }


            if (meetingRequired) {

                meetingRequired.textContent =
                    "*";

            }

        }


        /* ---------------------------------------------
           HYBRID
        --------------------------------------------- */

        else {

            if (locationField) {

                locationField.style.display =
                    "flex";

            }


            if (meetingLinkField) {

                meetingLinkField.style.display =
                    "flex";

            }


            if (location) {

                location.required =
                    true;

            }


            if (meetingLink) {

                meetingLink.required =
                    true;

            }


            if (locationRequired) {

                locationRequired.textContent =
                    "*";

            }


            if (meetingRequired) {

                meetingRequired.textContent =
                    "*";

            }

        }

    }


    /* ========================================================
       MEETING LINK
       NEW FEATURE
    ======================================================== */

    function openMeetingLink(scheduleId) {

        const schedule =
            getSchedule(scheduleId);


        if (!schedule) {

            console.error(
                "[Schedule] Schedule not found:",
                scheduleId
            );

            return;

        }


        const mode =
            String(
                schedule.mode || ""
            ).toUpperCase();


        if (
            mode !== "ONLINE" &&
            mode !== "HYBRID"
        ) {

            return;

        }


        const meetingLink =
            String(
                schedule.meeting_link || ""
            ).trim();


        if (!meetingLink) {

            alert(
                "Meeting link is not available for this schedule."
            );

            return;

        }


        let url =
            meetingLink;


        if (
            !/^https?:\/\//i.test(url)
        ) {

            url =
                "https://" +
                url;

        }


        window.open(
            url,
            "_blank",
            "noopener,noreferrer"
        );

    }


    /* ========================================================
       MAKE ONLINE / HYBRID MODE CLICKABLE
    ======================================================== */

    function initializeMeetingLinks() {

        const rows =
            document.querySelectorAll(
                ".schedule-row"
            );


        const schedules =
            Array.isArray(
                window.scheduleData
            )
                ? window.scheduleData
                : [];


        rows.forEach(
            function (row, index) {

                const modeBadge =
                    row.querySelector(
                        ".mode-badge"
                    );


                if (!modeBadge) {
                    return;
                }


                /*
                 * Prefer an explicit schedule ID
                 * when the HTML provides one.
                 */

                const explicitId =
                    row.dataset.scheduleId;


                let schedule =
                    null;


                if (explicitId) {

                    schedule =
                        getSchedule(
                            explicitId
                        );

                }


                /*
                 * Fallback to scheduleData order.
                 */

                if (!schedule) {

                    schedule =
                        schedules[index];

                }


                if (!schedule) {
                    return;
                }


                const mode =
                    String(
                        schedule.mode || ""
                    ).toUpperCase();


                modeBadge.classList.remove(
                    "meeting-link-clickable"
                );


                modeBadge.removeAttribute(
                    "role"
                );


                modeBadge.removeAttribute(
                    "tabindex"
                );


                modeBadge.removeAttribute(
                    "title"
                );


                modeBadge.onclick = null;


                /*
                 * OFFLINE
                 */

                if (
                    mode !== "ONLINE" &&
                    mode !== "HYBRID"
                ) {

                    return;

                }


                /*
                 * ONLINE / HYBRID
                 */

                modeBadge.classList.add(
                    "meeting-link-clickable"
                );


                modeBadge.setAttribute(
                    "role",
                    "button"
                );


                modeBadge.setAttribute(
                    "tabindex",
                    "0"
                );


                const hasLink =
                    Boolean(
                        String(
                            schedule.meeting_link ||
                            ""
                        ).trim()
                    );


                modeBadge.setAttribute(
                    "title",
                    hasLink
                        ? "Open meeting link"
                        : "Meeting link not available"
                );


                modeBadge.onclick =
                    function (event) {

                        event.preventDefault();

                        event.stopPropagation();


                        openMeetingLink(
                            schedule.id
                        );

                    };


                modeBadge.onkeydown =
                    function (event) {

                        if (
                            event.key ===
                                "Enter" ||
                            event.key ===
                                " "
                        ) {

                            event.preventDefault();


                            openMeetingLink(
                                schedule.id
                            );

                        }

                    };

            }
        );


        refreshIcons();

    }


    /* ========================================================
       OPEN MODAL
    ======================================================== */

    window.openScheduleModal =
        function (
            mode,
            scheduleId
        ) {

            const modal =
                byId("scheduleModal");


            const form =
                byId("scheduleForm");


            const modalTitle =
                byId("modalTitle");


            const modalSubtitle =
                byId("modalSubtitle");


            const saveButton =
                byId(
                    "saveScheduleButton"
                );


            if (
                !modal ||
                !form
            ) {

                console.error(
                    "[Schedule] Modal or form not found."
                );


                return;

            }


            clearErrors();


            /*
             * Re-enable save button
             */

            if (saveButton) {

                saveButton.disabled =
                    false;


                saveButton.style.opacity =
                    "";


                saveButton.style.cursor =
                    "";

            }


            /* =================================================
               EDIT
            ================================================= */

            if (
                mode === "edit" &&
                scheduleId
            ) {

                const schedule =
                    getSchedule(
                        scheduleId
                    );


                if (!schedule) {

                    console.error(
                        "[Schedule] Schedule not found:",
                        scheduleId
                    );


                    return;

                }


                if (modalTitle) {

                    modalTitle.textContent =
                        "Edit Schedule";

                }


                if (modalSubtitle) {

                    modalSubtitle.textContent =
                        "Update the training session details.";

                }


                form.action =
                    window.scheduleEditBaseUrl
                        .replace(
                            "__SCHEDULE_ID__",
                            schedule.id
                        );


                setValue(
                    "scheduleId",
                    schedule.id
                );


                setValue(
                    "title",
                    schedule.title
                );


                setValue(
                    "project_id",
                    schedule.project_id
                );


                /*
                 * Load trainers belonging to
                 * selected project.
                 */

                updateTrainers(
                    schedule.trainer_id
                );


                setValue(
                    "start_datetime",
                    schedule.start_datetime
                );


                setValue(
                    "end_datetime",
                    schedule.end_datetime
                );


                setValue(
                    "mode",
                    schedule.mode
                );


                setValue(
                    "location",
                    schedule.location
                );


                setValue(
                    "meeting_link",
                    schedule.meeting_link
                );


                setValue(
                    "notes",
                    schedule.notes
                );


                updateModeFields();

            }


            /* =================================================
               CREATE
            ================================================= */

            else {

                if (modalTitle) {

                    modalTitle.textContent =
                        "Add Schedule";

                }


                if (modalSubtitle) {

                    modalSubtitle.textContent =
                        "Create a new training session.";

                }


                form.reset();


                form.action =
                    window.scheduleCreateUrl;


                setValue(
                    "scheduleId",
                    ""
                );


                setValue(
                    "mode",
                    "OFFLINE"
                );


                updateTrainers();


                updateModeFields();

            }


            /*
             * Open modal
             */

            modal.classList.add(
                "is-open"
            );


            modal.setAttribute(
                "aria-hidden",
                "false"
            );


            document.body.classList.add(
                "modal-open"
            );


            /*
             * Start modal at top
             */

            const modalBody =
                modal.querySelector(
                    ".modal-body"
                );


            if (modalBody) {

                modalBody.scrollTop = 0;

            }


            refreshIcons();

        };


    /* ========================================================
       CLOSE MODAL
    ======================================================== */

    window.closeScheduleModal =
        function () {

            const modal =
                byId("scheduleModal");


            if (!modal) {
                return;
            }


            modal.classList.remove(
                "is-open"
            );


            modal.setAttribute(
                "aria-hidden",
                "true"
            );


            document.body.classList.remove(
                "modal-open"
            );

        };

    /* ========================================================
       CLOSE MODAL
    ======================================================== */

    window.closeScheduleModal =
        function () {

            const modal =
                byId("scheduleModal");

            if (!modal) {
                return;
            }

            modal.classList.remove(
                "is-open"
            );

            modal.setAttribute(
                "aria-hidden",
                "true"
            );

            document.body.classList.remove(
                "modal-open"
            );

        };


    /* ========================================================
       MEETING LINK
    ======================================================== */

    function openMeetingLink(scheduleId) {

        const schedule =
            getSchedule(scheduleId);

        if (!schedule) {

            console.error(
                "[Schedule] Schedule not found:",
                scheduleId
            );

            return;
        }

        const mode =
            String(
                schedule.mode || ""
            ).toUpperCase();

        /*
         * Meeting links are only valid
         * for ONLINE and HYBRID schedules.
         */
        if (
            mode !== "ONLINE" &&
            mode !== "HYBRID"
        ) {
            return;
        }

        const meetingLink =
            String(
                schedule.meeting_link || ""
            ).trim();

        /*
         * No meeting link available.
         */
        if (!meetingLink) {

            alert(
                "Meeting link is not available for this schedule."
            );

            return;
        }

        let url =
            meetingLink;

        /*
         * If the user entered something like:
         *
         * meet.google.com/abc
         *
         * automatically add https://
         */
        if (
            !/^https?:\/\//i.test(url)
        ) {

            url =
                "https://" + url;

        }

        /*
         * Open meeting in a new tab.
         */
        window.open(
            url,
            "_blank",
            "noopener,noreferrer"
        );

    };


    /* ========================================================
       MAKE ONLINE / HYBRID MODE CLICKABLE
    ======================================================== */

    function initializeMeetingLinks() {

        const rows =
            document.querySelectorAll(
                ".schedule-row"
            );

        const schedules =
            Array.isArray(
                window.scheduleData
            )
                ? window.scheduleData
                : [];

        rows.forEach(
            function (
                row,
                index
            ) {

                const modeBadge =
                    row.querySelector(
                        ".mode-badge"
                    );

                if (!modeBadge) {
                    return;
                }

                /*
                 * Try explicit schedule ID first.
                 */
                const explicitId =
                    row.dataset.scheduleId;

                let schedule =
                    null;

                if (explicitId) {

                    schedule =
                        getSchedule(
                            explicitId
                        );

                }

                /*
                 * Current schedule table
                 * follows the same order as
                 * window.scheduleData.
                 */
                if (!schedule) {

                    schedule =
                        schedules[index];

                }

                if (!schedule) {
                    return;
                }

                const mode =
                    String(
                        schedule.mode || ""
                    ).toUpperCase();

                /*
                 * Reset any previously
                 * initialized state.
                 */
                modeBadge.classList.remove(
                    "meeting-link-clickable"
                );

                modeBadge.removeAttribute(
                    "role"
                );

                modeBadge.removeAttribute(
                    "tabindex"
                );

                modeBadge.removeAttribute(
                    "title"
                );

                modeBadge.onclick =
                    null;

                modeBadge.onkeydown =
                    null;

                /*
                 * Offline mode should remain
                 * non-clickable.
                 */
                if (
                    mode !== "ONLINE" &&
                    mode !== "HYBRID"
                ) {
                    return;
                }

                /*
                 * Make Online / Hybrid clickable.
                 */
                modeBadge.classList.add(
                    "meeting-link-clickable"
                );

                modeBadge.setAttribute(
                    "role",
                    "button"
                );

                modeBadge.setAttribute(
                    "tabindex",
                    "0"
                );

                const hasLink =
                    Boolean(
                        String(
                            schedule.meeting_link || ""
                        ).trim()
                    );

                modeBadge.setAttribute(
                    "title",
                    hasLink
                        ? "Open meeting link"
                        : "Meeting link not available"
                );

                /*
                 * Mouse click.
                 */
                modeBadge.onclick =
                    function (event) {

                        event.preventDefault();

                        event.stopPropagation();

                        openMeetingLink(
                            schedule.id
                        );

                    };

                /*
                 * Keyboard accessibility.
                 *
                 * Enter / Space
                 */
                modeBadge.onkeydown =
                    function (event) {

                        if (
                            event.key === "Enter" ||
                            event.key === " "
                        ) {

                            event.preventDefault();

                            openMeetingLink(
                                schedule.id
                            );

                        }

                    };

            }
        );

        refreshIcons();

    }


    /* ========================================================
       SEARCH + FILTER
    ======================================================== */

    function applyScheduleFilters() {

        const searchInput =
            byId("scheduleSearch");

        const statusFilter =
            byId("statusFilter");

        const rows =
            Array.from(
                document.querySelectorAll(
                    ".schedule-row"
                )
            );

        const search =
            String(
                searchInput
                    ? searchInput.value
                    : ""
            )
            .trim()
            .toLowerCase();

        const selectedStatus =
            String(
                statusFilter
                    ? statusFilter.value
                    : "ALL"
            )
            .toUpperCase();

        let visibleCount =
            0;

        rows.forEach(
            function (row) {

                const rowSearch =
                    String(
                        row.dataset.search ||
                        ""
                    )
                    .toLowerCase();

                const rowStatus =
                    String(
                        row.dataset.status ||
                        ""
                    )
                    .toUpperCase();

                const matchesSearch =
                    !search ||
                    rowSearch.includes(
                        search
                    );

                const matchesStatus =
                    selectedStatus === "ALL" ||
                    rowStatus === selectedStatus;

                const visible =
                    matchesSearch &&
                    matchesStatus;

                row.style.display =
                    visible
                        ? ""
                        : "none";

                if (visible) {
                    visibleCount++;
                }

            }
        );

        updateScheduleCount(
            visibleCount
        );

    }


    /* ========================================================
       TABLE COUNT
    ======================================================== */

    function updateScheduleCount(
        visibleCount
    ) {

        const countElement =
            byId("scheduleCount");

        if (!countElement) {
            return;
        }

        const totalRows =
            document.querySelectorAll(
                ".schedule-row"
            ).length;

        if (totalRows === 0) {

            countElement.textContent =
                "Showing 0 schedules";

            return;

        }

        countElement.textContent =
            "Showing " +
            visibleCount +
            " of " +
            totalRows +
            " schedules";

    }


    /* ========================================================
       STATISTICS
    ======================================================== */

    function updateStatistics() {

        const schedules =
            Array.isArray(
                window.scheduleData
            )
                ? window.scheduleData
                : [];

        const total =
            schedules.length;

        const completed =
            schedules.filter(
                function (schedule) {

                    return String(
                        schedule.status || ""
                    ).toUpperCase() ===
                        "COMPLETED";

                }
            ).length;

        const cancelled =
            schedules.filter(
                function (schedule) {

                    return String(
                        schedule.status || ""
                    ).toUpperCase() ===
                        "CANCELLED";

                }
            ).length;

        const today =
            new Date();

        const todayYear =
            today.getFullYear();

        const todayMonth =
            today.getMonth();

        const todayDate =
            today.getDate();

        const todaySchedules =
            schedules.filter(
                function (schedule) {

                    if (
                        !schedule.start_datetime
                    ) {
                        return false;
                    }

                    const date =
                        new Date(
                            schedule.start_datetime
                        );

                    return (
                        date.getFullYear() ===
                            todayYear &&
                        date.getMonth() ===
                            todayMonth &&
                        date.getDate() ===
                            todayDate
                    );

                }
            ).length;

        const now =
            new Date();

        const upcoming =
            schedules.filter(
                function (schedule) {

                    const status =
                        String(
                            schedule.status ||
                            ""
                        ).toUpperCase();

                    if (
                        status === "COMPLETED" ||
                        status === "CANCELLED"
                    ) {
                        return false;
                    }

                    if (
                        !schedule.start_datetime
                    ) {
                        return false;
                    }

                    const start =
                        new Date(
                            schedule.start_datetime
                        );

                    return start >= now;

                }
            ).length;

        setText(
            "totalSchedules",
            total
        );

        setText(
            "todaySchedules",
            todaySchedules
        );

        setText(
            "upcomingSchedules",
            upcoming
        );

        setText(
            "completedSchedules",
            completed
        );

    }


    /* ========================================================
       FORM VALIDATION
    ======================================================== */

    function validateScheduleForm() {

        clearErrors();

        const title =
            byId("title");

        const project =
            byId("project_id");

        const trainer =
            byId("trainer_id");

        const start =
            byId("start_datetime");

        const end =
            byId("end_datetime");

        const mode =
            byId("mode");

        const location =
            byId("location");

        const meeting =
            byId("meeting_link");

        let valid =
            true;


        /* ---------------------------------------------
           Title
        --------------------------------------------- */

        if (
            !title ||
            !title.value.trim()
        ) {

            showError(
                "title",
                "titleError",
                "Session title is required."
            );

            valid =
                false;

        }


        /* ---------------------------------------------
           Project
        --------------------------------------------- */

        if (
            !project ||
            !project.value
        ) {

            showError(
                "project_id",
                "projectError",
                "Please select a project."
            );

            valid =
                false;

        }


        /* ---------------------------------------------
           Trainer
        --------------------------------------------- */

        if (
            !trainer ||
            !trainer.value
        ) {

            showError(
                "trainer_id",
                "trainerError",
                "Please select a trainer."
            );

            valid =
                false;

        }


        /* ---------------------------------------------
           Start
        --------------------------------------------- */

        if (
            !start ||
            !start.value
        ) {

            showError(
                "start_datetime",
                "startError",
                "Start date and time is required."
            );

            valid =
                false;

        }


        /* ---------------------------------------------
           End
        --------------------------------------------- */

        if (
            !end ||
            !end.value
        ) {

            showError(
                "end_datetime",
                "endError",
                "End date and time is required."
            );

            valid =
                false;

        }


        /* ---------------------------------------------
           Date comparison
        --------------------------------------------- */

        if (
            start &&
            end &&
            start.value &&
            end.value
        ) {

            const startDate =
                new Date(
                    start.value
                );

            const endDate =
                new Date(
                    end.value
                );

            if (
                endDate <= startDate
            ) {

                showError(
                    "end_datetime",
                    "endError",
                    "End time must be after start time."
                );

                valid =
                    false;

            }

        }


        /* ---------------------------------------------
           Offline
        --------------------------------------------- */

        if (
            mode &&
            mode.value === "OFFLINE"
        ) {

            if (
                location &&
                !location.value.trim()
            ) {

                showError(
                    "location",
                    null,
                    "Location is required."
                );

                valid =
                    false;

            }

        }


        /* ---------------------------------------------
           Online / Hybrid
        --------------------------------------------- */

        if (
            mode &&
            (
                mode.value === "ONLINE" ||
                mode.value === "HYBRID"
            )
        ) {

            if (
                meeting &&
                !meeting.value.trim()
            ) {

                showError(
                    "meeting_link",
                    null,
                    "Meeting link is required."
                );

                valid =
                    false;

            }

        }

        return valid;

    }


    /* ========================================================
       DOM READY
    ======================================================== */

    document.addEventListener(
        "DOMContentLoaded",
        function () {


            /* ---------------------------------------------
               Project change
            --------------------------------------------- */

            const projectSelect =
                byId("project_id");

            if (projectSelect) {

                projectSelect.addEventListener(
                    "change",
                    function () {

                        updateTrainers();

                    }
                );

            }


            /* ---------------------------------------------
               Mode change
            --------------------------------------------- */

            const modeSelect =
                byId("mode");

            if (modeSelect) {

                modeSelect.addEventListener(
                    "change",
                    function () {

                        updateModeFields();

                    }
                );

            }


            /* ---------------------------------------------
               Search
            --------------------------------------------- */

            const searchInput =
                byId("scheduleSearch");

            if (searchInput) {

                searchInput.addEventListener(
                    "input",
                    applyScheduleFilters
                );

            }


            /* ---------------------------------------------
               Status
            --------------------------------------------- */

            const statusFilter =
                byId("statusFilter");

            if (statusFilter) {

                statusFilter.addEventListener(
                    "change",
                    applyScheduleFilters
                );

            }


            /* ---------------------------------------------
               Form submit
            --------------------------------------------- */

            const form =
                byId("scheduleForm");

            if (form) {

                form.addEventListener(
                    "submit",
                    function (event) {

                        if (
                            !validateScheduleForm()
                        ) {

                            event.preventDefault();

                            return;

                        }

                        const saveButton =
                            byId(
                                "saveScheduleButton"
                            );

                        if (saveButton) {

                            saveButton.disabled =
                                true;

                            saveButton.style.opacity =
                                "0.7";

                            saveButton.style.cursor =
                                "not-allowed";

                        }

                    }
                );

            }


            /* ---------------------------------------------
               Overlay
            --------------------------------------------- */

            const modal =
                byId("scheduleModal");

            if (modal) {

                const overlay =
                    modal.querySelector(
                        ".modal-overlay"
                    );

                if (overlay) {

                    overlay.addEventListener(
                        "click",
                        function () {

                            window.closeScheduleModal();

                        }
                    );

                }

            }


            /* ---------------------------------------------
               Escape
            --------------------------------------------- */

            document.addEventListener(
                "keydown",
                function (event) {

                    if (
                        event.key !== "Escape"
                    ) {
                        return;
                    }

                    const modal =
                        byId(
                            "scheduleModal"
                        );

                    if (
                        modal &&
                        modal.classList.contains(
                            "is-open"
                        )
                    ) {

                        window.closeScheduleModal();

                    }

                }
            );


            /* ---------------------------------------------
               Initial state
            --------------------------------------------- */

            updateTrainers();

            updateModeFields();

            updateStatistics();

            applyScheduleFilters();

            refreshIcons();

            /*
             * Initialize clickable
             * Online / Hybrid meeting links.
             */
            initializeMeetingLinks();

        }

    );

})();

/* ============================================================
   QT PLATFORM
   TRAINING SCHEDULE JAVASCRIPT
============================================================ */

(function () {

    "use strict";


    /* ========================================================
       BASIC HELPERS
    ======================================================== */

    function byId(id) {

        return document.getElementById(id);

    }


    function refreshIcons() {

        if (
            typeof lucide !== "undefined" &&
            typeof lucide.createIcons === "function"
        ) {

            lucide.createIcons();

        }

    }


    function setValue(id, value) {

        const element =
            byId(id);

        if (!element) {
            return;
        }

        element.value =
            value === undefined ||
            value === null
                ? ""
                : value;

    }


    function setText(id, value) {

        const element =
            byId(id);

        if (element) {

            element.textContent =
                String(value);

        }

    }


    function getSchedule(id) {

        const schedules =
            Array.isArray(window.scheduleData)
                ? window.scheduleData
                : [];

        return schedules.find(
            schedule =>
                Number(schedule.id) ===
                Number(id)
        );

    }


    /* ========================================================
       FORM ERRORS
    ======================================================== */

    function clearErrors() {

        document
            .querySelectorAll(
                ".form-field.has-error"
            )
            .forEach(
                function (field) {

                    field.classList.remove(
                        "has-error"
                    );

                }
            );


        document
            .querySelectorAll(
                ".field-error"
            )
            .forEach(
                function (error) {

                    error.textContent = "";

                }
            );

    }


    function showError(
        fieldId,
        errorId,
        message
    ) {

        const field =
            byId(fieldId);

        if (field) {

            const wrapper =
                field.closest(
                    ".form-field"
                );

            if (wrapper) {

                wrapper.classList.add(
                    "has-error"
                );

            }

        }


        if (errorId) {

            const error =
                byId(errorId);

            if (error) {

                error.textContent =
                    message;

            }

        }

    }


    /* ========================================================
       TRAINER LOADING
    ======================================================== */

    function updateTrainers(
        selectedTrainerId
    ) {

        const projectSelect =
            byId("project_id");

        const trainerSelect =
            byId("trainer_id");

        if (
            !projectSelect ||
            !trainerSelect
        ) {

            return;

        }


        const projectId =
            String(
                projectSelect.value || ""
            ).trim();


        trainerSelect.innerHTML = "";


        const defaultOption =
            document.createElement(
                "option"
            );

        defaultOption.value = "";

        defaultOption.textContent =
            projectId
                ? "Select trainer"
                : "Select project first";

        trainerSelect.appendChild(
            defaultOption
        );


        if (!projectId) {

            trainerSelect.disabled =
                true;

            return;

        }


        trainerSelect.disabled =
            false;


        const trainerMap =
            window.scheduleTrainerMap || {};


        console.log(
            "[Schedule] Trainer map:",
            trainerMap
        );

        console.log(
            "[Schedule] Project:",
            projectId
        );


        let trainers = [];


        if (
            Object.prototype.hasOwnProperty.call(
                trainerMap,
                projectId
            )
        ) {

            trainers =
                trainerMap[projectId];

        }

        else if (
            Object.prototype.hasOwnProperty.call(
                trainerMap,
                Number(projectId)
            )
        ) {

            trainers =
                trainerMap[
                    Number(projectId)
                ];

        }

        else if (
            Array.isArray(trainerMap)
        ) {

            trainers =
                trainerMap.filter(
                    function (trainer) {

                        if (!trainer) {
                            return false;
                        }

                        const trainerProjectId =
                            trainer.project_id ??
                            trainer.projectId;

                        return String(
                            trainerProjectId
                        ) === projectId;

                    }
                );

        }


        if (!Array.isArray(trainers)) {

            trainers = [];

        }


        console.log(
            "[Schedule] Trainers:",
            trainers
        );


        if (trainers.length === 0) {

            const noTrainer =
                document.createElement(
                    "option"
                );

            noTrainer.value = "";

            noTrainer.textContent =
                "No trainers available";

            noTrainer.disabled =
                true;

            trainerSelect.appendChild(
                noTrainer
            );

            return;

        }


        trainers.forEach(
            function (trainer) {

                if (!trainer) {
                    return;
                }


                const trainerId =
                    trainer.id ??
                    trainer.trainer_id ??
                    trainer.user_id;


                const trainerName =
                    trainer.name ??
                    trainer.full_name ??
                    trainer.trainer_name ??
                    "Unnamed Trainer";


                if (
                    trainerId === undefined ||
                    trainerId === null
                ) {

                    return;

                }


                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    trainerId;

                option.textContent =
                    trainerName;


                if (trainer.location) {

                    option.textContent +=
                        " — " +
                        trainer.location;

                }


                if (
                    selectedTrainerId !== undefined &&
                    selectedTrainerId !== null &&
                    String(trainerId) ===
                        String(selectedTrainerId)
                ) {

                    option.selected =
                        true;

                }


                trainerSelect.appendChild(
                    option
                );

            }
        );


        if (
            selectedTrainerId !== undefined &&
            selectedTrainerId !== null
        ) {

            trainerSelect.value =
                String(
                    selectedTrainerId
                );

        }

    }


    /* ========================================================
       MODE FIELDS
    ======================================================== */

    function updateModeFields() {

        const mode =
            byId("mode");

        const locationField =
            byId("locationField");

        const meetingLinkField =
            byId("meetingLinkField");

        const location =
            byId("location");

        const meetingLink =
            byId("meeting_link");

        const locationRequired =
            byId("locationRequired");

        const meetingRequired =
            byId("meetingRequired");


        if (!mode) {
            return;
        }


        const selectedMode =
            String(
                mode.value || ""
            ).toUpperCase();


        /* ---------------------------------------------
           OFFLINE
        --------------------------------------------- */

        if (
            selectedMode ===
            "OFFLINE"
        ) {

            if (locationField) {

                locationField.style.display =
                    "flex";

            }


            if (meetingLinkField) {

                meetingLinkField.style.display =
                    "none";

            }


            if (location) {

                location.required =
                    true;

            }


            if (meetingLink) {

                meetingLink.required =
                    false;

            }


            if (locationRequired) {

                locationRequired.textContent =
                    "*";

            }


            if (meetingRequired) {

                meetingRequired.textContent =
                    "";

            }

        }


        /* ---------------------------------------------
           ONLINE
        --------------------------------------------- */

        else if (
            selectedMode ===
            "ONLINE"
        ) {

            if (locationField) {

                locationField.style.display =
                    "none";

            }


            if (meetingLinkField) {

                meetingLinkField.style.display =
                    "flex";

            }


            if (location) {

                location.required =
                    false;

            }


            if (meetingLink) {

                meetingLink.required =
                    true;

            }


            if (locationRequired) {

                locationRequired.textContent =
                    "";

            }


            if (meetingRequired) {

                meetingRequired.textContent =
                    "*";

            }

        }


        /* ---------------------------------------------
           HYBRID
        --------------------------------------------- */

        else {

            if (locationField) {

                locationField.style.display =
                    "flex";

            }


            if (meetingLinkField) {

                meetingLinkField.style.display =
                    "flex";

            }


            if (location) {

                location.required =
                    true;

            }


            if (meetingLink) {

                meetingLink.required =
                    true;

            }


            if (locationRequired) {

                locationRequired.textContent =
                    "*";

            }


            if (meetingRequired) {

                meetingRequired.textContent =
                    "*";

            }

        }

    }


    /* ========================================================
       MEETING LINK
    ======================================================== */

    function openMeetingLink(scheduleId) {

        const schedule =
            getSchedule(scheduleId);

        if (!schedule) {

            console.error(
                "[Schedule] Schedule not found:",
                scheduleId
            );

            return;

        }


        const mode =
            String(
                schedule.mode || ""
            ).toUpperCase();


        if (
            mode !== "ONLINE" &&
            mode !== "HYBRID"
        ) {

            return;

        }


        const meetingLink =
            String(
                schedule.meeting_link || ""
            ).trim();


        if (!meetingLink) {

            alert(
                "Meeting link is not available for this schedule."
            );

            return;

        }


        let url =
            meetingLink;


        if (
            !/^https?:\/\//i.test(url)
        ) {

            url =
                "https://" +
                url;

        }


        window.open(
            url,
            "_blank",
            "noopener,noreferrer"
        );

    }


    /* ========================================================
       MAKE ONLINE / HYBRID MODE CLICKABLE
    ======================================================== */

    function initializeMeetingLinks() {

        const rows =
            document.querySelectorAll(
                ".schedule-row"
            );

        const schedules =
            Array.isArray(
                window.scheduleData
            )
                ? window.scheduleData
                : [];


        rows.forEach(
            function (
                row,
                index
            ) {

                const modeBadge =
                    row.querySelector(
                        ".mode-badge"
                    );

                if (!modeBadge) {
                    return;
                }


                const explicitId =
                    row.dataset.scheduleId;


                let schedule =
                    null;


                if (explicitId) {

                    schedule =
                        getSchedule(
                            explicitId
                        );

                }


                if (!schedule) {

                    schedule =
                        schedules[index];

                }


                if (!schedule) {
                    return;
                }


                const mode =
                    String(
                        schedule.mode || ""
                    ).toUpperCase();


                modeBadge.classList.remove(
                    "meeting-link-clickable"
                );

                modeBadge.removeAttribute(
                    "role"
                );

                modeBadge.removeAttribute(
                    "tabindex"
                );

                modeBadge.removeAttribute(
                    "title"
                );

                modeBadge.onclick =
                    null;

                modeBadge.onkeydown =
                    null;


                if (
                    mode !== "ONLINE" &&
                    mode !== "HYBRID"
                ) {

                    return;

                }


                modeBadge.classList.add(
                    "meeting-link-clickable"
                );


                modeBadge.setAttribute(
                    "role",
                    "button"
                );


                modeBadge.setAttribute(
                    "tabindex",
                    "0"
                );


                const hasLink =
                    Boolean(
                        String(
                            schedule.meeting_link || ""
                        ).trim()
                    );


                modeBadge.setAttribute(
                    "title",
                    hasLink
                        ? "Open meeting link"
                        : "Meeting link not available"
                );


                modeBadge.onclick =
                    function (event) {

                        event.preventDefault();

                        event.stopPropagation();

                        openMeetingLink(
                            schedule.id
                        );

                    };


                modeBadge.onkeydown =
                    function (event) {

                        if (
                            event.key === "Enter" ||
                            event.key === " "
                        ) {

                            event.preventDefault();

                            openMeetingLink(
                                schedule.id
                            );

                        }

                    };

            }
        );


        refreshIcons();

    }


    /* ========================================================
       OPEN MODAL
    ======================================================== */

    window.openScheduleModal =
        function (
            mode,
            scheduleId
        ) {

            const modal =
                byId("scheduleModal");

            const form =
                byId("scheduleForm");

            const modalTitle =
                byId("modalTitle");

            const modalSubtitle =
                byId("modalSubtitle");

            const saveButton =
                byId(
                    "saveScheduleButton"
                );


            if (
                !modal ||
                !form
            ) {

                console.error(
                    "[Schedule] Modal or form not found."
                );

                return;

            }


            clearErrors();


            if (saveButton) {

                saveButton.disabled =
                    false;

                saveButton.style.opacity =
                    "";

                saveButton.style.cursor =
                    "";

            }


            /* =================================================
               EDIT
            ================================================= */

            if (
                mode === "edit" &&
                scheduleId
            ) {

                const schedule =
                    getSchedule(
                        scheduleId
                    );


                if (!schedule) {

                    console.error(
                        "[Schedule] Schedule not found:",
                        scheduleId
                    );

                    return;

                }


                if (modalTitle) {

                    modalTitle.textContent =
                        "Edit Schedule";

                }


                if (modalSubtitle) {

                    modalSubtitle.textContent =
                        "Update the training session details.";

                }


                form.action =
                    window.scheduleEditBaseUrl
                        .replace(
                            "__SCHEDULE_ID__",
                            schedule.id
                        );


                setValue(
                    "scheduleId",
                    schedule.id
                );


                setValue(
                    "title",
                    schedule.title
                );


                setValue(
                    "project_id",
                    schedule.project_id
                );


                updateTrainers(
                    schedule.trainer_id
                );


                setValue(
                    "start_datetime",
                    schedule.start_datetime
                );


                setValue(
                    "end_datetime",
                    schedule.end_datetime
                );


                setValue(
                    "mode",
                    schedule.mode
                );


                setValue(
                    "location",
                    schedule.location
                );


                setValue(
                    "meeting_link",
                    schedule.meeting_link
                );


                setValue(
                    "notes",
                    schedule.notes
                );


                updateModeFields();

            }


            /* =================================================
               CREATE
            ================================================= */

            else {

                if (modalTitle) {

                    modalTitle.textContent =
                        "Add Schedule";

                }


                if (modalSubtitle) {

                    modalSubtitle.textContent =
                        "Create a new training session.";

                }


                form.reset();


                form.action =
                    window.scheduleCreateUrl;


                setValue(
                    "scheduleId",
                    ""
                );


                setValue(
                    "mode",
                    "OFFLINE"
                );


                updateTrainers();

                updateModeFields();

            }


            modal.classList.add(
                "is-open"
            );


            modal.setAttribute(
                "aria-hidden",
                "false"
            );


            document.body.classList.add(
                "modal-open"
            );


            const modalBody =
                modal.querySelector(
                    ".modal-body"
                );


            if (modalBody) {

                modalBody.scrollTop =
                    0;

            }


            refreshIcons();

        };


    /* ========================================================
       CLOSE MODAL
    ======================================================== */

    window.closeScheduleModal =
        function () {

            const modal =
                byId("scheduleModal");

            if (!modal) {
                return;
            }


            modal.classList.remove(
                "is-open"
            );


            modal.setAttribute(
                "aria-hidden",
                "true"
            );


            document.body.classList.remove(
                "modal-open"
            );

        };


    /* ========================================================
       SEARCH + FILTER
    ======================================================== */

    function applyScheduleFilters() {

        const searchInput =
            byId("scheduleSearch");

        const statusFilter =
            byId("statusFilter");


        const rows =
            Array.from(
                document.querySelectorAll(
                    ".schedule-row"
                )
            );


        const search =
            String(
                searchInput
                    ? searchInput.value
                    : ""
            )
            .trim()
            .toLowerCase();


        const selectedStatus =
            String(
                statusFilter
                    ? statusFilter.value
                    : "ALL"
            ).toUpperCase();


        let visibleCount =
            0;


        rows.forEach(
            function (row) {

                const rowSearch =
                    String(
                        row.dataset.search ||
                        ""
                    )
                    .toLowerCase();


                const rowStatus =
                    String(
                        row.dataset.status ||
                        ""
                    )
                    .toUpperCase();


                const matchesSearch =
                    !search ||
                    rowSearch.includes(
                        search
                    );


                const matchesStatus =
                    selectedStatus === "ALL" ||
                    rowStatus === selectedStatus;


                const visible =
                    matchesSearch &&
                    matchesStatus;


                row.style.display =
                    visible
                        ? ""
                        : "none";


                if (visible) {

                    visibleCount++;

                }

            }
        );


        updateScheduleCount(
            visibleCount
        );

    }


    /* ========================================================
       TABLE COUNT
    ======================================================== */

    function updateScheduleCount(
        visibleCount
    ) {

        const countElement =
            byId("scheduleCount");


        if (!countElement) {
            return;
        }


        const totalRows =
            document.querySelectorAll(
                ".schedule-row"
            ).length;


        if (totalRows === 0) {

            countElement.textContent =
                "Showing 0 schedules";

            return;

        }


        countElement.textContent =
            "Showing " +
            visibleCount +
            " of " +
            totalRows +
            " schedules";

    }


    /* ========================================================
       STATISTICS
    ======================================================== */

    function updateStatistics() {

        const schedules =
            Array.isArray(
                window.scheduleData
            )
                ? window.scheduleData
                : [];


        const total =
            schedules.length;


        const completed =
            schedules.filter(
                function (schedule) {

                    return String(
                        schedule.status || ""
                    ).toUpperCase() ===
                        "COMPLETED";

                }
            ).length;


        const cancelled =
            schedules.filter(
                function (schedule) {

                    return String(
                        schedule.status || ""
                    ).toUpperCase() ===
                        "CANCELLED";

                }
            ).length;


        const today =
            new Date();


        const todayYear =
            today.getFullYear();

        const todayMonth =
            today.getMonth();

        const todayDate =
            today.getDate();


        const todaySchedules =
            schedules.filter(
                function (schedule) {

                    if (
                        !schedule.start_datetime
                    ) {

                        return false;

                    }


                    const date =
                        new Date(
                            schedule.start_datetime
                        );


                    return (
                        date.getFullYear() ===
                            todayYear &&
                        date.getMonth() ===
                            todayMonth &&
                        date.getDate() ===
                            todayDate
                    );

                }
            ).length;


        const now =
            new Date();


        const upcoming =
            schedules.filter(
                function (schedule) {

                    const status =
                        String(
                            schedule.status ||
                            ""
                        ).toUpperCase();


                    if (
                        status === "COMPLETED" ||
                        status === "CANCELLED"
                    ) {

                        return false;

                    }


                    if (
                        !schedule.start_datetime
                    ) {

                        return false;

                    }


                    const start =
                        new Date(
                            schedule.start_datetime
                        );


                    return start >= now;

                }
            ).length;


        setText(
            "totalSchedules",
            total
        );


        setText(
            "todaySchedules",
            todaySchedules
        );


        setText(
            "upcomingSchedules",
            upcoming
        );


        setText(
            "completedSchedules",
            completed
        );

    }


    /* ========================================================
       FORM VALIDATION
    ======================================================== */

    function validateScheduleForm() {

        clearErrors();


        const title =
            byId("title");

        const project =
            byId("project_id");

        const trainer =
            byId("trainer_id");

        const start =
            byId("start_datetime");

        const end =
            byId("end_datetime");

        const mode =
            byId("mode");

        const location =
            byId("location");

        const meeting =
            byId("meeting_link");


        let valid =
            true;


        /* ---------------------------------------------
           Title
        --------------------------------------------- */

        if (
            !title ||
            !title.value.trim()
        ) {

            showError(
                "title",
                "titleError",
                "Session title is required."
            );

            valid =
                false;

        }


        /* ---------------------------------------------
           Project
        --------------------------------------------- */

        if (
            !project ||
            !project.value
        ) {

            showError(
                "project_id",
                "projectError",
                "Please select a project."
            );

            valid =
                false;

        }


        /* ---------------------------------------------
           Trainer
        --------------------------------------------- */

        if (
            !trainer ||
            !trainer.value
        ) {

            showError(
                "trainer_id",
                "trainerError",
                "Please select a trainer."
            );

            valid =
                false;

        }


        /* ---------------------------------------------
           Start
        --------------------------------------------- */

        if (
            !start ||
            !start.value
        ) {

            showError(
                "start_datetime",
                "startError",
                "Start date and time is required."
            );

            valid =
                false;

        }


        /* ---------------------------------------------
           End
        --------------------------------------------- */

        if (
            !end ||
            !end.value
        ) {

            showError(
                "end_datetime",
                "endError",
                "End date and time is required."
            );

            valid =
                false;

        }


        /* ---------------------------------------------
           Date comparison
        --------------------------------------------- */

        if (
            start &&
            end &&
            start.value &&
            end.value
        ) {

            const startDate =
                new Date(
                    start.value
                );


            const endDate =
                new Date(
                    end.value
                );


            if (
                endDate <= startDate
            ) {

                showError(
                    "end_datetime",
                    "endError",
                    "End time must be after start time."
                );

                valid =
                    false;

            }

        }


        /* ---------------------------------------------
           Offline
        --------------------------------------------- */

        if (
            mode &&
            mode.value ===
                "OFFLINE"
        ) {

            if (
                location &&
                !location.value.trim()
            ) {

                showError(
                    "location",
                    null,
                    "Location is required."
                );

                valid =
                    false;

            }

        }


        /* ---------------------------------------------
           Online / Hybrid
        --------------------------------------------- */

        if (
            mode &&
            (
                mode.value ===
                    "ONLINE" ||
                mode.value ===
                    "HYBRID"
            )
        ) {

            if (
                meeting &&
                !meeting.value.trim()
            ) {

                showError(
                    "meeting_link",
                    null,
                    "Meeting link is required."
                );

                valid =
                    false;

            }

        }


        return valid;

    }


    /* ========================================================
       DOM READY
    ======================================================== */

    document.addEventListener(
        "DOMContentLoaded",
        function () {


            /* ---------------------------------------------
               Project change
            --------------------------------------------- */

            const projectSelect =
                byId("project_id");


            if (projectSelect) {

                projectSelect.addEventListener(
                    "change",
                    function () {

                        updateTrainers();

                    }
                );

            }


            /* ---------------------------------------------
               Mode change
            --------------------------------------------- */

            const modeSelect =
                byId("mode");


            if (modeSelect) {

                modeSelect.addEventListener(
                    "change",
                    function () {

                        updateModeFields();

                    }
                );

            }


            /* ---------------------------------------------
               Search
            --------------------------------------------- */

            const searchInput =
                byId("scheduleSearch");


            if (searchInput) {

                searchInput.addEventListener(
                    "input",
                    applyScheduleFilters
                );

            }


            /* ---------------------------------------------
               Status
            --------------------------------------------- */

            const statusFilter =
                byId("statusFilter");


            if (statusFilter) {

                statusFilter.addEventListener(
                    "change",
                    applyScheduleFilters
                );

            }


            /* ---------------------------------------------
               Form submit
            --------------------------------------------- */

            const form =
                byId("scheduleForm");


            if (form) {

                form.addEventListener(
                    "submit",
                    function (event) {

                        if (
                            !validateScheduleForm()
                        ) {

                            event.preventDefault();

                            return;

                        }


                        const saveButton =
                            byId(
                                "saveScheduleButton"
                            );


                        if (saveButton) {

                            saveButton.disabled =
                                true;

                            saveButton.style.opacity =
                                "0.7";

                            saveButton.style.cursor =
                                "not-allowed";

                        }

                    }
                );

            }


            /* ---------------------------------------------
               Overlay
            --------------------------------------------- */

            const modal =
                byId("scheduleModal");


            if (modal) {

                const overlay =
                    modal.querySelector(
                        ".modal-overlay"
                    );


                if (overlay) {

                    overlay.addEventListener(
                        "click",
                        function () {

                            window.closeScheduleModal();

                        }
                    );

                }

            }


            /* ---------------------------------------------
               Escape
            --------------------------------------------- */

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
                        byId(
                            "scheduleModal"
                        );


                    if (
                        modal &&
                        modal.classList.contains(
                            "is-open"
                        )
                    ) {

                        window.closeScheduleModal();

                    }

                }
            );


            /* ---------------------------------------------
               Initial state
            --------------------------------------------- */

            updateTrainers();

            updateModeFields();

            updateStatistics();

            applyScheduleFilters();

            refreshIcons();

            initializeMeetingLinks();

        }
    );

})();