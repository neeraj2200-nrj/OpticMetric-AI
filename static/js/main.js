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
});
