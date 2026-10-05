// Navigation Toggle for Mobile
const hamburger = document.querySelector('.hamburger');
const navLinks = document.querySelector('.nav-links');

if (hamburger) {
    hamburger.addEventListener('click', () => {
        navLinks.classList.toggle('active');
    });
}

// Close menu when clicking outside
document.addEventListener('click', (e) => {
    if (hamburger && navLinks && !hamburger.contains(e.target) && !navLinks.contains(e.target)) {
        navLinks.classList.remove('active');
    }
});

// Tracking Logic
// Helper to format date
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
        year: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

async function trackPackage(manualId = null) {
    // Support both new hero input and potential other inputs
    const trackingInput = document.getElementById('trackingInputHero');
    const trackingId = manualId || (trackingInput ? trackingInput.value : '');

    const timelineContainer = document.getElementById('trackingResult');
    const timelineContent = document.getElementById('timelineContent');

    if (!trackingId) return notify.error('Please enter a tracking ID');

    // Button state handling - trying to find the button relative to input or by class
    let startBtn = document.querySelector('.input-group-pill .btn-primary');
    let originalText = 'Track';

    if (startBtn) {
        originalText = startBtn.textContent;
        startBtn.textContent = '...';
        startBtn.disabled = true;
    }

    // Hide previous results
    timelineContainer.style.display = 'none';
    timelineContent.innerHTML = '';

    try {
        const response = await fetch(`/api/track/${trackingId}`);
        const data = await response.json();

        if (response.ok) {
            timelineContainer.style.display = 'block';

            // Scroll to results
            timelineContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

            const history = data.history || [{
                status: data.status,
                location: data.location,
                timestamp: data.created_at
            }];

            history.forEach((event, index) => {
                const isLast = index === history.length - 1;
                const item = document.createElement('div');
                item.className = `timeline-item ${isLast ? 'active' : ''}`;

                item.innerHTML = `
                    <div class="timeline-dot"></div>
                    <div class="timeline-content">
                        <h4>${event.status}</h4>
                        <div class="timeline-date">${formatDate(event.timestamp)}</div>
                        <div class="timeline-location">${event.location}</div>
                    </div>
                `;
                timelineContent.appendChild(item);
            });
        } else {
            notify.error(data.error || 'Package not found.');
        }
    } catch (error) {
        console.error('Error:', error);
        notify.error('Failed to connect to the server.');
    } finally {
        if (startBtn) {
            startBtn.textContent = originalText;
            startBtn.disabled = false;
        }
    }
}

// Attach Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Hero Button
    const heroBtn = document.querySelector('.input-group-pill .btn-primary');
    if (heroBtn) {
        heroBtn.onclick = () => trackPackage(); // Override inline if needed or just handle here (Inline removed/updated below)
    }

    // Hero Input Enter Key
    const heroInput = document.getElementById('trackingInputHero');
    if (heroInput) {
        heroInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') trackPackage();
        });
    }
});

// Contact Form Logic
const contactForm = document.getElementById('contactForm');
if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const subject = document.getElementById('subject').value;
        const message = document.getElementById('message').value;

        const submitBtn = contactForm.querySelector('button');
        submitBtn.textContent = 'Sending...';
        submitBtn.disabled = true;

        try {
            const response = await fetch('/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, email, subject, message })
            });

            if (response.ok) {
                notify.success('Message sent successfully!');
                contactForm.reset();
            } else {
                notify.error('Failed to send message. Please try again.');
            }
        } catch (error) {
            console.error('Error:', error);
            notify.error('An error occurred. Please try again later.');
        } finally {
            submitBtn.textContent = 'Send Message';
            submitBtn.disabled = false;
        }
    });
}
