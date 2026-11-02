document.addEventListener("DOMContentLoaded", function () {

    /* =========================================================
       ELEMENTS
    ========================================================== */

    const dataContainer =
        document.getElementById("communicationData");

    const conversationList =
        document.getElementById("conversationList");

    const searchInput =
        document.getElementById("conversationSearch");

    const chatWelcome =
        document.getElementById("chatWelcome");

    const activeChat =
        document.getElementById("activeChat");

    const messageArea =
        document.getElementById("messageArea");

    const chatAvatar =
        document.getElementById("chatAvatar");

    const chatUserName =
        document.getElementById("chatUserName");

    const chatUserRole =
        document.getElementById("chatUserRole");

    const chatReceiverId =
        document.getElementById("chatReceiverId");

    const chatSubject =
        document.getElementById("chatSubject");

    const chatMessage =
        document.getElementById("chatMessage");

    const messageComposer =
        document.getElementById("messageComposer");

    const attachmentButton =
        document.getElementById("attachmentButton");

    const chatFile =
        document.getElementById("chatFile");

    const attachmentPreview =
        document.getElementById("attachmentPreview");

    const emojiButton =
        document.getElementById("emojiButton");


    /* =========================================================
       MODAL
    ========================================================== */

    const modal =
        document.getElementById("composeModal");

    const newMessageButton =
        document.getElementById("newMessageButton");

    const newMessageButtonSmall =
        document.getElementById("newMessageButtonSmall");

    const welcomeNewMessage =
        document.getElementById("welcomeNewMessage");

    const modalClose =
        document.getElementById("modalClose");

    const modalCancel =
        document.getElementById("modalCancel");

    const modalBackground =
        document.getElementById("modalBackground");

    const newMessageForm =
        document.getElementById("newMessageForm");


    /* =========================================================
       STATE
    ========================================================== */

    let messages = [];

    let activePartnerId = null;

    let currentFilter = "all";


    /* =========================================================
       ICONS
    ========================================================== */

    function refreshIcons() {

        if (
            typeof lucide !== "undefined" &&
            lucide.createIcons
        ) {

            lucide.createIcons();

        }

    }


    /* =========================================================
       ESCAPE HTML
    ========================================================== */

    function escapeHtml(value) {

        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    }


    /* =========================================================
       DATE PARSER
    ========================================================== */

    function parseDate(value) {

        if (!value) {
            return 0;
        }

        const match =
            String(value).match(
                /^(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4}),\s+(\d{1,2}):(\d{2})\s*(AM|PM)$/i
            );

        if (!match) {

            const fallback =
                new Date(value).getTime();

            return isNaN(fallback)
                ? 0
                : fallback;

        }

        const months = {

            Jan: 0,
            Feb: 1,
            Mar: 2,
            Apr: 3,
            May: 4,
            Jun: 5,
            Jul: 6,
            Aug: 7,
            Sep: 8,
            Oct: 9,
            Nov: 10,
            Dec: 11

        };

        let hour =
            parseInt(match[4], 10);

        const minute =
            parseInt(match[5], 10);

        const period =
            match[6].toUpperCase();

        if (
            period === "PM" &&
            hour !== 12
        ) {

            hour += 12;

        }

        if (
            period === "AM" &&
            hour === 12
        ) {

            hour = 0;

        }

        return new Date(

            parseInt(match[3], 10),

            months[match[2]],

            parseInt(match[1], 10),

            hour,

            minute

        ).getTime();

    }


    /* =========================================================
       FILE SIZE
    ========================================================== */

    function formatFileSize(bytes) {

        bytes = Number(bytes || 0);

        if (!bytes) {
            return "";
        }

        if (bytes < 1024) {

            return bytes + " B";

        }

        if (bytes < 1024 * 1024) {

            return (
                (bytes / 1024).toFixed(1)
                + " KB"
            );

        }

        if (bytes < 1024 * 1024 * 1024) {

            return (
                (bytes / (1024 * 1024)).toFixed(1)
                + " MB"
            );

        }

        return (
            (bytes / (1024 * 1024 * 1024)).toFixed(1)
            + " GB"
        );

    }


    /* =========================================================
       LOAD SERVER DATA
    ========================================================== */

    if (dataContainer) {

        dataContainer
            .querySelectorAll(".message-data")
            .forEach(function (item) {

                messages.push({

                    id:
                        Number(
                            item.dataset.id
                        ),

                    type:
                        item.dataset.type,

                    partnerId:
                        Number(
                            item.dataset.partnerId
                        ),

                    partnerName:
                        item.dataset.partnerName ||
                        "User",

                    partnerRole:
                        item.dataset.partnerRole ||
                        "User",

                    subject:
                        item.dataset.subject ||
                        "Chat Message",

                    message:
                        item.dataset.message ||
                        "",

                    priority:
                        item.dataset.priority ||
                        "NORMAL",

                    read:
                        item.dataset.read === "true",

                    created:
                        item.dataset.created ||
                        "",

                    attachmentName:
                        item.dataset.attachmentName ||
                        "",

                    attachmentPath:
                        item.dataset.attachmentPath ||
                        "",

                    attachmentType:
                        item.dataset.attachmentType ||
                        "",

                    attachmentSize:
                        Number(
                            item.dataset.attachmentSize || 0
                        )

                });

            });

    }


    /* =========================================================
       SORT
    ========================================================== */

    messages.sort(function (a, b) {

        return (
            parseDate(a.created) -
            parseDate(b.created)
        );

    });


    /* =========================================================
       BUILD CONVERSATIONS
    ========================================================== */

    function buildConversations() {

        const map = new Map();

        const sorted =
            [...messages].sort(function (a, b) {

                return (
                    parseDate(b.created) -
                    parseDate(a.created)
                );

            });

        sorted.forEach(function (message) {

            if (!map.has(message.partnerId)) {

                map.set(
                    message.partnerId,
                    {

                        partnerId:
                            message.partnerId,

                        name:
                            message.partnerName,

                        role:
                            message.partnerRole,

                        latest:
                            message,

                        unread: 0

                    }
                );

            }

            if (
                message.type === "received" &&
                !message.read
            ) {

                map.get(
                    message.partnerId
                ).unread += 1;

            }

        });

        return Array.from(map.values());

    }


    /* =========================================================
       RENDER CONVERSATIONS
    ========================================================== */

    function renderConversations() {

        if (!conversationList) {
            return;
        }

        conversationList.innerHTML = "";

        let conversations =
            buildConversations();

        const search =
            (
                searchInput?.value ||
                ""
            )
            .trim()
            .toLowerCase();

        if (currentFilter === "unread") {

            conversations =
                conversations.filter(function (conversation) {

                    return conversation.unread > 0;

                });

        }

        if (search) {

            conversations =
                conversations.filter(function (conversation) {

                    return (

                        conversation.name
                            .toLowerCase()
                            .includes(search)

                        ||

                        conversation.role
                            .toLowerCase()
                            .includes(search)

                        ||

                        (
                            conversation.latest.message ||
                            ""
                        )
                        .toLowerCase()
                        .includes(search)

                    );

                });

        }

        if (!conversations.length) {

            conversationList.innerHTML = `

                <div class="conversation-empty">

                    <i data-lucide="message-square-off"></i>

                    <strong>
                        No conversations
                    </strong>

                    <span>
                        Start a new conversation.
                    </span>

                </div>

            `;

            refreshIcons();

            return;

        }

        conversations.forEach(function (conversation) {

            const latest =
                conversation.latest;

            const initials =
                getInitials(
                    conversation.name
                );

            const item =
                document.createElement("div");

            item.className =
                "conversation-item";

            if (
                Number(activePartnerId) ===
                Number(conversation.partnerId)
            ) {

                item.classList.add("active");

            }

            item.dataset.partnerId =
                conversation.partnerId;

            let preview =
                latest.message ||
                "";

            if (
                latest.attachmentName &&
                !preview
            ) {

                preview =
                    "📎 " +
                    latest.attachmentName;

            }

            item.innerHTML = `

                <div class="conversation-avatar">
                    ${escapeHtml(initials)}
                </div>

                <div class="conversation-content">

                    <div class="conversation-top">

                        <span class="conversation-name">
                            ${escapeHtml(
                                conversation.name
                            )}
                        </span>

                        <span class="conversation-time">
                            ${escapeHtml(
                                shortTime(
                                    latest.created
                                )
                            )}
                        </span>

                    </div>

                    <div class="conversation-preview">

                        <span class="conversation-preview-text">
                            ${escapeHtml(
                                preview ||
                                "No messages yet"
                            )}
                        </span>

                        ${
                            conversation.unread > 0
                            ?
                            `
                                <span class="unread-count">
                                    ${conversation.unread}
                                </span>
                            `
                            :
                            ""
                        }

                    </div>

                </div>

            `;

            item.addEventListener(
                "click",
                function () {

                    openConversation(
                        conversation.partnerId
                    );

                }
            );

            conversationList.appendChild(item);

        });

        refreshIcons();

    }


    /* =========================================================
       INITIALS
    ========================================================== */

    function getInitials(name) {

        const parts =
            String(name || "U")
                .trim()
                .split(/\s+/)
                .filter(Boolean);

        if (!parts.length) {
            return "U";
        }

        if (parts.length === 1) {

            return parts[0]
                .substring(0, 2)
                .toUpperCase();

        }

        return (
            parts[0][0] +
            parts[parts.length - 1][0]
        ).toUpperCase();

    }


    /* =========================================================
       SHORT TIME
    ========================================================== */

    function shortTime(value) {

        const timestamp =
            parseDate(value);

        if (!timestamp) {
            return "";
        }

        const date =
            new Date(timestamp);

        let hour =
            date.getHours();

        const minute =
            String(
                date.getMinutes()
            )
            .padStart(2, "0");

        const period =
            hour >= 12
                ? "PM"
                : "AM";

        hour =
            hour % 12 || 12;

        return (
            hour +
            ":" +
            minute +
            " " +
            period
        );

    }


    /* =========================================================
       SCROLL CHAT TO BOTTOM
       IMPORTANT:
       ONLY MESSAGE AREA SCROLLS
    ========================================================== */

    function scrollChatToBottom(smooth = false) {

        if (!messageArea) {
            return;
        }

        requestAnimationFrame(function () {

            if (smooth) {

                messageArea.scrollTo({
                    top: messageArea.scrollHeight,
                    behavior: "smooth"
                });

            } else {

                messageArea.scrollTop =
                    messageArea.scrollHeight;

            }

        });

    }


    /* =========================================================
       OPEN CONVERSATION
       DOES NOT CHANGE URL
    ========================================================== */

    function openConversation(partnerId) {

        activePartnerId =
            Number(partnerId);

        const conversationMessages =
            messages.filter(function (message) {

                return (
                    Number(message.partnerId) ===
                    Number(activePartnerId)
                );

            });

        if (!conversationMessages.length) {
            return;
        }

        const first =
            conversationMessages[0];

        chatWelcome?.classList.add("hidden");

        activeChat?.classList.add("active");

        if (chatUserName) {

            chatUserName.textContent =
                first.partnerName;

        }

        if (chatUserRole) {

            chatUserRole.textContent =
                first.partnerRole;

        }

        if (chatAvatar) {

            chatAvatar.textContent =
                getInitials(
                    first.partnerName
                );

        }

        if (chatReceiverId) {

            chatReceiverId.value =
                activePartnerId;

        }

        renderMessages(
            conversationMessages,
            false
        );

        markConversationRead(
            activePartnerId
        );

        renderConversations();

        chatMessage?.focus();

    }


    /* =========================================================
       RENDER MESSAGES
    ========================================================== */

    function renderMessages(
        list,
        smoothScroll = false
    ) {

        if (!messageArea) {
            return;
        }

        messageArea.innerHTML = "";

        const today =
            document.createElement("div");

        today.className =
            "today-label";

        today.textContent =
            "Today";

        messageArea.appendChild(today);

        const sortedList =
            [...list].sort(function (a, b) {

                return (
                    parseDate(a.created) -
                    parseDate(b.created)
                );

            });

        sortedList.forEach(function (message) {

            const row =
                document.createElement("div");

            row.className =
                "message-row " +
                (
                    message.type === "sent"
                        ? "sent"
                        : "received"
                );

            const bubble =
                document.createElement("div");

            bubble.className =
                "message-bubble";


            /* =================================================
               PRIORITY
            ================================================== */

            if (
                message.priority &&
                message.priority !== "NORMAL"
            ) {

                const priority =
                    document.createElement("div");

                priority.className =
                    "message-priority " +
                    String(
                        message.priority
                    ).toLowerCase();

                priority.textContent =
                    String(
                        message.priority
                    );

                bubble.appendChild(priority);

            }


            /* =================================================
               ATTACHMENT
            ================================================== */

            if (
                message.attachmentPath &&
                message.attachmentName
            ) {

                bubble.appendChild(
                    createMessageAttachment(
                        message
                    )
                );

            }


            /* =================================================
               TEXT
            ================================================== */

            if (
                message.message &&
                message.message.trim()
            ) {

                const text =
                    document.createElement("div");

                text.className =
                    "message-text";

                text.textContent =
                    message.message;

                bubble.appendChild(text);

            }


            /* =================================================
               META
            ================================================== */

            const meta =
                document.createElement("div");

            meta.className =
                "message-meta";

            meta.innerHTML = `

                <span>
                    ${escapeHtml(
                        shortTime(
                            message.created
                        )
                    )}
                </span>

                ${
                    message.type === "sent"
                    ?
                    `
                        <span class="message-status">
                            ✓✓
                        </span>
                    `
                    :
                    ""
                }

            `;

            bubble.appendChild(meta);

            row.appendChild(bubble);

            messageArea.appendChild(row);

        });


        /* =====================================================
           IMPORTANT:
           SCROLL ONLY MESSAGE AREA
        ====================================================== */

        scrollChatToBottom(
            smoothScroll
        );

        refreshIcons();

    }


    /* =========================================================
       CREATE ATTACHMENT
    ========================================================== */

    function createMessageAttachment(message) {

        const wrapper =
            document.createElement("div");

        wrapper.className =
            "message-attachment";

        const type =
            String(
                message.attachmentType ||
                ""
            ).toLowerCase();


        /* IMAGE */

        if (
            type.startsWith("image/")
        ) {

            const image =
                document.createElement("img");

            image.className =
                "message-image";

            image.src =
                getStaticFileUrl(
                    message.attachmentPath
                );

            image.alt =
                message.attachmentName;

            image.title =
                message.attachmentName;

            image.addEventListener(
                "click",
                function () {

                    window.open(
                        image.src,
                        "_blank"
                    );

                }
            );

            wrapper.appendChild(image);

            return wrapper;

        }


        /* FILE */

        const card =
            document.createElement("div");

        card.className =
            "message-file";

        card.innerHTML = `

            <div class="message-file-icon">
                <i data-lucide="file-text"></i>
            </div>

            <div class="message-file-info">

                <span class="message-file-name">
                    ${escapeHtml(
                        message.attachmentName
                    )}
                </span>

                <span class="message-file-size">
                    ${escapeHtml(
                        formatFileSize(
                            message.attachmentSize
                        )
                    )}
                </span>

            </div>

            <a
                class="message-file-download"
                href="${escapeHtml(
                    getStaticFileUrl(
                        message.attachmentPath
                    )
                )}"
                target="_blank"
                rel="noopener"
                title="Open file"
            >

                <i data-lucide="download"></i>

            </a>

        `;

        wrapper.appendChild(card);

        return wrapper;

    }


    /* =========================================================
       STATIC FILE URL
    ========================================================== */

    function getStaticFileUrl(path) {

        if (!path) {
            return "";
        }

        return (
            "/static/" +
            String(path)
                .replace(/^\/+/, "")
        );

    }


    /* =========================================================
       MARK READ
    ========================================================== */

    function markConversationRead(partnerId) {

        messages.forEach(function (message) {

            if (
                Number(message.partnerId) ===
                Number(partnerId)

                &&

                message.type === "received"
            ) {

                message.read = true;

            }

        });

    }


    /* =========================================================
       SEARCH
    ========================================================== */

    searchInput?.addEventListener(
        "input",
        function () {

            renderConversations();

        }
    );


    /* =========================================================
       FILTER
    ========================================================== */

    document
        .querySelectorAll(".chat-tab")
        .forEach(function (tab) {

            tab.addEventListener(
                "click",
                function () {

                    document
                        .querySelectorAll(".chat-tab")
                        .forEach(function (item) {

                            item.classList.remove(
                                "active"
                            );

                        });

                    tab.classList.add(
                        "active"
                    );

                    currentFilter =
                        tab.dataset.chatFilter ||
                        "all";

                    renderConversations();

                }
            );

        });


    /* =========================================================
       TEXTAREA RESIZE
    ========================================================== */

    function autoResizeTextarea() {

        if (!chatMessage) {
            return;
        }

        chatMessage.style.height =
            "48px";

        const height =
            Math.min(
                chatMessage.scrollHeight,
                120
            );

        chatMessage.style.height =
            height + "px";

    }


    chatMessage?.addEventListener(
        "input",
        autoResizeTextarea
    );


    /* =========================================================
       ENTER TO SEND
    ========================================================== */

    chatMessage?.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                if (
                    chatMessage.value.trim() ||
                    chatFile?.files.length
                ) {

                    messageComposer?.requestSubmit();

                }

            }

        }
    );


    /* =========================================================
       ATTACHMENT BUTTON
    ========================================================== */

    attachmentButton?.addEventListener(
        "click",
        function () {

            chatFile?.click();

        }
    );


    /* =========================================================
       FILE SELECTED
    ========================================================== */

    chatFile?.addEventListener(
        "change",
        function () {

            const file =
                chatFile.files?.[0];

            if (!file) {

                clearAttachment();

                return;

            }

            showAttachmentPreview(file);

            chatMessage?.focus();

        }
    );


    /* =========================================================
       ATTACHMENT PREVIEW
    ========================================================== */

    function showAttachmentPreview(file) {

        if (!attachmentPreview) {
            return;
        }

        attachmentPreview.innerHTML = "";

        const card =
            document.createElement("div");

        card.className =
            "attachment-preview-card";


        if (
            file.type &&
            file.type.startsWith("image/")
        ) {

            const image =
                document.createElement("img");

            image.className =
                "attachment-preview-image";

            const objectUrl =
                URL.createObjectURL(file);

            image.src =
                objectUrl;

            image.onload =
                function () {

                    URL.revokeObjectURL(
                        objectUrl
                    );

                };

            card.appendChild(image);

        }

        else {

            const icon =
                document.createElement("div");

            icon.className =
                "attachment-preview-icon";

            icon.innerHTML =
                `<i data-lucide="file-text"></i>`;

            card.appendChild(icon);

        }


        const info =
            document.createElement("div");

        info.className =
            "attachment-preview-info";

        info.innerHTML = `

            <div class="attachment-preview-name">
                ${escapeHtml(file.name)}
            </div>

            <div class="attachment-preview-size">
                ${escapeHtml(
                    formatFileSize(file.size)
                )}
            </div>

        `;

        card.appendChild(info);


        const remove =
            document.createElement("button");

        remove.type =
            "button";

        remove.className =
            "attachment-remove";

        remove.title =
            "Remove attachment";

        remove.innerHTML =
            `<i data-lucide="x"></i>`;

        remove.addEventListener(
            "click",
            clearAttachment
        );

        card.appendChild(remove);

        attachmentPreview.appendChild(card);

        attachmentPreview.classList.add("show");

        refreshIcons();

    }


    /* =========================================================
       CLEAR ATTACHMENT
    ========================================================== */

    function clearAttachment() {

        if (chatFile) {

            chatFile.value = "";

        }

        if (attachmentPreview) {

            attachmentPreview.innerHTML = "";

            attachmentPreview.classList.remove(
                "show"
            );

        }

    }


    /* =========================================================
       EMOJI
    ========================================================== */

    emojiButton?.addEventListener(
        "click",
        function () {

            if (!chatMessage) {
                return;
            }

            const emoji =
                "😊";

            const start =
                chatMessage.selectionStart ??
                chatMessage.value.length;

            const end =
                chatMessage.selectionEnd ??
                chatMessage.value.length;

            chatMessage.value =
                chatMessage.value.substring(
                    0,
                    start
                )
                +
                emoji
                +
                chatMessage.value.substring(
                    end
                );

            chatMessage.focus();

            const position =
                start +
                emoji.length;

            chatMessage.selectionStart =
                position;

            chatMessage.selectionEnd =
                position;

            autoResizeTextarea();

        }
    );


    /* =========================================================
       SEND MESSAGE
       AJAX / FETCH
       NO REFRESH
       NO URL CHANGE
    ========================================================== */

    messageComposer?.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const hasText =
                chatMessage &&
                chatMessage.value.trim();

            const hasFile =
                chatFile &&
                chatFile.files &&
                chatFile.files.length > 0;

            if (!chatReceiverId?.value) {

                alert(
                    "Please select a conversation first."
                );

                return;

            }

            if (
                !hasText &&
                !hasFile
            ) {

                alert(
                    "Please type a message or attach a file."
                );

                return;

            }

            const formData =
                new FormData(
                    messageComposer
                );

            const sendButton =
                messageComposer.querySelector(
                    ".send-button"
                );

            if (sendButton) {

                sendButton.disabled =
                    true;

            }

            try {

                const response =
                    await fetch(
                        "/communication",
                        {
                            method: "POST",
                            body: formData,

                            headers: {

                                "X-Requested-With":
                                    "XMLHttpRequest",

                                "Accept":
                                    "application/json"

                            }

                        }
                    );

                if (!response.ok) {

                    throw new Error(
                        "HTTP " +
                        response.status
                    );

                }

                const data =
                    await response.json();

                if (!data.success) {

                    alert(
                        data.message ||
                        "Unable to send message."
                    );

                    return;

                }


                /* =================================================
                   ADD MESSAGE TO LOCAL STATE
                ================================================== */

                if (data.message_data) {

                    messages.push(
                        data.message_data
                    );

                }


                /* =================================================
                   SORT
                ================================================== */

                messages.sort(
                    function (a, b) {

                        return (
                            parseDate(a.created) -
                            parseDate(b.created)
                        );

                    }
                );


                /* =================================================
                   KEEP SAME CHAT
                ================================================== */

                activePartnerId =
                    Number(
                        chatReceiverId.value
                    );


                /* =================================================
                   UPDATE CHAT
                ================================================== */

                const conversationMessages =
                    messages.filter(
                        function (message) {

                            return (
                                Number(
                                    message.partnerId
                                ) ===
                                Number(
                                    activePartnerId
                                )
                            );

                        }
                    );

                renderMessages(
                    conversationMessages,
                    true
                );

                renderConversations();


                /* =================================================
                   CLEAR MESSAGE
                ================================================== */

                if (chatMessage) {

                    chatMessage.value = "";

                    chatMessage.style.height =
                        "48px";

                }

                clearAttachment();

                chatMessage?.focus();


                /* =================================================
                   ALWAYS STAY AT BOTTOM
                ================================================== */

                scrollChatToBottom(true);

            }

            catch (error) {

                console.error(
                    "Send message error:",
                    error
                );

                alert(
                    "Unable to send the message. Please try again."
                );

            }

            finally {

                if (sendButton) {

                    sendButton.disabled =
                        false;

                }

            }

        }
    );


    /* =========================================================
       NEW MESSAGE MODAL
    ========================================================== */

    function openModal() {

        if (!modal) {
            return;
        }

        modal.classList.add(
            "active"
        );

        modal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.style.overflow =
            "hidden";

        setTimeout(
            function () {

                document
                    .getElementById(
                        "newReceiver"
                    )
                    ?.focus();

            },
            100
        );

    }


    function closeModal() {

        if (!modal) {
            return;
        }

        modal.classList.remove(
            "active"
        );

        modal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.style.overflow =
            "";

    }


    newMessageButton?.addEventListener(
        "click",
        openModal
    );

    newMessageButtonSmall?.addEventListener(
        "click",
        openModal
    );

    welcomeNewMessage?.addEventListener(
        "click",
        openModal
    );

    modalClose?.addEventListener(
        "click",
        closeModal
    );

    modalCancel?.addEventListener(
        "click",
        closeModal
    );

    modalBackground?.addEventListener(
        "click",
        closeModal
    );


    /* =========================================================
       ESC CLOSE
    ========================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape"
            ) {

                closeModal();

            }

        }
    );


    /* =========================================================
       NEW MESSAGE CHARACTER COUNT
    ========================================================== */

    const newMessage =
        document.getElementById(
            "newMessage"
        );

    const newMessageCount =
        document.getElementById(
            "newMessageCount"
        );

    newMessage?.addEventListener(
        "input",
        function () {

            if (newMessageCount) {

                newMessageCount.textContent =
                    newMessage.value.length;

            }

        }
    );


    /* =========================================================
       HEADER BUTTONS
    ========================================================== */

    document
        .getElementById(
            "searchMessagesButton"
        )
        ?.addEventListener(
            "click",
            function () {

                alert(
                    "Message search can be connected here."
                );

            }
        );


    document
        .getElementById(
            "callButton"
        )
        ?.addEventListener(
            "click",
            function () {

                alert(
                    "Voice calling can be connected here."
                );

            }
        );


    document
        .getElementById(
            "conversationInfoButton"
        )
        ?.addEventListener(
            "click",
            function () {

                if (!activePartnerId) {

                    alert(
                        "Please select a conversation first."
                    );

                    return;

                }

                alert(
                    "Conversation information can be shown here."
                );

            }
        );


    /* =========================================================
       NEW MESSAGE MODAL - AJAX
    ========================================================== */

    newMessageForm?.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const receiver =
                document.getElementById(
                    "newReceiver"
                );

            const message =
                document.getElementById(
                    "newMessage"
                );

            if (!receiver?.value) {

                alert(
                    "Please select a recipient."
                );

                return;

            }

            if (!message?.value.trim()) {

                alert(
                    "Please enter a message."
                );

                return;

            }

            const formData =
                new FormData(
                    newMessageForm
                );

            const submitButton =
                newMessageForm.querySelector(
                    'button[type="submit"]'
                );

            if (submitButton) {

                submitButton.disabled =
                    true;

            }

            try {

                const response =
                    await fetch(
                        "/communication",
                        {
                            method: "POST",
                            body: formData,

                            headers: {

                                "X-Requested-With":
                                    "XMLHttpRequest",

                                "Accept":
                                    "application/json"

                            }

                        }
                    );

                if (!response.ok) {

                    throw new Error(
                        "HTTP " +
                        response.status
                    );

                }

                const data =
                    await response.json();

                if (!data.success) {

                    alert(
                        data.message ||
                        "Unable to send message."
                    );

                    return;

                }

                if (data.message_data) {

                    messages.push(
                        data.message_data
                    );

                }

                messages.sort(
                    function (a, b) {

                        return (
                            parseDate(a.created) -
                            parseDate(b.created)
                        );

                    }
                );

                activePartnerId =
                    Number(
                        receiver.value
                    );

                newMessageForm.reset();

                if (newMessageCount) {

                    newMessageCount.textContent =
                        "0";

                }

                closeModal();

                renderConversations();

                openConversation(
                    activePartnerId
                );

                /* Scroll only inside chat */

                scrollChatToBottom(true);

            }

            catch (error) {

                console.error(
                    "New message error:",
                    error
                );

                alert(
                    "Unable to send the message. Please try again."
                );

            }

            finally {

                if (submitButton) {

                    submitButton.disabled =
                        false;

                }

            }

        }
    );


    /* =========================================================
       INITIAL LOAD
    ========================================================== */

    renderConversations();

    refreshIcons();


    /* =========================================================
       FINAL INITIALIZATION
       Make sure the message container owns scrolling.
    ========================================================== */

    if (messageArea) {

        messageArea.style.overflowY =
            "auto";

        messageArea.style.overflowX =
            "hidden";

    }

});