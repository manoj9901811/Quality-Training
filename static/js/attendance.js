document.addEventListener("DOMContentLoaded", function () {

    const modal =
        document.getElementById("attendanceModal");

    const form =
        document.getElementById("attendanceForm");

    const closeButton =
        document.getElementById("closeModal");

    const cancelButton =
        document.getElementById("cancelModal");

    const background =
        modal
            ? modal.querySelector(".modal-background")
            : null;


    const scheduleId =
        document.getElementById("scheduleId");

    const attendanceDate =
        document.getElementById("attendanceDate");


    const modalHeading =
        document.getElementById("modalHeading");

    const modalSession =
        document.getElementById("modalSession");

    const modalTrainer =
        document.getElementById("modalTrainer");

    const modalDate =
        document.getElementById("modalDate");

    const checkIn =
        document.getElementById("checkIn");

    const checkOut =
        document.getElementById("checkOut");

    const remarks =
        document.getElementById("remarks");


    /* =====================================================
       OPEN ATTENDANCE MODAL
    ===================================================== */

    function openAttendanceModal(button) {

        if (!modal || !button) {
            return;
        }


        const id =
            button.dataset.scheduleId || "";

        const title =
            button.dataset.title || "Training Session";

        const trainer =
            button.dataset.trainer || "—";

        const date =
            button.dataset.date || "";

        const status =
            button.dataset.status || "";

        const checkInValue =
            button.dataset.checkIn || "";

        const checkOutValue =
            button.dataset.checkOut || "";

        const remarksValue =
            button.dataset.remarks || "";


        /* =================================================
           SET HIDDEN VALUES
        ================================================= */

        if (scheduleId) {
            scheduleId.value = id;
        }

        if (attendanceDate) {
            attendanceDate.value = date;
        }


        /* =================================================
           MODAL INFORMATION
        ================================================= */

        if (modalSession) {
            modalSession.textContent = title;
        }

        if (modalTrainer) {
            modalTrainer.textContent = trainer;
        }

        if (modalDate) {
            modalDate.textContent = formatDate(date);
        }


        /* =================================================
           EXISTING ATTENDANCE VALUES
        ================================================= */

        if (checkIn) {
            checkIn.value = checkInValue;
        }

        if (checkOut) {
            checkOut.value = checkOutValue;
        }

        if (remarks) {
            remarks.value = remarksValue;
        }


        /* =================================================
           RESET STATUS RADIO BUTTONS
        ================================================= */

        document
            .querySelectorAll('input[name="status"]')
            .forEach(function (radio) {

                radio.checked =
                    radio.value === status;

            });


        /* =================================================
           MODAL TITLE
        ================================================= */

        if (modalHeading) {

            if (status) {

                modalHeading.textContent =
                    "Edit Attendance";

            } else {

                modalHeading.textContent =
                    "Mark Attendance";

            }

        }


        /* =================================================
           SHOW MODAL
        ================================================= */

        modal.classList.add("show");

        document.body.classList.add("modal-open");


        refreshIcons();

    }


    /* =====================================================
       CLOSE ATTENDANCE MODAL
    ===================================================== */

    function closeAttendanceModal() {

        if (!modal) {
            return;
        }

        modal.classList.remove("show");

        document.body.classList.remove(
            "modal-open"
        );

    }


    /* =====================================================
       FORMAT DATE
    ===================================================== */

    function formatDate(value) {

        if (!value) {
            return "—";
        }


        const parts =
            value.split("-");


        if (parts.length !== 3) {
            return value;
        }


        return (
            parts[2] +
            "-" +
            parts[1] +
            "-" +
            parts[0]
        );

    }


    /* =====================================================
       ATTENDANCE BUTTONS
    ===================================================== */

    document
        .querySelectorAll(".attendance-button")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    openAttendanceModal(button);

                }
            );

        });


    /* =====================================================
       CLOSE BUTTON
    ===================================================== */

    if (closeButton) {

        closeButton.addEventListener(
            "click",
            closeAttendanceModal
        );

    }


    /* =====================================================
       CANCEL BUTTON
    ===================================================== */

    if (cancelButton) {

        cancelButton.addEventListener(
            "click",
            closeAttendanceModal
        );

    }


    /* =====================================================
       BACKGROUND CLICK
    ===================================================== */

    if (background) {

        background.addEventListener(
            "click",
            closeAttendanceModal
        );

    }


    /* =====================================================
       ESCAPE KEY
    ===================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Escape") {

                closeAttendanceModal();

            }

        }
    );


    /* =====================================================
       FORM VALIDATION
    ===================================================== */

    if (form) {

        form.addEventListener(
            "submit",
            function (event) {

                const selectedStatus =
                    document.querySelector(
                        'input[name="status"]:checked'
                    );


                if (!selectedStatus) {

                    event.preventDefault();

                    alert(
                        "Please select an attendance status."
                    );

                    return;

                }


                /* =========================================
                   CHECK-IN / CHECK-OUT VALIDATION
                ========================================= */

                if (
                    checkIn &&
                    checkOut &&
                    checkIn.value &&
                    checkOut.value &&
                    checkOut.value < checkIn.value
                ) {

                    event.preventDefault();

                    alert(
                        "Check-out time cannot be before check-in time."
                    );

                    return;

                }

            }
        );

    }


    /* =====================================================
       LUCIDE ICONS
    ===================================================== */

    function refreshIcons() {

        if (
            typeof lucide !== "undefined" &&
            typeof lucide.createIcons === "function"
        ) {

            lucide.createIcons();

        }

    }


    refreshIcons();

});
/* =====================================================
   PREVENT FUTURE ATTENDANCE POPUP
===================================================== */

const dateFilter = document.querySelector(
    'input[name="date"]'
);

if (dateFilter) {

    dateFilter.addEventListener(
        "change",
        function () {

            const selectedDate =
                this.value;

            if (!selectedDate) {
                return;
            }

            const today =
                new Date().toISOString().split("T")[0];

            if (selectedDate > today) {

                alert(
                    "⚠️ Future Attendance Not Allowed\n\n" +
                    "Attendance can only be marked " +
                    "for today or a past date."
                );

                this.value = today;
            }

        }
    );

}