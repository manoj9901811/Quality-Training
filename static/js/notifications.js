"use strict";


/* ============================================================
   ICONS
============================================================ */

function refreshNotificationIcons() {

    if (
        typeof lucide !== "undefined"
    ) {

        lucide.createIcons();

    }

}


/* ============================================================
   FILTERS
============================================================ */

function applyNotificationFilter(
    filter
) {

    const items =
        document.querySelectorAll(
            ".notification-page-item"
        );

    items.forEach(
        function (item) {

            const isRead =
                item.dataset.read === "true";

            let show = true;


            if (filter === "unread") {

                show = !isRead;

            }


            if (filter === "read") {

                show = isRead;

            }


            item.style.display =
                show
                    ? ""
                    : "none";

        }
    );

}


/* ============================================================
   FILTER BUTTONS
============================================================ */

function setupNotificationFilters() {

    const buttons =
        document.querySelectorAll(
            ".notification-filter-button"
        );


    buttons.forEach(
        function (button) {

            button.addEventListener(
                "click",
                function () {

                    buttons.forEach(
                        function (item) {

                            item.classList.remove(
                                "active"
                            );

                        }
                    );


                    button.classList.add(
                        "active"
                    );


                    applyNotificationFilter(
                        button.dataset.filter
                    );

                }
            );

        }
    );

}


/* ============================================================
   INITIALIZATION
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        refreshNotificationIcons();

        setupNotificationFilters();

    }
);