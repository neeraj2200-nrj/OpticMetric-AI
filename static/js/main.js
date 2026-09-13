// OpticMetric AI Clinical Workstation Common Javascript Utilities

document.addEventListener("DOMContentLoaded", function() {
    console.log("OpticMetric AI Clinical Workstation Initialized.");
    
    // Add active class transitions to cards
    const cards = document.querySelectorAll(".clinical-card");
    cards.forEach(card => {
        card.addEventListener("mouseenter", () => {
            card.style.transform = "translateY(-2px)";
            card.style.boxShadow = "0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02)";
            card.style.transition = "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease";
        });
        card.addEventListener("mouseleave", () => {
            card.style.transform = "none";
            card.style.boxShadow = "none";
        });
    });

    // Check saved sidebar collapse state from localStorage for desktop view
    if (localStorage.getItem("opticmetric_sidebar_collapsed") === "true") {
        document.body.classList.add("sidebar-collapsed");
    }

    const sidebarLogoToggle = document.getElementById("sidebarLogoToggle");
    const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
    const sidebar = document.querySelector(".sidebar");
    const sidebarOverlay = document.getElementById("sidebarOverlay");
    const navLinks = document.querySelectorAll(".sidebar-nav-link");

    // Close Mobile Drawer
    function closeMobileSidebar() {
        if (sidebar) sidebar.classList.remove("sidebar-open");
        document.body.classList.remove("sidebar-active");
        if (sidebarToggleBtn) {
            sidebarToggleBtn.setAttribute("aria-expanded", "false");
            sidebarToggleBtn.setAttribute("aria-label", "Open menu");
        }
    }

    // Open Mobile Drawer
    function openMobileSidebar() {
        if (sidebar) sidebar.classList.add("sidebar-open");
        document.body.classList.add("sidebar-active");
        if (sidebarToggleBtn) {
            sidebarToggleBtn.setAttribute("aria-expanded", "true");
            sidebarToggleBtn.setAttribute("aria-label", "Close menu");
        }
    }

    // Toggle Mobile Drawer
    function toggleMobileSidebar() {
        if (sidebar && sidebar.classList.contains("sidebar-open")) {
            closeMobileSidebar();
        } else {
            openMobileSidebar();
        }
    }

    // Logo Click Handler (Desktop collapse toggle OR Mobile drawer close)
    if (sidebarLogoToggle) {
        function handleLogoClick(e) {
            e.preventDefault();
            if (window.innerWidth >= 992) {
                // Desktop: toggle collapsed state
                document.body.classList.toggle("sidebar-collapsed");
                const isCollapsed = document.body.classList.contains("sidebar-collapsed");
                localStorage.setItem("opticmetric_sidebar_collapsed", isCollapsed ? "true" : "false");
                
                // Trigger window resize event for Chart.js auto-reflow
                setTimeout(() => {
                    window.dispatchEvent(new Event('resize'));
                }, 310);
            } else {
                // Mobile: close drawer if open
                closeMobileSidebar();
            }
        }

        sidebarLogoToggle.addEventListener("click", handleLogoClick);
        sidebarLogoToggle.addEventListener("keydown", function(e) {
            if (e.key === "Enter" || e.key === " ") {
                handleLogoClick(e);
            }
        });
    }

    // Mobile Hamburger Button click
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener("click", function(e) {
            e.stopPropagation();
            toggleMobileSidebar();
        });
    }

    // Overlay backdrop click -> Close mobile drawer
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener("click", function() {
            closeMobileSidebar();
        });
    }

    // Navigation item click -> Close mobile drawer after navigating
    navLinks.forEach(link => {
        link.addEventListener("click", function() {
            if (window.innerWidth < 992) {
                closeMobileSidebar();
            }
        });
    });

    // Window resize handler: clean up state on window size transition
    window.addEventListener("resize", function() {
        if (window.innerWidth >= 992) {
            closeMobileSidebar();
        }
    });
});

