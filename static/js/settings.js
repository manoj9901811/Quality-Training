document.addEventListener(
    "DOMContentLoaded",
    function () {


        /* ====================================================
           SETTINGS NAVIGATION
        ==================================================== */

        const navItems =
            document.querySelectorAll(
                ".settings-nav-item"
            );


        const sections =
            document.querySelectorAll(
                ".settings-section"
            );


        navItems.forEach(
            function (item) {

                item.addEventListener(
                    "click",
                    function () {

                        const target =
                            item.dataset.section;


                        navItems.forEach(
                            function (nav) {

                                nav.classList.remove(
                                    "active"
                                );

                            }
                        );


                        sections.forEach(
                            function (section) {

                                section.classList.remove(
                                    "active"
                                );

                            }
                        );


                        item.classList.add(
                            "active"
                        );


                        const targetSection =
                            document.querySelector(
                                `[data-section-content="${target}"]`
                            );


                        if (targetSection) {

                            targetSection.classList.add(
                                "active"
                            );

                        }

                    }
                );

            }
        );



        /* ====================================================
           PRIMARY COLOR
        ==================================================== */

        const colorInput =
            document.getElementById(
                "primaryColor"
            );


        const colorValue =
            document.getElementById(
                "primaryColorValue"
            );


        if (colorInput && colorValue) {

            colorInput.addEventListener(
                "input",
                function () {

                    colorValue.textContent =
                        colorInput.value.toUpperCase();

                }
            );

        }



        /* ====================================================
           RESET CONFIRMATION
        ==================================================== */

        const form =
            document.getElementById(
                "settingsForm"
            );


        if (form) {

            form.addEventListener(
                "reset",
                function (event) {

                    const confirmed =
                        window.confirm(
                            "Reset the current settings form?"
                        );


                    if (!confirmed) {

                        event.preventDefault();

                    }

                }
            );

        }



        /* ====================================================
           LUCIDE
        ==================================================== */

        if (
            window.lucide &&
            typeof lucide.createIcons ===
                "function"
        ) {

            lucide.createIcons();

        }

    }
);