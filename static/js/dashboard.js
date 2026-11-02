document.addEventListener("DOMContentLoaded", function () {

    const greetingElement =
        document.getElementById("greetingText");

    const dateElement =
        document.getElementById("currentDate");


    function updateDateAndGreeting() {

        const now = new Date();


        /*
         * Always use India Standard Time.
         * This keeps the dashboard correct even
         * when the server is hosted in another timezone.
         */

        const indiaParts =
            new Intl.DateTimeFormat("en-IN", {
                timeZone: "Asia/Kolkata",
                hour: "numeric",
                minute: "numeric",
                hour12: false
            }).formatToParts(now);


        const hourPart =
            indiaParts.find(
                part => part.type === "hour"
            );


        const hour =
            Number(hourPart.value);


        let greeting;


        if (hour >= 5 && hour < 12) {

            greeting = "Good morning";

        } else if (hour >= 12 && hour < 17) {

            greeting = "Good afternoon";

        } else if (hour >= 17 && hour < 21) {

            greeting = "Good evening";

        } else {

            greeting = "Good night";

        }


        if (greetingElement) {
            greetingElement.textContent = greeting;
        }


        /*
         * Display today's date in India.
         */

        if (dateElement) {

            dateElement.textContent =
                new Intl.DateTimeFormat("en-IN", {
                    timeZone: "Asia/Kolkata",
                    weekday: "short",
                    day: "2-digit",
                    month: "short",
                    year: "numeric"
                }).format(now);

        }

    }


    updateDateAndGreeting();


    /*
     * Check every minute.
     * This allows the greeting to change automatically
     * without refreshing the dashboard.
     */

    setInterval(
        updateDateAndGreeting,
        60 * 1000
    );


    /*
     * Initialize Lucide icons if available.
     */

    if (typeof lucide !== "undefined") {
        lucide.createIcons();
    }

});