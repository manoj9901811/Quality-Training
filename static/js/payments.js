document.addEventListener("DOMContentLoaded", function () {

    /* ========================================================
       LOAD PAYMENT DATA
       ======================================================== */

    const paymentDataElement =
        document.getElementById("payment-data");

    let payments = [];

    if (paymentDataElement) {

        try {

            payments =
                JSON.parse(
                    paymentDataElement.textContent || "[]"
                );

        } catch (error) {

            console.error(
                "[Payments] Unable to read payment data:",
                error
            );

            payments = [];

        }

    }


    /* ========================================================
       CREATE / EDIT MODAL ELEMENTS
       ======================================================== */

    const paymentModal =
        document.getElementById("paymentModal");

    const paymentForm =
        document.getElementById("paymentForm");

    const paymentModalHeading =
        document.getElementById(
            "paymentModalHeading"
        );

    const paymentAction =
        document.getElementById(
            "paymentAction"
        );

    const paymentId =
        document.getElementById(
            "paymentId"
        );

    const paymentProject =
        document.getElementById(
            "paymentProject"
        );

    const paymentTrainer =
        document.getElementById(
            "paymentTrainer"
        );

    const rateType =
        document.getElementById(
            "rateType"
        );

    const paymentRate =
        document.getElementById(
            "paymentRate"
        );

    const totalDays =
        document.getElementById(
            "totalDays"
        );

    const totalHours =
        document.getElementById(
            "totalHours"
        );

    const grossAmount =
        document.getElementById(
            "grossAmount"
        );

    const adjustmentAmount =
        document.getElementById(
            "adjustmentAmount"
        );

    const finalAmountPreview =
        document.getElementById(
            "finalAmountPreview"
        );

    const dueDate =
        document.getElementById(
            "dueDate"
        );

    const paymentStatus =
        document.getElementById(
            "paymentStatus"
        );

    const paymentMethod =
        document.getElementById(
            "paymentMethod"
        );

    const transactionReference =
        document.getElementById(
            "transactionReference"
        );

    const paymentNotes =
        document.getElementById(
            "paymentNotes"
        );

    const daysGroup =
        document.getElementById(
            "daysGroup"
        );

    const hoursGroup =
        document.getElementById(
            "hoursGroup"
        );


    /* ========================================================
       VIEW MODAL ELEMENTS
       ======================================================== */

    const viewPaymentModal =
        document.getElementById(
            "viewPaymentModal"
        );

    const viewPaymentCode =
        document.getElementById(
            "viewPaymentCode"
        );

    const viewPaymentStatus =
        document.getElementById(
            "viewPaymentStatus"
        );

    const viewPaymentProject =
        document.getElementById(
            "viewPaymentProject"
        );

    const viewPaymentTrainer =
        document.getElementById(
            "viewPaymentTrainer"
        );

    const viewPaymentRate =
        document.getElementById(
            "viewPaymentRate"
        );

    const viewPaymentRateType =
        document.getElementById(
            "viewPaymentRateType"
        );

    const viewPaymentGross =
        document.getElementById(
            "viewPaymentGross"
        );

    const viewPaymentAdjustment =
        document.getElementById(
            "viewPaymentAdjustment"
        );

    const viewPaymentFinal =
        document.getElementById(
            "viewPaymentFinal"
        );

    const viewPaymentDueDate =
        document.getElementById(
            "viewPaymentDueDate"
        );

    const viewPaymentDate =
        document.getElementById(
            "viewPaymentDate"
        );

    const viewPaymentMethod =
        document.getElementById(
            "viewPaymentMethod"
        );

    const viewPaymentReference =
        document.getElementById(
            "viewPaymentReference"
        );

    const viewPaymentNotes =
        document.getElementById(
            "viewPaymentNotes"
        );


    /* ========================================================
       FIND PAYMENT
       ======================================================== */

    function findPayment(id) {

        return payments.find(function (payment) {

            return String(payment.id) ===
                   String(id);

        });

    }


    /* ========================================================
       CURRENCY
       ======================================================== */

    function formatCurrency(value) {

        const number =
            Number(value || 0);

        return "₹" +
            number.toLocaleString(
                "en-IN",
                {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }
            );

    }


    /* ========================================================
       DATE
       ======================================================== */

    function formatDate(value) {

        if (!value) {
            return "—";
        }

        const parts =
            String(value).split("-");

        if (parts.length !== 3) {
            return value;
        }

        const months = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec"
        ];

        const month =
            months[
                Number(parts[1]) - 1
            ] || parts[1];

        return (
            parts[2] +
            " " +
            month +
            " " +
            parts[0]
        );

    }


    /* ========================================================
       TEXT
       ======================================================== */

    function formatText(value) {

        if (!value) {
            return "—";
        }

        return String(value)
            .replaceAll("_", " ");

    }


    /* ========================================================
       STATUS BADGE
       ======================================================== */

    function createStatusBadge(status) {

        const normalized =
            String(status || "")
                .toUpperCase();

        const cssClass =
            normalized.toLowerCase();

        return `
            <span class="payment-status ${cssClass}">
                ${formatText(normalized)}
            </span>
        `;

    }


    /* ========================================================
       ICON REFRESH
       ======================================================== */

    function refreshIcons() {

        if (
            typeof lucide !== "undefined" &&
            typeof lucide.createIcons === "function"
        ) {

            lucide.createIcons();

        }

    }


    /* ========================================================
       OPEN CREATE
       ======================================================== */

    function openCreatePaymentModal() {

        if (!paymentModal || !paymentForm) {
            return;
        }

        paymentForm.reset();

        paymentAction.value = "create";
        paymentId.value = "";

        paymentModalHeading.textContent =
            "Create Payment";

        rateType.value = "PER_DAY";

        paymentStatus.value =
            "PENDING";

        totalDays.value = "0";
        totalHours.value = "0";

        grossAmount.value = "0";
        adjustmentAmount.value = "0";

        finalAmountPreview.textContent =
            formatCurrency(0);

        updateRateFields();

        paymentModal.classList.add("show");

        paymentModal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "modal-open"
        );

        refreshIcons();

    }


    /* ========================================================
       OPEN EDIT
       ======================================================== */

    function openEditPaymentModal(id) {

        const payment =
            findPayment(id);

        if (!payment || !paymentModal) {
            return;
        }

        paymentModalHeading.textContent =
            "Edit Payment";

        paymentAction.value = "edit";

        paymentId.value =
            payment.id;

        paymentProject.value =
            String(
                payment.project_id || ""
            );

        paymentTrainer.value =
            String(
                payment.trainer_id || ""
            );

        rateType.value =
            payment.rate_type ||
            "PER_DAY";

        paymentRate.value =
            payment.rate || 0;

        totalDays.value =
            payment.total_days || 0;

        totalHours.value =
            payment.total_hours || 0;

        grossAmount.value =
            payment.gross_amount || 0;

        adjustmentAmount.value =
            payment.adjustment_amount || 0;

        dueDate.value =
            payment.due_date || "";

        paymentStatus.value =
            payment.status ||
            "PENDING";

        paymentMethod.value =
            payment.payment_method ||
            "";

        transactionReference.value =
            payment.transaction_reference ||
            "";

        paymentNotes.value =
            payment.notes ||
            "";

        updateRateFields();

        calculateAmount();

        paymentModal.classList.add("show");

        paymentModal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "modal-open"
        );

        refreshIcons();

    }


    /* ========================================================
       CLOSE CREATE / EDIT
       ======================================================== */

    function closePaymentModal() {

        if (!paymentModal) {
            return;
        }

        paymentModal.classList.remove(
            "show"
        );

        paymentModal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "modal-open"
        );

    }


    /* ========================================================
       RATE TYPE
       ======================================================== */

    function updateRateFields() {

        if (!rateType) {
            return;
        }

        const type =
            String(
                rateType.value || ""
            ).toUpperCase();


        if (type === "PER_DAY") {

            if (daysGroup) {
                daysGroup.style.display = "";
            }

            if (hoursGroup) {
                hoursGroup.style.display =
                    "none";
            }

        }

        else if (type === "PER_HOUR") {

            if (daysGroup) {
                daysGroup.style.display =
                    "none";
            }

            if (hoursGroup) {
                hoursGroup.style.display = "";
            }

        }

        else {

            if (daysGroup) {
                daysGroup.style.display =
                    "none";
            }

            if (hoursGroup) {
                hoursGroup.style.display =
                    "none";
            }

        }

    }


    /* ========================================================
       CALCULATE AMOUNT
       ======================================================== */

    function calculateAmount() {

        if (!rateType) {
            return;
        }

        const type =
            String(
                rateType.value || ""
            ).toUpperCase();

        const rate =
            Number(
                paymentRate.value || 0
            );

        const days =
            Number(
                totalDays.value || 0
            );

        const hours =
            Number(
                totalHours.value || 0
            );

        const adjustment =
            Number(
                adjustmentAmount.value || 0
            );

        let calculatedGross = 0;


        if (type === "PER_DAY") {

            calculatedGross =
                rate * days;

        }

        else if (type === "PER_HOUR") {

            calculatedGross =
                rate * hours;

        }

        else if (type === "FIXED") {

            calculatedGross =
                rate;

        }


        const finalAmount =
            calculatedGross +
            adjustment;


        if (grossAmount) {

            grossAmount.value =
                calculatedGross.toFixed(2);

        }


        if (finalAmountPreview) {

            finalAmountPreview.textContent =
                formatCurrency(
                    Math.max(
                        finalAmount,
                        0
                    )
                );

        }

    }


    /* ========================================================
       OPEN VIEW PAYMENT
       ======================================================== */

    function openViewPaymentModal(id) {

        const payment =
            findPayment(id);

        if (
            !payment ||
            !viewPaymentModal
        ) {

            console.error(
                "[Payments] Payment not found:",
                id
            );

            return;

        }


        if (viewPaymentCode) {

            viewPaymentCode.textContent =
                payment.payment_code ||
                "—";

        }


        if (viewPaymentStatus) {

            viewPaymentStatus.innerHTML =
                createStatusBadge(
                    payment.status
                );

        }


        if (viewPaymentProject) {

            let projectText = "—";

            if (payment.project_code) {

                projectText =
                    payment.project_code;

                if (
                    payment.project_name &&
                    payment.project_name !== "—"
                ) {

                    projectText +=
                        " - " +
                        payment.project_name;

                }

            }

            viewPaymentProject.textContent =
                projectText;

        }


        if (viewPaymentTrainer) {

            viewPaymentTrainer.textContent =
                payment.trainer_name ||
                "—";

        }


        if (viewPaymentRate) {

            viewPaymentRate.textContent =
                formatCurrency(
                    payment.rate
                );

        }


        if (viewPaymentRateType) {

            viewPaymentRateType.textContent =
                formatText(
                    payment.rate_type
                );

        }


        if (viewPaymentGross) {

            viewPaymentGross.textContent =
                formatCurrency(
                    payment.gross_amount
                );

        }


        if (viewPaymentAdjustment) {

            viewPaymentAdjustment.textContent =
                formatCurrency(
                    payment.adjustment_amount
                );

        }


        if (viewPaymentFinal) {

            viewPaymentFinal.textContent =
                formatCurrency(
                    payment.final_amount
                );

        }


        if (viewPaymentDueDate) {

            viewPaymentDueDate.textContent =
                formatDate(
                    payment.due_date
                );

        }


        if (viewPaymentDate) {

            viewPaymentDate.textContent =
                formatDate(
                    payment.payment_date
                );

        }


        if (viewPaymentMethod) {

            viewPaymentMethod.textContent =
                formatText(
                    payment.payment_method
                );

        }


        if (viewPaymentReference) {

            viewPaymentReference.textContent =
                payment.transaction_reference ||
                "—";

        }


        if (viewPaymentNotes) {

            viewPaymentNotes.textContent =
                payment.notes ||
                "—";

        }


        viewPaymentModal.classList.add(
            "show"
        );

        viewPaymentModal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "modal-open"
        );

        refreshIcons();

    }


    /* ========================================================
       CLOSE VIEW
       ======================================================== */

    function closeViewPaymentModal() {

        if (!viewPaymentModal) {
            return;
        }

        viewPaymentModal.classList.remove(
            "show"
        );

        viewPaymentModal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "modal-open"
        );

    }


    /* ========================================================
       MARK AS PAID
       ======================================================== */

    function markPaymentAsPaid(id) {

        const payment =
            findPayment(id);

        if (!payment) {
            return;
        }


        const confirmed =
            window.confirm(
                "Mark payment " +
                payment.payment_code +
                " as PAID?"
            );


        if (!confirmed) {
            return;
        }


        submitPaymentAction(
            "mark-paid",
            payment.id
        );

    }


    /* ========================================================
       POST ACTION
       ======================================================== */

    function submitPaymentAction(
        action,
        id
    ) {

        const form =
            document.createElement(
                "form"
            );

        form.method = "POST";

        form.action =
            window.location.pathname;


        const csrfInput =
            document.querySelector(
                '#paymentForm input[name="csrf_token"]'
            );


        if (csrfInput) {

            const csrf =
                document.createElement(
                    "input"
                );

            csrf.type = "hidden";
            csrf.name = "csrf_token";
            csrf.value =
                csrfInput.value;

            form.appendChild(csrf);

        }


        const actionInput =
            document.createElement(
                "input"
            );

        actionInput.type = "hidden";
        actionInput.name = "action";
        actionInput.value =
            action;

        form.appendChild(
            actionInput
        );


        const paymentInput =
            document.createElement(
                "input"
            );

        paymentInput.type = "hidden";
        paymentInput.name =
            "payment_id";

        paymentInput.value =
            id;

        form.appendChild(
            paymentInput
        );


        document.body.appendChild(
            form
        );

        form.submit();

    }


    /* ========================================================
       CREATE BUTTONS
       ======================================================== */

    [
        document.getElementById(
            "openCreatePayment"
        ),

        document.getElementById(
            "openCreatePaymentEmpty"
        )

    ].forEach(function (button) {

        if (!button) {
            return;
        }

        button.addEventListener(
            "click",
            openCreatePaymentModal
        );

    });


    /* ========================================================
       VIEW BUTTONS
       ======================================================== */

    document.querySelectorAll(
        ".view-payment"
    ).forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                openViewPaymentModal(
                    button.dataset.paymentId
                );

            }
        );

    });


    /* ========================================================
       EDIT BUTTONS
       ======================================================== */

    document.querySelectorAll(
        ".edit-payment"
    ).forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                openEditPaymentModal(
                    button.dataset.paymentId
                );

            }
        );

    });


    /* ========================================================
       MARK PAID BUTTONS
       ======================================================== */

    document.querySelectorAll(
        ".mark-paid-payment"
    ).forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                markPaymentAsPaid(
                    button.dataset.paymentId
                );

            }
        );

    });


    /* ========================================================
       RATE EVENTS
       ======================================================== */

    if (rateType) {

        rateType.addEventListener(
            "change",
            function () {

                updateRateFields();
                calculateAmount();

            }
        );

    }


    [
        paymentRate,
        totalDays,
        totalHours,
        adjustmentAmount

    ].forEach(function (input) {

        if (!input) {
            return;
        }

        input.addEventListener(
            "input",
            calculateAmount
        );

        input.addEventListener(
            "change",
            calculateAmount
        );

    });


    /* ========================================================
       FORM VALIDATION
       ======================================================== */

    if (paymentForm) {

        paymentForm.addEventListener(
            "submit",
            function (event) {

                const project =
                    paymentProject.value;

                const trainer =
                    paymentTrainer.value;

                const rate =
                    Number(
                        paymentRate.value || 0
                    );

                const type =
                    String(
                        rateType.value || ""
                    ).toUpperCase();


                if (!project) {

                    event.preventDefault();

                    alert(
                        "Please select a project."
                    );

                    return;

                }


                if (!trainer) {

                    event.preventDefault();

                    alert(
                        "Please select a trainer."
                    );

                    return;

                }


                if (rate < 0) {

                    event.preventDefault();

                    alert(
                        "Rate cannot be negative."
                    );

                    return;

                }


                if (
                    type === "PER_DAY" &&
                    Number(
                        totalDays.value || 0
                    ) <= 0
                ) {

                    event.preventDefault();

                    alert(
                        "Please enter the total number of days."
                    );

                    return;

                }


                if (
                    type === "PER_HOUR" &&
                    Number(
                        totalHours.value || 0
                    ) <= 0
                ) {

                    event.preventDefault();

                    alert(
                        "Please enter the total number of hours."
                    );

                    return;

                }


                if (
                    type === "FIXED" &&
                    rate <= 0
                ) {

                    event.preventDefault();

                    alert(
                        "Please enter a valid payment amount."
                    );

                    return;

                }


                const gross =
                    Number(
                        grossAmount.value || 0
                    );

                const adjustment =
                    Number(
                        adjustmentAmount.value || 0
                    );


                if (
                    gross + adjustment < 0
                ) {

                    event.preventDefault();

                    alert(
                        "Final amount cannot be negative."
                    );

                    return;

                }


                const message =
                    paymentAction.value === "edit"
                        ? "Update this payment?"
                        : "Create this payment?";


                if (
                    !window.confirm(message)
                ) {

                    event.preventDefault();

                }

            }
        );

    }


    /* ========================================================
       CLOSE BUTTONS
       ======================================================== */

    const closePaymentButton =
        document.getElementById(
            "closePaymentModal"
        );

    const cancelPaymentButton =
        document.getElementById(
            "cancelPaymentModal"
        );

    const closeViewPaymentButton =
        document.getElementById(
            "closeViewPaymentModal"
        );

    const closeViewPaymentFooter =
        document.getElementById(
            "closeViewPaymentButton"
        );


    if (closePaymentButton) {

        closePaymentButton.addEventListener(
            "click",
            closePaymentModal
        );

    }


    if (cancelPaymentButton) {

        cancelPaymentButton.addEventListener(
            "click",
            closePaymentModal
        );

    }


    if (closeViewPaymentButton) {

        closeViewPaymentButton.addEventListener(
            "click",
            closeViewPaymentModal
        );

    }


    if (closeViewPaymentFooter) {

        closeViewPaymentFooter.addEventListener(
            "click",
            closeViewPaymentModal
        );

    }


    /* ========================================================
       BACKGROUND CLICK
       ======================================================== */

    if (paymentModal) {

        const background =
            paymentModal.querySelector(
                ".modal-background"
            );

        if (background) {

            background.addEventListener(
                "click",
                closePaymentModal
            );

        }

    }


    if (viewPaymentModal) {

        const background =
            viewPaymentModal.querySelector(
                ".modal-background"
            );

        if (background) {

            background.addEventListener(
                "click",
                closeViewPaymentModal
            );

        }

    }


    /* ========================================================
       ESCAPE
       ======================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (event.key !== "Escape") {
                return;
            }

            closePaymentModal();
            closeViewPaymentModal();

        }
    );


    /* ========================================================
       INITIALIZE
       ======================================================== */

    updateRateFields();
    calculateAmount();
    refreshIcons();

});