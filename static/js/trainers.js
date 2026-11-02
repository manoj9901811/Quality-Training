/* =========================================================
   QT PLATFORM
   TRAINER MANAGEMENT JS
========================================================= */


/* =========================================================
   OPEN TRAINER MODAL
========================================================= */

function openTrainerModal() {

    const modal =
        document.getElementById(
            "trainerModal"
        );


    if (!modal) {
        return;
    }


    modal.classList.add("show");

    document.body.style.overflow =
        "hidden";


    setTimeout(function () {

        const name =
            document.getElementById(
                "trainer_full_name"
            );


        if (name) {

            name.focus();

        }

    }, 100);

}


/* =========================================================
   CLOSE TRAINER MODAL
========================================================= */

function closeTrainerModal() {

    const modal =
        document.getElementById(
            "trainerModal"
        );


    if (!modal) {
        return;
    }


    modal.classList.remove("show");

    document.body.style.overflow =
        "";

}


/* =========================================================
   SEARCH TRAINERS
========================================================= */

function searchTrainers() {

    const input =
        document.getElementById(
            "trainerSearch"
        );


    const table =
        document.getElementById(
            "trainersTable"
        );


    if (!input || !table) {
        return;
    }


    const search =
        input.value
            .toLowerCase()
            .trim();


    const availabilityFilter =
        document.getElementById(
            "availabilityFilter"
        );


    const selectedAvailability =
        availabilityFilter
            ? availabilityFilter.value
            : "";


    const rows =
        table.querySelectorAll(
            "tbody tr.trainer-row"
        );


    let visibleCount = 0;


    rows.forEach(function (row) {

        const text =
            row.textContent
                .toLowerCase();


        const availability =
            row.dataset.availability ||
            "";


        const matchesSearch =
            !search ||
            text.includes(search);


        const matchesAvailability =
            !selectedAvailability ||
            availability ===
                selectedAvailability;


        if (
            matchesSearch &&
            matchesAvailability
        ) {

            row.style.display = "";

            visibleCount++;

        } else {

            row.style.display = "none";

        }

    });


    updateTrainerResultMessage(
        visibleCount,
        rows.length
    );

}


/* =========================================================
   RESULT MESSAGE
========================================================= */

function updateTrainerResultMessage(
    visibleCount,
    totalCount
) {

    const message =
        document.getElementById(
            "trainerResultMessage"
        );


    if (!message) {
        return;
    }


    if (totalCount === 0) {

        message.textContent =
            "No trainers available";

        return;

    }


    if (
        visibleCount === totalCount
    ) {

        message.textContent =
            "Showing 1 to " +
            totalCount +
            " of " +
            totalCount +
            " trainers";

    } else {

        message.textContent =
            "Showing " +
            visibleCount +
            " of " +
            totalCount +
            " trainers";

    }

}


/* =========================================================
   RESET TRAINER FORM
========================================================= */

function resetTrainerForm() {

    const form =
        document.getElementById(
            "trainerForm"
        );


    if (form) {

        form.reset();

    }


    const experience =
        document.getElementById(
            "trainer_experience"
        );


    const rate =
        document.getElementById(
            "trainer_rate"
        );


    const availability =
        document.getElementById(
            "trainer_availability"
        );


    if (experience) {

        experience.value = "0";

    }


    if (rate) {

        rate.value = "0";

    }


    if (availability) {

        availability.value =
            "AVAILABLE";

    }

}


/* =========================================================
   MODAL BACKDROP
========================================================= */

function setupTrainerModal() {

    const modal =
        document.getElementById(
            "trainerModal"
        );


    if (!modal) {
        return;
    }


    modal.addEventListener(
        "click",
        function (event) {

            if (
                event.target === modal
            ) {

                closeTrainerModal();

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
                event.key === "Escape"
            ) {

                closeTrainerModal();

            }

        }
    );

}


/* =========================================================
   SEARCH EVENT
========================================================= */

function setupTrainerSearch() {

    const input =
        document.getElementById(
            "trainerSearch"
        );


    if (!input) {
        return;
    }


    input.addEventListener(
        "input",
        function () {

            searchTrainers();

        }
    );

}


/* =========================================================
   AVAILABILITY FILTER
========================================================= */

function setupAvailabilityFilter() {

    const filter =
        document.getElementById(
            "availabilityFilter"
        );


    if (!filter) {
        return;
    }


    filter.addEventListener(
        "change",
        function () {

            searchTrainers();

        }
    );

}


/* =========================================================
   LUCIDE ICONS
========================================================= */

function refreshTrainerIcons() {

    if (
        typeof lucide !==
        "undefined"
    ) {

        lucide.createIcons();

    }

}


/* =========================================================
   DOM READY
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        setupTrainerModal();

        setupEscapeKey();

        setupTrainerSearch();

        setupAvailabilityFilter();

        refreshTrainerIcons();

    }
);