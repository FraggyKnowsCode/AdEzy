// ========================================
// AdEzy - Main JavaScript (Client-Side Logic)
// ========================================
// 
// Real-time Updates (AJAX Polling):
// - Notifications: Auto-refresh every 5 seconds
// - Messages: Auto-refresh every 5 seconds
// - Balance: Auto-refresh every 10 seconds
// - Orders (Dashboard): Auto-refresh every 10 seconds
// - Gigs (Home): Auto-refresh every 10 seconds
// - Order Messages: Auto-refresh every 3 seconds
//
// Toast notifications appear for new messages and notifications
// ========================================

// Global variables
let allGigs = [];
let currentUser = null;
let lastScrollY = window.scrollY;
let displayedGigsCount = 0;
const GIGS_PER_PAGE = 15;

// Helper: Check if tab is hidden/inactive to pause background polling
function isPageHidden() {
    return document.hidden || document.visibilityState === 'hidden';
}

// ========================================
// Show More Gigs Function
// ========================================
function showMoreGigs() {
    renderGigs(allGigs, true);
}

// ========================================
// Initialize App on Page Load
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('AdEzy initialized');
    
    // Load initial data
    loadGigsForSearch(); // Always load gigs for search functionality
    loadUserBalance();
    loadSellerEarnings();
    updateCartBadge();
    
    // Auto-refresh balance every 30 seconds when active
    setInterval(() => {
        if (!isPageHidden()) {
            loadUserBalance();
        }
    }, 30000);
    
    // Load seller's gigs if on dashboard
    if (document.getElementById('my-gigs-container')) {
        loadMyGigs();
    }
    
    // Initial load for messages dropdown (unified polling managed by ensureChatPollerStarted)
    if (document.getElementById('conversations-list')) {
        loadChatConversations(true);
    }
    
    // Load notifications
    if (document.getElementById('notifications-list')) {
        loadNotifications();
        // Auto-refresh notifications every 20 seconds when active
        setInterval(() => {
            if (!isPageHidden()) {
                loadNotifications();
            }
        }, 20000);
    }
    
    // Set up event listeners
    setupSearchListener();
    setupDashboardTabs();
    setupScrollBehavior();
    
    // Check if on dashboard page
    if (document.querySelector('#buyer-section')) {
        loadBuyerOrders();
        loadSellerOrders();
        // Auto-refresh orders every 25 seconds when tab active
        setInterval(() => {
            if (!isPageHidden()) {
                loadBuyerOrders();
                loadSellerOrders();
            }
        }, 25000);
    }
    
    // Handle anchor scroll on page load
    if (window.location.hash) {
        setTimeout(() => {
            const element = document.querySelector(window.location.hash);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 500);
    }
});

// Setup scroll behavior for sticky navbar
function setupScrollBehavior() {
    let scrollTimeout;
    
    window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;
        
        // Add/remove class based on scroll direction
        if (currentScrollY > 100) {
            if (currentScrollY > lastScrollY) {
                // Scrolling down
                document.body.classList.add('scrolled-down');
            } else {
                // Scrolling up
                document.body.classList.remove('scrolled-down');
            }
        } else {
            // Near top
            document.body.classList.remove('scrolled-down');
        }
        
        lastScrollY = currentScrollY;
    });
}

// Filter by category and scroll to popular services
function filterByCategory(categoryName) {
    // Update URL with category parameter
    window.location.href = `/?category=${encodeURIComponent(categoryName)}#popular-services`;
}

// Make filterByCategory available globally
window.filterByCategory = filterByCategory;


// ========================================
// Dynamic Gig Rendering (DOM Manipulation)
// ========================================
// Load gigs for search (works on all pages)
async function loadGigsForSearch() {
    try {
        // Check for URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const category = urlParams.get('category');
        const filter = urlParams.get('filter');
        
        // Build API URL with parameters
        let apiUrl = '/api/gigs/';
        const params = [];
        if (category) params.push(`category=${encodeURIComponent(category)}`);
        if (filter) params.push(`filter=${encodeURIComponent(filter)}`);
        if (params.length > 0) {
            apiUrl += '?' + params.join('&');
        }
        
        // Reset pagination
        displayedGigsCount = 0;
        
        // Fetch gigs from Django backend
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            throw new Error('Failed to fetch gigs');
        }
        
        const data = await response.json();
        allGigs = data.gigs;
        console.log(`Loaded ${allGigs.length} gigs for search`);
        
        // If we're on home page, render the gigs
        const container = document.querySelector('#gig-container');
        if (container) {
            renderGigs(allGigs);
            // Update search results info if category/filter is active
            updateFilterInfo(category, filter, allGigs.length);
        }
    } catch (error) {
        console.error('Error loading gigs for search:', error);
        allGigs = [];
    }
}

async function loadGigs() {
    const container = document.querySelector('#gig-container');
    
    if (!container) return;
    
    // Show loading state
    container.innerHTML = '<div class="loading">Loading gigs...</div>';
    
    try {
        // Fetch gigs from Django backend
        const response = await fetch('/api/gigs/');
        
        if (!response.ok) {
            throw new Error('Failed to fetch gigs');
        }
        
        const data = await response.json();
        allGigs = data.gigs;
        
        // Render gigs
        renderGigs(allGigs);
        
    } catch (error) {
        console.error('Error loading gigs:', error);
        container.innerHTML = `
            <div class="empty-state">
                <h3><i class="fa-solid fa-triangle-exclamation"></i> Error Loading Gigs</h3>
                <p>Please try again later.</p>
            </div>
        `;
    }
}

function renderGigs(gigs, append = false) {
    const container = document.querySelector('#gig-container');
    const searchResultsInfo = document.getElementById('search-results-info');
    const searchResultsText = document.getElementById('search-results-text');
    const searchInput = document.querySelector('#search-input');
    const showMoreContainer = document.getElementById('show-more-container');
    const gigsCountInfo = document.getElementById('gigs-count-info');
    
    if (!container) {
        console.log('Gig container not found on this page');
        return;
    }
    
    console.log(`Rendering ${gigs.length} gigs (append: ${append})`);
    
    // Show/hide search results info
    if (searchResultsInfo && searchInput && searchInput.value.trim() !== '') {
        const searchTerm = searchInput.value.trim();
        if (searchResultsText) {
            searchResultsText.textContent = `Found ${gigs.length} gig${gigs.length !== 1 ? 's' : ''} matching "${searchTerm}"`;
        }
        searchResultsInfo.style.display = 'block';
    } else if (searchResultsInfo) {
        searchResultsInfo.style.display = 'none';
    }
    
    // Clear container if not appending
    if (!append) {
        container.innerHTML = '';
        displayedGigsCount = 0;
    }
    
    // Check if empty
    if (gigs.length === 0) {
        const searchTerm = searchInput ? searchInput.value.trim() : '';
        container.innerHTML = `
            <div class="empty-state">
                <h3>No gigs found</h3>
                <p>${searchTerm ? `No results for "${searchTerm}". Try different keywords.` : 'Check back later for new services.'}</p>
            </div>
        `;
        if (showMoreContainer) showMoreContainer.style.display = 'none';
        return;
    }
    
    // Determine how many gigs to show
    const startIndex = append ? displayedGigsCount : 0;
    const endIndex = Math.min(startIndex + GIGS_PER_PAGE, gigs.length);
    const gigsToShow = gigs.slice(startIndex, endIndex);
    
    // Create gig cards dynamically
    gigsToShow.forEach((gig, index) => {
        // Create card container
        const card = document.createElement('div');
        card.className = 'gig-card';
        card.style.animationDelay = `${index * 0.1}s`;
        
        // Create image element
        const image = document.createElement('img');
        image.className = 'gig-card-image';
        image.src = gig.image_url;
        image.alt = gig.title;
        image.loading = 'lazy';
        
        // Create content container
        const content = document.createElement('div');
        content.className = 'gig-card-content';
        
        // Create title
        const title = document.createElement('h3');
        title.className = 'gig-card-title';
        title.textContent = gig.title;
        
        // Create seller name
        const seller = document.createElement('p');
        seller.className = 'gig-card-seller';
        seller.textContent = `by ${gig.seller_name}`;
        
        // Create rating display (if rating exists)
        if (gig.rating && gig.rating > 0) {
            const ratingDiv = document.createElement('div');
            ratingDiv.className = 'gig-card-rating';
            ratingDiv.innerHTML = `
                <span class="rating-stars"><i class="fa-solid fa-star text-gold"></i> ${gig.rating.toFixed(1)}</span>
                <span class="rating-reviews">(${gig.total_reviews} reviews)</span>
            `;
            content.appendChild(ratingDiv);
        }
        
        // Create category badge
        const category = document.createElement('span');
        category.className = 'gig-card-category';
        category.textContent = gig.category;
        
        // Append to content
        content.appendChild(title);
        content.appendChild(seller);
        content.appendChild(category);
        
        // Create footer
        const footer = document.createElement('div');
        footer.className = 'gig-card-footer';
        
        // Create price
        const price = document.createElement('div');
        price.className = 'gig-card-price';
        price.textContent = `${gig.price} ৳`;
        
        // Create actions group with Add to Cart + View Details
        const actionsGroup = document.createElement('div');
        actionsGroup.className = 'gig-actions-group';
        actionsGroup.style.display = 'flex';
        actionsGroup.style.gap = '8px';
        actionsGroup.style.alignItems = 'center';

        const cartButton = document.createElement('button');
        cartButton.className = 'btn-card-cart';
        cartButton.title = 'Add Service to Cart';
        cartButton.innerHTML = '<i class="fa-solid fa-cart-plus"></i>';
        cartButton.onclick = (e) => {
            e.stopPropagation();
            addServiceToCart(gig.id, gig.title, gig.price, gig.seller_name, gig.delivery_time);
        };

        const orderButton = document.createElement('button');
        orderButton.className = 'btn-order';
        orderButton.textContent = 'View Details';
        orderButton.onclick = (e) => {
            e.stopPropagation();
            window.location.href = '/gig/' + gig.id + '/';
        };

        actionsGroup.appendChild(cartButton);
        actionsGroup.appendChild(orderButton);

        // Append to footer
        footer.appendChild(price);
        footer.appendChild(actionsGroup);
        
        // Make card clickable
        card.style.cursor = 'pointer';
        card.onclick = () => {
            window.location.href = '/gig/' + gig.id + '/';
        };
        
        // Assemble card
        card.appendChild(image);
        card.appendChild(content);
        card.appendChild(footer);
        
        // Add to container
        container.appendChild(card);
    });
    
    // Update displayed count
    displayedGigsCount = endIndex;
    
    // Show/hide "Show More" button
    if (showMoreContainer) {
        if (displayedGigsCount < gigs.length) {
            showMoreContainer.style.display = 'block';
            if (gigsCountInfo) {
                gigsCountInfo.textContent = `Showing ${displayedGigsCount} of ${gigs.length} gigs`;
            }
        } else {
            showMoreContainer.style.display = 'none';
        }
    }
}

// ========================================
// Search Functionality (Client-Side)
// ========================================
function setupSearchListener() {
    const searchInput = document.querySelector('#search-input');
    const suggestionsContainer = document.getElementById('search-suggestions');
    
    if (!searchInput) return;
    
    // Function to show search suggestions
    const showSuggestions = () => {
        const searchTerm = searchInput.value.toLowerCase().trim();
        
        if (!suggestionsContainer) return;
        
        // Hide suggestions if search is empty
        if (searchTerm === '' || searchTerm.length < 2) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        // Filter gigs based on search term
        const filteredGigs = allGigs.filter(gig => {
            const title = (gig.title || '').toLowerCase();
            const description = (gig.description || '').toLowerCase();
            const category = (gig.category || '').toLowerCase();
            const seller = (gig.seller_name || '').toLowerCase();
            
            return title.includes(searchTerm) ||
                   description.includes(searchTerm) ||
                   category.includes(searchTerm) ||
                   seller.includes(searchTerm);
        });
        
        // Show suggestions
        if (filteredGigs.length > 0) {
            const maxSuggestions = 5;
            const suggestions = filteredGigs.slice(0, maxSuggestions);
            
            suggestionsContainer.innerHTML = suggestions.map(gig => `
                <div class="search-suggestion-item" onclick="selectGig(${gig.id})">
                    <img src="${gig.image_url}" alt="${gig.title}" class="search-suggestion-image">
                    <div class="search-suggestion-content">
                        <h4 class="search-suggestion-title">${gig.title}</h4>
                        <div class="search-suggestion-meta">
                            <span class="search-suggestion-category">${gig.category} • by ${gig.seller_name}</span>
                            <span class="search-suggestion-price">${gig.price} ৳</span>
                        </div>
                    </div>
                </div>
            `).join('');
            
            // Add footer if more results available
            if (filteredGigs.length > maxSuggestions) {
                suggestionsContainer.innerHTML += `
                    <div class="search-suggestions-footer">
                        +${filteredGigs.length - maxSuggestions} more results. Press Enter to view all.
                    </div>
                `;
            }
            
            suggestionsContainer.style.display = 'block';
        } else {
            suggestionsContainer.innerHTML = '<div class="search-suggestions-empty">No gigs found for "' + searchTerm + '"</div>';
            suggestionsContainer.style.display = 'block';
        }
    };
    
    // Function to perform full search
    const performSearch = () => {
        const searchTerm = searchInput.value.trim();
        
        // Hide suggestions
        if (suggestionsContainer) {
            suggestionsContainer.style.display = 'none';
        }
        
        // Reset pagination
        displayedGigsCount = 0;
        
        // Check if we're on the home page
        const container = document.querySelector('#gig-container');
        
        if (!container) {
            // If not on home page, redirect to home with search
            if (searchTerm) {
                window.location.href = `/?search=${encodeURIComponent(searchTerm)}`;
            } else {
                window.location.href = '/';
            }
            return;
        }
        
        // If search is empty, show all gigs
        if (searchTerm === '') {
            renderGigs(allGigs);
            return;
        }
        
        // Filter gigs based on search term (title, description, category, seller)
        const searchTermLower = searchTerm.toLowerCase();
        const filteredGigs = allGigs.filter(gig => {
            const title = (gig.title || '').toLowerCase();
            const description = (gig.description || '').toLowerCase();
            const category = (gig.category || '').toLowerCase();
            const seller = (gig.seller_name || '').toLowerCase();
            
            return title.includes(searchTermLower) ||
                   description.includes(searchTermLower) ||
                   category.includes(searchTermLower) ||
                   seller.includes(searchTermLower);
        });
        
        // Re-render with filtered results
        renderGigs(filteredGigs);
        
        // Scroll to results if found
        if (filteredGigs.length > 0) {
            container.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };
    
    // Show suggestions on input
    searchInput.addEventListener('input', () => {
        showSuggestions();
        // Also perform live filtering if on home page
        const container = document.querySelector('#gig-container');
        if (container) {
            const searchTerm = searchInput.value.trim();
            if (searchTerm === '') {
                renderGigs(allGigs);
            } else {
                const searchTermLower = searchTerm.toLowerCase();
                const filteredGigs = allGigs.filter(gig => {
                    const title = (gig.title || '').toLowerCase();
                    const description = (gig.description || '').toLowerCase();
                    const category = (gig.category || '').toLowerCase();
                    const seller = (gig.seller_name || '').toLowerCase();
                    
                    return title.includes(searchTermLower) ||
                           description.includes(searchTermLower) ||
                           category.includes(searchTermLower) ||
                           seller.includes(searchTermLower);
                });
                renderGigs(filteredGigs);
            }
        }
    });
    
    // Search on Enter key
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch();
        }
    });
    
    // Search icon click
    const searchIcon = document.getElementById('search-icon');
    if (searchIcon) {
        searchIcon.style.pointerEvents = 'auto';
        searchIcon.style.cursor = 'pointer';
        searchIcon.addEventListener('click', () => {
            performSearch();
        });
    }
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (suggestionsContainer && !searchInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            suggestionsContainer.style.display = 'none';
        }
    });
    
    // Show suggestions when focusing on input with existing text
    searchInput.addEventListener('focus', () => {
        if (searchInput.value.trim().length >= 2) {
            showSuggestions();
        }
    });
    
    // Check for search parameter in URL on page load
    const urlParams = new URLSearchParams(window.location.search);
    const searchParam = urlParams.get('search');
    if (searchParam) {
        searchInput.value = searchParam;
        // Trigger search after gigs are loaded
        setTimeout(performSearch, 500);
    }
}

// Function to select a gig from suggestions
function selectGig(gigId) {
    // Redirect to gig detail page
    window.location.href = '/gig/' + gigId + '/';
}

// ========================================
// Order Handling with Modal
// ========================================
async function handleOrder(gigId) {
    const modal = document.querySelector('#order-modal');
    const modalContent = document.querySelector('#modal-content');
    
    if (!modal || !modalContent) {
        alert('Order modal not found. Please refresh the page.');
        return;
    }
    
    // Show modal
    modal.classList.remove('hidden');
    modalContent.innerHTML = `
        <div class="order-confirm-dialog" style="text-align: center; padding: 48px 24px;">
            <div style="font-size: 2.5rem; color: var(--gold); margin-bottom: 16px;">
                <i class="fa-solid fa-spinner fa-spin"></i>
            </div>
            <h3 style="color: var(--text-primary); font-size: 1.2rem; font-weight: 600;">Loading Service Details...</h3>
        </div>
    `;
    
    try {
        // Fetch gig info and balance concurrently
        const [gigRes, balanceRes] = await Promise.all([
            fetch(`/api/gigs/${gigId}/`),
            fetch('/api/user/balance/')
        ]);

        // Check if user needs to log in
        if (balanceRes.status === 401 || balanceRes.redirected || balanceRes.url.includes('/login')) {
            modalContent.innerHTML = `
                <div class="order-confirm-dialog">
                    <div class="order-dialog-header">
                        <h3><i class="fa-solid fa-lock" style="color: var(--gold);"></i> Sign In Required</h3>
                        <button class="order-dialog-close" onclick="closeModal()" aria-label="Close"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                    <div style="text-align: center; padding: 24px 0;">
                        <div style="font-size: 3rem; color: var(--gold); margin-bottom: 14px;">
                            <i class="fa-solid fa-circle-user"></i>
                        </div>
                        <p style="color: var(--text-secondary); font-size: 1rem; line-height: 1.6; margin-bottom: 24px;">
                            Please log in or create an account to place an order.<br>
                            <strong style="color: var(--gold);">Every new user receives 5,000 ৳ welcome credits!</strong>
                        </p>
                        <div class="order-dialog-actions" style="justify-content: center; gap: 14px;">
                            <a href="/login/?next=/gig/${gigId}/" class="btn btn-primary" style="padding: 12px 28px;">
                                <i class="fa-solid fa-right-to-bracket"></i> Log In
                            </a>
                            <a href="/register/" class="btn btn-secondary" style="padding: 12px 28px;">
                                <i class="fa-solid fa-user-plus"></i> Sign Up (Free 5,000 ৳)
                            </a>
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        if (!gigRes.ok) {
            throw new Error('Service details could not be retrieved');
        }

        const gig = await gigRes.json();
        let balanceData = { balance: 5000.00 };
        if (balanceRes.ok) {
            balanceData = await balanceRes.json();
            updateBalanceDisplay(balanceData.balance);
        }

        const currentBalance = balanceData.balance;
        const gigPrice = parseFloat(gig.price);
        const hasEnough = currentBalance >= gigPrice;
        const remaining = currentBalance - gigPrice;

        modalContent.innerHTML = `
            <div class="order-confirm-dialog">
                <div class="order-dialog-header">
                    <h3>Confirm Your Order</h3>
                    <button class="order-dialog-close" onclick="closeModal()" aria-label="Close">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>

                <div class="order-gig-card">
                    <img src="${gig.image_url}" alt="${gig.title}" class="order-gig-thumb" onerror="this.src='/static/images/default-gig.jpg'">
                    <div class="order-gig-details">
                        <h4>${gig.title}</h4>
                        <p class="order-seller-name"><i class="fa-solid fa-user-check"></i> Seller: <strong>${gig.seller_name}</strong></p>
                        <span class="order-delivery-tag"><i class="fa-regular fa-clock"></i> ${gig.delivery_time} Days Delivery</span>
                    </div>
                </div>

                <div class="order-pricing-summary">
                    <div class="pricing-line">
                        <span>Service Cost:</span>
                        <strong style="color: var(--text-primary); font-size: 1.05rem;">${gigPrice.toFixed(2)} ৳</strong>
                    </div>
                    <div class="pricing-line">
                        <span>Your Current Balance:</span>
                        <span class="balance-now">${currentBalance.toFixed(2)} ৳</span>
                    </div>
                    <div class="pricing-divider"></div>
                    <div class="pricing-line total-line">
                        <span>Balance After Order:</span>
                        <strong class="${hasEnough ? 'balance-after' : 'balance-short'}">
                            ${remaining.toFixed(2)} ৳
                        </strong>
                    </div>
                </div>

                ${!hasEnough ? `
                    <div class="order-insufficient-alert">
                        <i class="fa-solid fa-circle-exclamation"></i>
                        <div>
                            <strong>Insufficient Balance:</strong> You need <strong>${(gigPrice - currentBalance).toFixed(2)} ৳</strong> more to place this order.
                        </div>
                    </div>
                    <div class="order-dialog-actions">
                        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                        <button class="btn btn-primary" onclick="closeModal(); if(window.showBalanceRequestModal) window.showBalanceRequestModal();">
                            <i class="fa-solid fa-wallet"></i> Request Balance
                        </button>
                    </div>
                ` : `
                    <div class="order-req-field">
                        <label for="order-requirements-input">
                            <i class="fa-solid fa-pen-to-square"></i> Order Instructions & Requirements (Optional):
                        </label>
                        <textarea id="order-requirements-input" placeholder="Provide any details, files, or guidelines for the seller..." rows="3"></textarea>
                    </div>
                    <div class="order-dialog-actions">
                        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                        <button class="btn btn-primary" id="confirm-order-btn" onclick="submitConfirmedOrder(${gig.id}, ${gigPrice})">
                            <i class="fa-solid fa-check"></i> Confirm & Place Order (${gigPrice.toFixed(2)} ৳)
                        </button>
                    </div>
                `}
            </div>
        `;
        
    } catch (error) {
        console.error('Error opening order dialog:', error);
        modalContent.innerHTML = `
            <div class="order-confirm-dialog">
                <div class="order-dialog-header">
                    <h3>Service Error</h3>
                    <button class="order-dialog-close" onclick="closeModal()"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div style="padding: 24px; text-align: center;">
                    <p style="color: var(--text-secondary); margin-bottom: 20px;">Could not load service details. Please try again.</p>
                    <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                </div>
            </div>
        `;
    }
}

async function submitConfirmedOrder(gigId, price) {
    const btn = document.getElementById('confirm-order-btn');
    const reqInput = document.getElementById('order-requirements-input');
    const requirements = reqInput ? reqInput.value.trim() : '';

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Processing Order...`;
    }

    try {
        const csrftoken = getCookie('csrftoken');
        const response = await fetch('/api/orders/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                gig_id: gigId,
                requirements: requirements
            })
        });

        const data = await response.json();
        const modalContent = document.querySelector('#modal-content');

        if (data.success) {
            updateBalanceDisplay(data.new_balance);

            modalContent.innerHTML = `
                <div class="order-success-dialog">
                    <div class="success-icon-wrap">
                        <i class="fa-solid fa-circle-check"></i>
                    </div>
                    <h3>Order Placed Successfully!</h3>
                    <p class="success-sub">
                        Order <strong>#${data.order_id}</strong> is confirmed. The seller has been notified and will begin working on your request.
                    </p>
                    
                    <div class="success-summary-box">
                        <div class="pricing-line">
                            <span>Amount Paid:</span>
                            <strong style="color: var(--gold); font-size: 1.1rem;">${price.toFixed(2)} ৳</strong>
                        </div>
                        <div class="pricing-line">
                            <span>Remaining Balance:</span>
                            <strong class="balance-after" style="font-size: 1.1rem;">${data.new_balance.toFixed(2)} ৳</strong>
                        </div>
                    </div>

                    <div class="success-dialog-actions">
                        <a href="/dashboard/" class="btn btn-primary">
                            <i class="fa-solid fa-gauge-high"></i> View in Dashboard
                        </a>
                        <button class="btn btn-secondary" onclick="closeModal()">
                            Continue Shopping
                        </button>
                    </div>
                </div>
            `;
            if (typeof showToast === 'function') {
                showToast('Order placed successfully!', 'success');
            }
        } else {
            modalContent.innerHTML = `
                <div class="order-confirm-dialog">
                    <div class="order-dialog-header">
                        <h3>Order Failed</h3>
                        <button class="order-dialog-close" onclick="closeModal()"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                    <div style="padding: 24px; text-align: center;">
                        <div style="font-size: 2.5rem; color: #ef4444; margin-bottom: 12px;">
                            <i class="fa-solid fa-triangle-exclamation"></i>
                        </div>
                        <p style="color: var(--text-secondary); margin-bottom: 24px;">${data.error || 'Failed to process order.'}</p>
                        <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                    </div>
                </div>
            `;
        }
    } catch (err) {
        console.error('Order submission error:', err);
        const modalContent = document.querySelector('#modal-content');
        if (modalContent) {
            modalContent.innerHTML = `
                <div class="order-confirm-dialog">
                    <div class="order-dialog-header">
                        <h3>Order Error</h3>
                        <button class="order-dialog-close" onclick="closeModal()"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                    <div style="padding: 24px; text-align: center;">
                        <p style="color: var(--text-secondary); margin-bottom: 24px;">Network or server error while placing order. Please try again.</p>
                        <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                    </div>
                </div>
            `;
        }
    }
}

function closeModal() {
    const modal = document.querySelector('#order-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function handleModalBackdropClick(e) {
    if (e.target && e.target.id === 'order-modal') {
        closeModal();
    }
}

// Global User Dropdown toggle
function toggleUserDropdown(event) {
    if (event) event.stopPropagation();
    const menu = document.getElementById('user-dropdown-menu');
    if (menu) {
        const isShown = menu.classList.contains('show') || menu.style.display === 'flex';
        if (isShown) {
            menu.classList.remove('show');
            menu.style.display = 'none';
        } else {
            menu.classList.add('show');
            menu.style.display = 'flex';
        }
    }
}

// Global Search Overlay toggle
function toggleSearchOverlay() {
    const overlay = document.getElementById('search-overlay');
    if (overlay) {
        const isHidden = overlay.style.display === 'none' || overlay.style.display === '';
        overlay.style.display = isHidden ? 'flex' : 'none';
        if (isHidden) {
            const input = document.getElementById('search-input');
            if (input) input.focus();
        }
    }
}

// Close dropdowns on outside click
document.addEventListener('click', (e) => {
    const menu = document.getElementById('user-dropdown-menu');
    if (menu && !e.target.closest('.user-menu-wrapper')) {
        menu.classList.remove('show');
        menu.style.display = 'none';
    }
});


// ========================================
// User Balance Management
// ========================================
async function loadUserBalance() {
    try {
        const response = await fetch('/api/user/balance/');
        
        if (response.ok) {
            const data = await response.json();
            updateBalanceDisplay(data.balance);
            if (data.earnings !== undefined) {
                updateEarningsDisplay(data.earnings);
            }
        }
    } catch (error) {
        console.error('Error loading balance:', error);
    }
}

function updateBalanceDisplay(balance) {
    if (typeof balance !== 'number') {
        balance = parseFloat(balance) || 0;
    }
    const formatted = balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    
    const balanceElement = document.querySelector('#user-balance');
    const balanceDropdown = document.querySelector('#user-balance-dropdown');
    const balanceHeader = document.querySelector('#user-balance-header');
    
    if (balanceElement) {
        balanceElement.textContent = formatted;
    }
    if (balanceDropdown) {
        balanceDropdown.textContent = formatted;
    }
    if (balanceHeader) {
        balanceHeader.textContent = formatted;
    }
}

function updateEarningsDisplay(earnings) {
    if (typeof earnings !== 'number') {
        earnings = parseFloat(earnings) || 0;
    }
    const formatted = earnings.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    
    const earningsElements = document.querySelectorAll('#user-earnings, #user-earnings-header, #header-user-earnings');
    earningsElements.forEach(el => {
        el.textContent = formatted;
    });
}

// ========================================
// Dashboard Tab Switching
// ========================================
function setupDashboardTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    if (tabButtons.length === 0) return;
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetSection = button.getAttribute('data-target');
            
            // Remove active class from all buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            button.classList.add('active');
            
            // Hide all sections
            const sections = document.querySelectorAll('.dashboard-section');
            sections.forEach(section => {
                section.classList.remove('active');
            });
            
            // Show target section
            const target = document.querySelector(`#${targetSection}`);
            if (target) {
                target.classList.add('active');
            }
        });
    });
    
    // Setup filter tabs on home page
    const filterButtons = document.querySelectorAll('.tab-filter');
    if (filterButtons.length > 0) {
        filterButtons.forEach(button => {
            button.addEventListener('click', async () => {
                const filter = button.getAttribute('data-filter');
                
                // Remove active class from all buttons
                filterButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                button.classList.add('active');
                
                // Load gigs with filter
                await loadGigsWithFilter(filter);
            });
        });
    }
}

// Helper function to update filter info display
function updateFilterInfo(category, filter, count) {
    const searchResultsInfo = document.getElementById('search-results-info');
    const searchResultsText = document.getElementById('search-results-text');
    
    if (!searchResultsInfo || !searchResultsText) return;
    
    let message = '';
    if (category) {
        message = `Showing ${count} gig${count !== 1 ? 's' : ''} in "${category}"`;
    } else if (filter === 'top-rated') {
        message = `Showing ${count} top-rated gig${count !== 1 ? 's' : ''}`;
    } else if (filter === 'new') {
        message = `Showing ${count} new gig${count !== 1 ? 's' : ''}`;
    }
    
    if (message) {
        searchResultsText.textContent = message;
        searchResultsInfo.style.display = 'block';
    } else {
        searchResultsInfo.style.display = 'none';
    }
}

// Load gigs with filter
async function loadGigsWithFilter(filter) {
    const container = document.querySelector('#gig-container');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading gigs...</div>';
    
    // Reset pagination
    displayedGigsCount = 0;
    
    try {
        const apiUrl = filter === 'all' ? '/api/gigs/' : `/api/gigs/?filter=${filter}`;
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            throw new Error('Failed to fetch gigs');
        }
        
        const data = await response.json();
        allGigs = data.gigs;
        renderGigs(allGigs);
        updateFilterInfo(null, filter !== 'all' ? filter : null, allGigs.length);
    } catch (error) {
        console.error('Error loading gigs:', error);
        container.innerHTML = `
            <div class="empty-state">
                <h3><i class="fa-solid fa-triangle-exclamation"></i> Error Loading Gigs</h3>
                <p>Please try again later.</p>
            </div>
        `;
    }
}

// ========================================
// Load Buyer Orders
// ========================================
async function loadBuyerOrders() {
    const container = document.querySelector('#buyer-orders-container');
    
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading your orders...</div>';
    
    try {
        const response = await fetch('/api/orders/buyer/');
        
        if (!response.ok) {
            throw new Error('Failed to fetch orders');
        }
        
        const data = await response.json();
        
        if (data.orders.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No Orders Yet</h3>
                    <p>Browse gigs and place your first order!</p>
                </div>
            `;
            return;
        }
        
        // Render orders
        container.innerHTML = '';
        data.orders.forEach(order => {
            const orderCard = document.createElement('div');
            orderCard.className = 'glass-panel mb-20';
            orderCard.innerHTML = `
                <h4>${order.gig_title}</h4>
                <p>Seller: ${order.seller_name}</p>
                <p>Price: ${order.price} ৳</p>
                <p>Status: <span class="badge-${order.status}">${order.status}</span></p>
                <p>Ordered: ${new Date(order.created_at).toLocaleDateString()}</p>
                <a href="/order/${order.id}/" class="btn btn-primary" style="margin-top: 10px; display: inline-block;">View Details & Messages</a>
            `;
            container.appendChild(orderCard);
        });
        
    } catch (error) {
        console.error('Error loading buyer orders:', error);
        container.innerHTML = '<div class="empty-state"><h3>Error loading orders</h3></div>';
    }
}

// ========================================
// Load Seller Orders
// ========================================
async function loadSellerOrders() {
    const container = document.querySelector('#seller-orders-container');
    
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading your sales...</div>';
    
    try {
        const response = await fetch('/api/orders/seller/');
        
        if (!response.ok) {
            throw new Error('Failed to fetch orders');
        }
        
        const data = await response.json();
        
        if (data.orders.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No Sales Yet</h3>
                    <p>Create gigs to start selling!</p>
                </div>
            `;
            return;
        }
        
        // Render orders
        container.innerHTML = '';
        data.orders.forEach(order => {
            const orderCard = document.createElement('div');
            orderCard.className = 'glass-panel mb-20';
            orderCard.innerHTML = `
                <h4>${order.gig_title}</h4>
                <p>Buyer: ${order.buyer_name}</p>
                <p>Price: ${order.price} ৳</p>
                <p>Status: <span class="badge-${order.status}">${order.status}</span></p>
                <p>Requirements: ${order.requirements || 'None'}</p>
                <p>Ordered: ${new Date(order.created_at).toLocaleDateString()}</p>
                <a href="/order/${order.id}/" class="btn btn-primary" style="margin-top: 10px; display: inline-block;">View Details & Messages</a>
            `;
            container.appendChild(orderCard);
        });
        
    } catch (error) {
        console.error('Error loading seller orders:', error);
        container.innerHTML = '<div class="empty-state"><h3>Error loading sales</h3></div>';
    }
}

// ========================================
// Utility Functions
// ========================================

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ========================================
// Seller Earnings
// ========================================
async function loadSellerEarnings() {
    try {
        const response = await fetch('/api/seller/earnings/');
        
        if (response.ok) {
            const data = await response.json();
            
            // Update total / available earnings in profile dropdown
            const earningsVal = data.available_earnings !== undefined ? data.available_earnings : data.total_earnings;
            updateEarningsDisplay(earningsVal);
        }
    } catch (error) {
        console.error('Error loading earnings:', error);
    }
}

async function showEarningsModal(event) {
    event.preventDefault();
    
    const modal = document.querySelector('#earnings-modal');
    modal.classList.remove('hidden');
    
    try {
        const response = await fetch('/api/seller/earnings/');
        const data = await response.json();
        
        // Update summary
        document.querySelector('#total-earnings').textContent = data.total_earnings.toFixed(2) + ' ৳';
        document.querySelector('#total-orders').textContent = data.total_orders;
        
        // Render earnings by gig
        const byGigContainer = document.querySelector('#earnings-by-gig');
        if (data.earnings_by_gig.length === 0) {
            byGigContainer.innerHTML = '<p style="text-align: center; color: #64748b; padding: 20px;">No earnings yet</p>';
        } else {
            byGigContainer.innerHTML = data.earnings_by_gig.map(item => `
                <div class="earnings-item">
                    <div class="earnings-item-info">
                        <div class="earnings-item-title">${item.gig_title}</div>
                        <div class="earnings-item-details">${item.orders_count} orders completed</div>
                    </div>
                    <div class="earnings-item-amount">${item.total_earned.toFixed(2)} ৳</div>
                </div>
            `).join('');
        }
        
        // Render recent earnings
        const recentContainer = document.querySelector('#recent-earnings');
        if (data.recent_earnings.length === 0) {
            recentContainer.innerHTML = '<p style="text-align: center; color: #64748b; padding: 20px;">No recent earnings</p>';
        } else {
            recentContainer.innerHTML = data.recent_earnings.map(item => `
                <div class="earnings-item">
                    <div class="earnings-item-info">
                        <div class="earnings-item-title">${item.gig_title}</div>
                        <div class="earnings-item-details">Order #${item.order_id} • ${item.buyer} • ${item.completed_at}</div>
                    </div>
                    <div class="earnings-item-amount">+${item.amount.toFixed(2)} ৳</div>
                </div>
            `).join('');
        }
        
    } catch (error) {
        console.error('Error loading earnings:', error);
    }
}

function closeEarningsModal() {
    document.querySelector('#earnings-modal').classList.add('hidden');
}

// Load seller's gigs
async function loadMyGigs() {
    const container = document.getElementById('my-gigs-container');
    
    try {
        const response = await fetch('/api/my-gigs/');
        const data = await response.json();
        
        if (data.gigs && data.gigs.length > 0) {
            container.innerHTML = `
                <div class="gigs-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px;">
                    ${data.gigs.map(gig => `
                        <div class="gig-card" style="background: #161d2d; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3); transition: transform 0.3s;">
                            <img src="${gig.image_url}" alt="${gig.title}" style="width: 100%; height: 180px; object-fit: cover;">
                            <div style="padding: 15px;">
                                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                                    <span style="display: inline-block; padding: 4px 10px; background: ${gig.status === 'active' ? '#10b981' : '#6b7280'}; color: white; border-radius: 12px; font-size: 0.8rem; text-transform: capitalize;">
                                        ${gig.status}
                                    </span>
                                    <span style="color: #94a3b8; font-size: 0.85rem;">${gig.created_at}</span>
                                </div>
                                <h3 style="font-size: 1.05rem; margin: 10px 0; color: #ffffff; font-weight: 600;">${gig.title}</h3>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255, 255, 255, 0.08);">
                                    <div>
                                        <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 4px;">${gig.category}</p>
                                        <p style="color: var(--gold); font-weight: bold; font-size: 1.1rem;">${gig.price} ৳</p>
                                    </div>
                                    <div style="text-align: right;">
                                        <p style="color: #94a3b8; font-size: 0.85rem;">
                                            <i class="fas fa-clock"></i> ${gig.delivery_time} days
                                        </p>
                                    </div>
                                </div>
                                <div style="display: flex; gap: 8px; margin-top: 14px;">
                                    <button onclick="window.location.href='/update-gig/${gig.id}/'" class="btn btn-secondary" style="flex: 1; padding: 8px; font-size: 0.9rem;">
                                        <i class="fas fa-edit"></i> Edit
                                    </button>
                                    <button onclick="viewGig(${gig.id})" class="btn btn-primary" style="flex: 1; padding: 8px; font-size: 0.9rem;">
                                        <i class="fas fa-eye"></i> View
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #64748b;">
                    <i class="fas fa-briefcase" style="font-size: 3rem; margin-bottom: 15px; opacity: 0.3;"></i>
                    <p style="font-size: 1.1rem; margin-bottom: 10px;">You haven't created any gigs yet</p>
                    <p style="font-size: 0.95rem;">Create your first gig to start selling your services!</p>
                    <a href="/create-gig/" class="btn btn-primary" style="margin-top: 20px; display: inline-block;">
                        <i class="fas fa-plus"></i> Create Your First Gig
                    </a>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading gigs:', error);
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #ef4444;">
                <p>Error loading gigs. Please try again later.</p>
            </div>
        `;
    }
}

// View gig details
function viewGig(gigId) {
    window.location.href = `/gig/${gigId}/`;
}

// Load conversations for messages dropdown
let currentMessageOrderId = null;
let previousUnreadMessages = 0;

async function loadConversations() {
    if (typeof loadChatConversations === 'function') {
        return loadChatConversations(true);
    }
}

// Open messages modal
async function openMessagesModal(orderId) {
    currentMessageOrderId = orderId;
    const modal = document.getElementById('messages-modal');
    modal.style.display = 'flex';
    
    await loadMessagesForOrder(orderId);
}

// Close messages modal
function closeMessagesModal() {
    const modal = document.getElementById('messages-modal');
    modal.style.display = 'none';
    currentMessageOrderId = null;
    
    // Reload conversations to update unread counts
    loadConversations();
}

// Load messages for a specific order
async function loadMessagesForOrder(orderId) {
    const container = document.getElementById('messages-container');
    const orderInfo = document.getElementById('messages-order-info');
    const title = document.getElementById('messages-modal-title');
    
    container.innerHTML = '<div class="loading" style="text-align: center; padding: 20px;">Loading messages...</div>';
    
    try {
        const response = await fetch(`/api/orders/${orderId}/messages/`);
        const data = await response.json();
        
        if (data.order_info) {
            title.textContent = data.order_info.gig_title;
            orderInfo.innerHTML = `
                <div class="order-info-left">
                    <h3>${data.order_info.gig_title}</h3>
                    <p><strong>With:</strong> ${data.order_info.other_user}</p>
                    <p><strong>Price:</strong> ${data.order_info.price} ৳</p>
                </div>
                <span class="order-status-badge status-${data.order_info.status}">${data.order_info.status.replace('_', ' ')}</span>
            `;
        }
        
        if (data.messages && data.messages.length > 0) {
            container.innerHTML = data.messages.map(msg => {
                const time = new Date(msg.created_at).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit'
                });
                return `
                    <div class="message-bubble ${msg.is_own ? 'own' : 'other'}">
                        <span class="message-sender">${msg.sender}</span>
                        <div class="message-content">${msg.message}</div>
                        <span class="message-time">${time}</span>
                    </div>
                `;
            }).join('');
            
            // Scroll to bottom
            container.scrollTop = container.scrollHeight;
        } else {
            container.innerHTML = '<div style="text-align: center; padding: 40px; color: #94a3b8;">No messages yet. Start the conversation!</div>';
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        container.innerHTML = '<div style="text-align: center; padding: 20px; color: #ef4444;">Error loading messages</div>';
    }
}

// Send message from modal
async function sendMessageFromModal() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message || !currentMessageOrderId) return;
    
    try {
        const response = await fetch(`/api/orders/${currentMessageOrderId}/send-message/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        if (data.success) {
            input.value = '';
            await loadMessagesForOrder(currentMessageOrderId);
        } else {
            alert('Error sending message: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Error sending message. Please try again.');
    }
}

// Load notifications
let previousNotificationCount = 0;

async function loadNotifications() {
    const container = document.getElementById('notifications-list');
    const badge = document.getElementById('notifications-badge');
    
    try {
        const response = await fetch('/api/notifications/');
        const data = await response.json();
        
        // Check for new notifications
        const currentCount = data.unread_count || 0;
        if (previousNotificationCount > 0 && currentCount > previousNotificationCount) {
            const newCount = currentCount - previousNotificationCount;
            if (typeof showToast === 'function') {
                showToast(`${newCount} new notification${newCount > 1 ? 's' : ''}!`, 'info');
            }
        }
        previousNotificationCount = currentCount;
        
        // Update badge
        if (data.unread_count > 0) {
            badge.textContent = data.unread_count;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
        
        if (data.notifications && data.notifications.length > 0) {
            container.innerHTML = data.notifications.map(notif => {
                const timeAgo = getTimeAgo(new Date(notif.created_at));
                const icon = getNotificationIcon(notif.type);
                const clickable = notif.order_id ? 'clickable' : '';
                const unread = !notif.is_read ? 'unread' : '';
                
                return `
                    <div class="notification-item ${clickable} ${unread}" 
                         ${notif.order_id ? `onclick="handleNotificationClick(${notif.id}, ${notif.order_id})"` : `onclick="markNotificationRead(${notif.id})"`}>
                        <div class="notification-icon">${icon}</div>
                        <div class="notification-content">
                            <div class="notification-title">${notif.title}</div>
                            <div class="notification-time">${timeAgo}</div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = `
                <div class="empty-conversations">
                    <i class="fas fa-bell-slash"></i>
                    <p>No notifications yet</p>
                    <p style="font-size: 0.85rem;">We'll notify you when something happens</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #ef4444;">Error loading notifications</div>';
    }
}

function getNotificationIcon(type) {
    const icons = {
        'order_placed': '<i class="fa-solid fa-box"></i>',
        'order_accepted': '<i class="fa-solid fa-check"></i>',
        'order_delivered': '<i class="fa-solid fa-truck"></i>',
        'order_completed': '<i class="fa-solid fa-circle-check"></i>',
        'order_cancelled': '<i class="fa-solid fa-xmark"></i>',
        'message_received': '<i class="fa-solid fa-comment-dots"></i>',
        'review_received': '<i class="fa-solid fa-star text-gold"></i>'
    };
    return icons[type] || '<i class="fa-solid fa-bullhorn"></i>';
}

// Handle notification click
async function handleNotificationClick(notificationId, orderId) {
    await markNotificationRead(notificationId);
    if (orderId) {
        openMessagesModal(orderId);
    }
}

// Mark notification as read
async function markNotificationRead(notificationId) {
    try {
        await fetch(`/api/notifications/${notificationId}/read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        loadNotifications();
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

// Mark all notifications as read
async function markAllNotificationsRead() {
    try {
        await fetch('/api/notifications/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        loadNotifications();
    } catch (error) {
        console.error('Error marking all notifications as read:', error);
    }
}

// Helper function to get time ago
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
    if (seconds < 604800) return Math.floor(seconds / 86400) + 'd ago';
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Export functions for global access
window.handleOrder = handleOrder;
window.closeModal = closeModal;
window.loadGigs = loadGigs;
window.loadBuyerOrders = loadBuyerOrders;
window.loadSellerOrders = loadSellerOrders;
window.showEarningsModal = showEarningsModal;
window.closeEarningsModal = closeEarningsModal;
window.loadMyGigs = loadMyGigs;
window.loadConversations = loadConversations;
window.openMessagesModal = openMessagesModal;
window.closeMessagesModal = closeMessagesModal;
window.sendMessageFromModal = sendMessageFromModal;
window.loadNotifications = loadNotifications;
window.markNotificationRead = markNotificationRead;
window.markAllNotificationsRead = markAllNotificationsRead;
window.handleNotificationClick = handleNotificationClick;

// Clear search function
function clearSearch() {
    const searchInput = document.querySelector('#search-input');
    const suggestionsContainer = document.getElementById('search-suggestions');
    if (searchInput) {
        searchInput.value = '';
        renderGigs(allGigs);
        searchInput.focus();
    }
    if (suggestionsContainer) {
        suggestionsContainer.style.display = 'none';
    }
}
window.clearSearch = clearSearch;
window.selectGig = selectGig;


// ========================================
// Balance Request Functions
// ========================================
async function showBalanceRequestModal(event) {
    if (event) event.preventDefault();
    
    const modal = document.getElementById('balance-request-modal');
    modal.classList.remove('hidden');
    
    // Reset form
    document.getElementById('balance-request-form').reset();
    
    // Reload current balance
    await loadUserBalance();
    
    // Load existing requests
    await loadBalanceRequests();
}

function closeBalanceRequestModal() {
    const modal = document.getElementById('balance-request-modal');
    modal.classList.add('hidden');
}

async function submitBalanceRequest(event) {
    event.preventDefault();
    
    const amount = document.getElementById('balance-amount').value;
    const note = document.getElementById('balance-note').value;
    
    try {
        const response = await fetch('/api/balance-request/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                amount: parseFloat(amount),
                note: note
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Balance request submitted successfully! Admin will review your request.');
            document.getElementById('balance-request-form').reset();
            await loadBalanceRequests();
            await loadUserBalance();
        } else {
            alert('Error: ' + (data.error || 'Failed to submit request'));
        }
    } catch (error) {
        console.error('Error submitting balance request:', error);
        alert('Failed to submit balance request. Please try again.');
    }
}

async function loadBalanceRequests() {
    const container = document.getElementById('balance-requests-list');
    
    try {
        const response = await fetch('/api/balance-requests/');
        const data = await response.json();
        
        // Reload balance to show any updates from approved requests
        await loadUserBalance();
        
        if (data.requests.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #94a3b8; padding: 20px;">No balance requests yet</p>';
            return;
        }
        
        container.innerHTML = data.requests.map(req => {
            const statusColor = req.status === 'approved' ? '#10b981' : 
                              req.status === 'rejected' ? '#ef4444' : '#f59e0b';
            const statusIcon = req.status === 'approved' ? '<i class="fa-solid fa-check"></i>' : 
                             req.status === 'rejected' ? '<i class="fa-solid fa-xmark"></i>' : '<i class="fa-solid fa-clock"></i>';
            
            return `
                <div style="padding: 16px; margin-bottom: 12px; background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; border-left: 4px solid ${statusColor};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="font-weight: 700; color: #ffffff; font-size: 1.15rem;">
                            ${req.amount} ৳
                        </div>
                        <div style="background: ${statusColor}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.82rem; font-weight: 700; display: inline-flex; align-items: center; gap: 5px;">
                            ${statusIcon} ${req.status.toUpperCase()}
                        </div>
                    </div>
                    ${req.note ? `<div style="color: #cbd5e1; font-size: 0.9rem; margin-bottom: 8px;">${req.note}</div>` : ''}
                    ${req.admin_note ? `<div style="color: #fbbf24; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); padding: 8px 12px; border-radius: 8px; font-size: 0.85rem; margin-bottom: 8px;">Admin: ${req.admin_note}</div>` : ''}
                    <div style="color: #94a3b8; font-size: 0.82rem;">
                        ${req.created_at}
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading balance requests:', error);
        container.innerHTML = '<p style="text-align: center; color: #ef4444;">Failed to load requests</p>';
    }
}

// Expose functions to window
window.showBalanceRequestModal = showBalanceRequestModal;
window.closeBalanceRequestModal = closeBalanceRequestModal;
window.submitBalanceRequest = submitBalanceRequest;
window.loadBalanceRequests = loadBalanceRequests;


// ========================================
// Cashout Request Functions
// ========================================
async function showCashoutModal(event) {
    if (event) event.preventDefault();
    
    const modal = document.getElementById('cashout-modal');
    modal.classList.remove('hidden');
    
    // Reset form
    document.getElementById('cashout-form').reset();
    
    // Load available earnings
    await loadAvailableEarnings();
    
    // Load existing requests
    await loadCashoutRequests();
}

function closeCashoutModal() {
    const modal = document.getElementById('cashout-modal');
    modal.classList.add('hidden');
}

async function loadAvailableEarnings() {
    try {
        const response = await fetch('/api/available-earnings/');
        const data = await response.json();
        
        document.getElementById('total-earnings-display').textContent = data.total_earnings.toFixed(2) + ' ৳';
        document.getElementById('cashed-out-display').textContent = data.total_cashed_out.toFixed(2) + ' ৳';
        document.getElementById('available-earnings-display').textContent = data.available_earnings.toFixed(2) + ' ৳';
        
        // Update max attribute on amount input
        const amountInput = document.getElementById('cashout-amount');
        amountInput.max = data.available_earnings;
        
    } catch (error) {
        console.error('Error loading available earnings:', error);
    }
}

async function submitCashoutRequest(event) {
    event.preventDefault();
    
    const amount = parseFloat(document.getElementById('cashout-amount').value);
    const paymentMethod = document.getElementById('payment-method').value;
    const paymentDetails = document.getElementById('payment-details').value;
    const note = document.getElementById('cashout-note').value;
    
    try {
        const response = await fetch('/api/cashout-request/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                amount: amount,
                payment_method: paymentMethod,
                payment_details: paymentDetails,
                note: note
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Cashout request submitted successfully! Admin will process your payment.');
            document.getElementById('cashout-form').reset();
            await loadAvailableEarnings();
            await loadCashoutRequests();
            await loadSellerEarnings(); // Refresh earnings display
        } else {
            alert('Error: ' + (data.error || 'Failed to submit request'));
        }
    } catch (error) {
        console.error('Error submitting cashout request:', error);
        alert('Failed to submit cashout request. Please try again.');
    }
}

async function loadCashoutRequests() {
    const container = document.getElementById('cashout-requests-list');
    
    try {
        const response = await fetch('/api/cashout-requests/');
        const data = await response.json();
        
        if (data.requests.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #94a3b8; padding: 20px;">No cashout requests yet</p>';
            return;
        }
        
        container.innerHTML = data.requests.map(req => {
            const statusColor = req.status === 'approved' ? '#10b981' : 
                              req.status === 'rejected' ? '#ef4444' : '#f59e0b';
            const statusIcon = req.status === 'approved' ? '<i class="fa-solid fa-check"></i>' : 
                             req.status === 'rejected' ? '<i class="fa-solid fa-xmark"></i>' : '<i class="fa-solid fa-clock"></i>';
            
            return `
                <div style="padding: 16px; margin-bottom: 12px; background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; border-left: 4px solid ${statusColor};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="font-weight: 700; color: #ffffff; font-size: 1.15rem;">
                            ${req.amount} ৳ <span style="font-size: 0.85rem; color: #94a3b8; font-weight: 500;">via ${req.payment_method}</span>
                        </div>
                        <div style="background: ${statusColor}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.82rem; font-weight: 700; display: inline-flex; align-items: center; gap: 5px;">
                            ${statusIcon} ${req.status.toUpperCase()}
                        </div>
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.9rem; margin-bottom: 6px;">
                        <i class="fa-solid fa-credit-card text-gold" style="font-size: 0.85rem; margin-right: 4px;"></i> ${req.payment_details}
                    </div>
                    ${req.note ? `<div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 8px;">Note: ${req.note}</div>` : ''}
                    ${req.admin_note ? `<div style="color: #fbbf24; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); padding: 8px 12px; border-radius: 8px; font-size: 0.85rem; margin-bottom: 8px;">Admin: ${req.admin_note}</div>` : ''}
                    <div style="color: #64748b; font-size: 0.82rem;">
                        ${req.created_at}
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading cashout requests:', error);
        container.innerHTML = '<p style="text-align: center; color: #ef4444;">Failed to load requests</p>';
    }
}

// Expose functions to window
window.showCashoutModal = showCashoutModal;
window.closeCashoutModal = closeCashoutModal;
window.submitCashoutRequest = submitCashoutRequest;
window.loadCashoutRequests = loadCashoutRequests;
window.loadAvailableEarnings = loadAvailableEarnings;


// ========================================
// Cashout History Functions
// ========================================
async function showCashoutHistoryModal(event) {
    if (event) event.preventDefault();
    
    const modal = document.getElementById('cashout-history-modal');
    modal.classList.remove('hidden');
    
    // Load earnings summary and history
    await loadCashoutHistory();
}

function closeCashoutHistoryModal() {
    const modal = document.getElementById('cashout-history-modal');
    modal.classList.add('hidden');
}

async function loadCashoutHistory() {
    try {
        // Load earnings summary
        const earningsResponse = await fetch('/api/available-earnings/');
        const earningsData = await earningsResponse.json();
        
        document.getElementById('history-total-earnings').textContent = earningsData.total_earnings.toFixed(2) + ' ৳';
        document.getElementById('history-cashed-out').textContent = earningsData.total_cashed_out.toFixed(2) + ' ৳';
        document.getElementById('history-available').textContent = earningsData.available_earnings.toFixed(2) + ' ৳';
        
        // Load approved cashout history
        const historyResponse = await fetch('/api/cashout-requests/');
        const historyData = await historyResponse.json();
        
        const container = document.getElementById('cashout-history-list');
        
        // Filter only approved requests
        const approvedRequests = historyData.requests.filter(req => req.status === 'approved');
        
        if (approvedRequests.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #94a3b8; padding: 20px;">No cashout history yet</p>';
            return;
        }
        
        container.innerHTML = approvedRequests.map(req => {
            return `
                <div style="padding: 16px; margin-bottom: 12px; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 12px; border-left: 4px solid #10b981;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-weight: 700; color: #ffffff; font-size: 1.2rem;">
                            ${req.amount} ৳
                        </div>
                        <div style="background: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.82rem; font-weight: 700; display: inline-flex; align-items: center; gap: 5px;">
                            <i class="fa-solid fa-check"></i> PAID
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 8px;">
                        <div>
                            <div style="color: #94a3b8; font-size: 0.82rem; margin-bottom: 2px;">Payment Method</div>
                            <div style="color: #f1f5f9; font-weight: 600;">${req.payment_method}</div>
                        </div>
                        <div>
                            <div style="color: #94a3b8; font-size: 0.82rem; margin-bottom: 2px;">Account</div>
                            <div style="color: #f1f5f9; font-weight: 600;">${req.payment_details}</div>
                        </div>
                    </div>
                    ${req.admin_note ? `<div style="color: #34d399; font-size: 0.88rem; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.2); padding: 8px 12px; border-radius: 6px; margin-bottom: 8px;">
                        <strong>Admin:</strong> ${req.admin_note}
                    </div>` : ''}
                    <div style="color: #64748b; font-size: 0.82rem;">
                        Processed on ${req.updated_at}
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading cashout history:', error);
        document.getElementById('cashout-history-list').innerHTML = '<p style="text-align: center; color: #ef4444;">Failed to load history</p>';
    }
}

// ========================================
// Show Toast Notification
// ========================================
function showToast(message, type = 'info') {
    // Remove existing toast if any
    const existingToast = document.getElementById('live-update-toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Create toast
    const toast = document.createElement('div');
    toast.id = 'live-update-toast';
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: ${type === 'success' ? 'var(--gold)' : 'var(--deep-blue)'};
        color: ${type === 'success' ? 'var(--deep-blue)' : 'white'};
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        font-weight: 600;
        animation: slideInUp 0.3s ease-out;
    `;
    toast.textContent = message;
    
    // Add CSS animation
    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            @keyframes slideInUp {
                from {
                    transform: translateY(100%);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(toast);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideInUp 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Expose functions to window
window.showCashoutHistoryModal = showCashoutHistoryModal;
window.closeCashoutHistoryModal = closeCashoutHistoryModal;
window.loadCashoutHistory = loadCashoutHistory;
window.showToast = showToast;

// ========================================
// Global Unified Cart System (Services & Products)
// ========================================
const CART_STORAGE_KEY = 'adezy_unified_cart_v1';

function getStoredCart() {
    try {
        const raw = localStorage.getItem(CART_STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch (e) {
        console.error('Error reading cart:', e);
        return [];
    }
}

function saveStoredCart(cart) {
    try {
        localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
        updateCartBadge();
    } catch (e) {
        console.error('Error saving cart:', e);
    }
}

function updateCartBadge() {
    const cart = getStoredCart();
    const count = cart.length;
    const badge = document.getElementById('cart-counter');
    const modalCount = document.getElementById('cart-modal-count');

    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline-block' : 'none';
    }
    if (modalCount) {
        modalCount.textContent = count;
    }
}

function toggleCartModal(forceOpen) {
    const modal = document.getElementById('cart-modal');
    if (!modal) return;

    if (forceOpen === true) {
        modal.style.display = 'flex';
        renderUnifiedCartUI();
        return;
    }

    const isVisible = modal.style.display === 'flex' || modal.style.display === 'block';
    if (isVisible) {
        modal.style.display = 'none';
    } else {
        modal.style.display = 'flex';
        renderUnifiedCartUI();
    }
}

function addServiceToCart(gigId, title, price, seller, deliveryTime) {
    const cart = getStoredCart();
    const exists = cart.find(item => item.type === 'service' && String(item.id) === String(gigId));
    if (exists) {
        showToast(`"${title}" is already in your cart!`, 'info');
        toggleCartModal(true);
        return;
    }

    cart.push({
        id: String(gigId),
        type: 'service',
        title: title || 'Service Gig',
        price: parseFloat(price) || 0,
        seller: seller || 'Freelancer',
        delivery_time: deliveryTime || 3
    });

    saveStoredCart(cart);
    showToast(`Added service "${title}" to your cart!`, 'success');
    toggleCartModal(true);
}

function addProductToCart(productId, title, price, category) {
    const cart = getStoredCart();
    const exists = cart.find(item => item.type === 'product' && String(item.id) === String(productId));
    if (exists) {
        showToast(`"${title}" is already in your cart!`, 'info');
        toggleCartModal(true);
        return;
    }

    cart.push({
        id: String(productId),
        type: 'product',
        title: title || 'Digital Product',
        price: parseFloat(price) || 0,
        category: category || 'Digital Product'
    });

    saveStoredCart(cart);
    showToast(`Added "${title}" to your cart!`, 'success');
    toggleCartModal(true);
}

function removeUnifiedCartItem(index) {
    const cart = getStoredCart();
    if (index >= 0 && index < cart.length) {
        const removed = cart.splice(index, 1)[0];
        saveStoredCart(cart);
        renderUnifiedCartUI();
        showToast(`Removed "${removed.title}" from cart`, 'info');
    }
}

function clearEntireCart() {
    saveStoredCart([]);
    renderUnifiedCartUI();
    showToast('Cart cleared', 'info');
}

function renderUnifiedCartUI() {
    const list = document.getElementById('cart-items-list');
    const totalEl = document.getElementById('cart-total-display');
    const checkoutBtn = document.getElementById('cart-checkout-btn');
    if (!list) return;

    const cart = getStoredCart();
    updateCartBadge();

    if (checkoutBtn) {
        checkoutBtn.style.display = 'inline-flex';
        checkoutBtn.disabled = cart.length === 0;
        checkoutBtn.innerHTML = '<i class="fa-solid fa-lock"></i> Checkout with Credits';
    }

    if (cart.length === 0) {
        list.innerHTML = `
            <div class="cart-empty-msg">
                <i class="fa-solid fa-basket-shopping"></i>
                <p>Your cart is empty.</p>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 6px;">Add digital products or services to checkout.</p>
            </div>
        `;
        if (totalEl) totalEl.textContent = '0.00 ৳';
        return;
    }

    let total = 0;
    let html = '<ul class="cart-items-ul">';
    cart.forEach((item, index) => {
        total += item.price;
        const isService = item.type === 'service';
        const typeBadge = isService
            ? `<span class="cart-badge-type service"><i class="fa-solid fa-briefcase"></i> Service</span>`
            : `<span class="cart-badge-type product"><i class="fa-solid fa-file-arrow-down"></i> Digital</span>`;
        
        const subInfo = isService 
            ? `By ${item.seller} • ${item.delivery_time} Days Delivery`
            : `${item.category} • Instant Download`;

        html += `
            <li class="cart-item-row">
                <div class="cart-item-info">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        ${typeBadge}
                        <strong style="color: #ffffff; font-size: 0.92rem;">${item.title}</strong>
                    </div>
                    <span class="cart-item-sub">${subInfo}</span>
                </div>
                <div class="cart-item-actions">
                    <strong style="color: var(--gold); font-size: 0.95rem;">${item.price.toFixed(2)} ৳</strong>
                    <button onclick="removeUnifiedCartItem(${index})" class="cart-del-btn" title="Remove item">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </li>
        `;
    });
    html += '</ul>';
    list.innerHTML = html;

    if (totalEl) {
        totalEl.textContent = `${total.toFixed(2)} ৳`;
    }
}

async function checkoutUnifiedCart() {
    const cart = getStoredCart();
    if (cart.length === 0) {
        showToast('Your cart is empty!', 'error');
        return;
    }

    const checkoutBtn = document.getElementById('cart-checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.disabled = true;
        checkoutBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing Checkout...';
    }

    try {
        const response = await fetch('/api/cart/checkout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ items: cart })
        });

        if (response.status === 401 || response.status === 403) {
            alert('Please sign in to complete your checkout.');
            window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
            return;
        }

        const data = await response.json();

        if (data.success) {
            // Update balance display
            if (typeof data.new_balance !== 'undefined') {
                const bEl = document.getElementById('user-balance');
                const bDrop = document.getElementById('user-balance-dropdown');
                const formatted = Number(data.new_balance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                if (bEl) bEl.textContent = formatted;
                if (bDrop) bDrop.textContent = formatted;
            }

            // Clear cart
            saveStoredCart([]);

            // Render Success View in Modal
            const list = document.getElementById('cart-items-list');
            const totalEl = document.getElementById('cart-total-display');
            if (totalEl) totalEl.textContent = '0.00 ৳';

            let itemsHtml = '';
            if (data.orders && data.orders.length > 0) {
                itemsHtml += `<h4 style="color: #60a5fa; font-size: 0.95rem; margin: 12px 0 6px 0;"><i class="fa-solid fa-briefcase"></i> Active Service Orders:</h4>`;
                data.orders.forEach(o => {
                    itemsHtml += `
                        <div class="cart-success-item">
                            <span>Order #${o.id} - ${o.title}</span>
                            <a href="/dashboard/" class="btn-download-pkg" style="background: rgba(59, 130, 246, 0.2); border: 1px solid rgba(59, 130, 246, 0.4); color: #93c5fd;">
                                View in Dashboard <i class="fa-solid fa-arrow-right"></i>
                            </a>
                        </div>
                    `;
                });
            }

            if (data.products && data.products.length > 0) {
                itemsHtml += `<h4 style="color: #c084fc; font-size: 0.95rem; margin: 16px 0 6px 0;"><i class="fa-solid fa-download"></i> Digital Product Downloads:</h4>`;
                data.products.forEach(p => {
                    itemsHtml += `
                        <div class="cart-success-item">
                            <span>${p.title}</span>
                            <a href="${p.download_url}" class="btn-download-pkg" target="_blank">
                                <i class="fa-solid fa-file-arrow-down"></i> Download Package
                            </a>
                        </div>
                    `;
                });
            }

            if (list) {
                list.innerHTML = `
                    <div class="cart-success-view">
                        <div class="cart-success-icon"><i class="fa-solid fa-circle-check"></i></div>
                        <h3 class="cart-success-title">Payment &amp; Order Confirmed!</h3>
                        <p class="cart-success-desc">Deducted from your AdEzy virtual balance. New balance: <strong>${data.new_balance.toFixed(2)} ৳</strong>.</p>
                        
                        <div class="cart-success-list">
                            ${itemsHtml}
                        </div>
                        
                        <button class="btn btn-primary" onclick="toggleCartModal()" style="width: 100%;">
                            <i class="fa-solid fa-check"></i> Done
                        </button>
                    </div>
                `;
            }

            if (checkoutBtn) {
                checkoutBtn.style.display = 'none';
            }

            showToast('Checkout successful!', 'success');
        } else {
            alert(data.error || 'Checkout failed.');
            if (checkoutBtn) {
                checkoutBtn.disabled = false;
                checkoutBtn.innerHTML = '<i class="fa-solid fa-lock"></i> Checkout with Credits';
            }
        }
    } catch (e) {
        console.error('Checkout error:', e);
        alert('Network error during checkout. Please try again.');
        if (checkoutBtn) {
            checkoutBtn.disabled = false;
            checkoutBtn.innerHTML = '<i class="fa-solid fa-lock"></i> Checkout with Credits';
        }
    }
}

function quickBuySingleProduct(productId, title, price) {
    addProductToCart(productId, title, price, 'Digital Product');
    checkoutUnifiedCart();
}

// Expose unified cart functions to window
window.getStoredCart = getStoredCart;
window.saveStoredCart = saveStoredCart;
window.updateCartBadge = updateCartBadge;
window.toggleCartModal = toggleCartModal;
window.addServiceToCart = addServiceToCart;
window.addProductToCart = addProductToCart;
window.removeUnifiedCartItem = removeUnifiedCartItem;
window.clearEntireCart = clearEntireCart;
window.renderUnifiedCartUI = renderUnifiedCartUI;
window.checkoutUnifiedCart = checkoutUnifiedCart;
window.quickBuySingleProduct = quickBuySingleProduct;

// ============================================================================
// 20. WHATSAPP-STYLE LIVE MESSENGER CONTROLLER
// ============================================================================

let chatConversations = [];
let activeChatType = null; // 'direct' | 'order' | 'suggested'
let activeChatTarget = null; // username or orderId
let activeChatMeta = {};
let selectedChatAttachment = null;
let currentChatTab = 'all'; // 'all' | 'unread' | 'orders'
let chatPollingTimer = null;
let contactsCache = [];
let lastSeenTotalUnread = 0;
let hasInitializedChatPoller = false;

// Audio Chime Synthesizer (Web Audio API - zero external file dependencies)
function playMessageChime() {
    try {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextClass) return;
        const ctx = new AudioContextClass();
        const now = ctx.currentTime;

        // Tone 1: Gentle bell intro
        const osc1 = ctx.createOscillator();
        const gain1 = ctx.createGain();
        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(659.25, now); // E5
        gain1.gain.setValueAtTime(0.12, now);
        gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
        osc1.connect(gain1);
        gain1.connect(ctx.destination);
        osc1.start(now);
        osc1.stop(now + 0.18);

        // Tone 2: Crisp confirmation chime
        const osc2 = ctx.createOscillator();
        const gain2 = ctx.createGain();
        osc2.type = 'sine';
        osc2.frequency.setValueAtTime(987.77, now + 0.09); // B5
        gain2.gain.setValueAtTime(0.14, now + 0.09);
        gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.38);
        osc2.connect(gain2);
        gain2.connect(ctx.destination);
        osc2.start(now + 0.09);
        osc2.stop(now + 0.38);
    } catch (err) {
        console.debug('Audio chime skipped:', err);
    }
}

// Helpers
function escapeChatHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function formatChatFileSize(bytes) {
    if (!bytes || isNaN(bytes)) return '';
    if (bytes < 1024) return bytes + ' B';
    const kb = bytes / 1024;
    if (kb < 1024) return kb.toFixed(1) + ' KB';
    const mb = kb / 1024;
    return mb.toFixed(1) + ' MB';
}

function formatChatTime(isoString) {
    if (!isoString) return '';
    try {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return date.toLocaleDateString([], { weekday: 'short' });
        } else {
            return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
        }
    } catch (e) {
        return '';
    }
}

// Toggle Messenger Modal
function toggleChatApp() {
    const modal = document.getElementById('whatsapp-modal');
    if (!modal) return;

    if (modal.style.display === 'none' || !modal.style.display) {
        modal.style.display = 'flex';
        loadChatConversations();
        ensureChatPollerStarted();
    } else {
        modal.style.display = 'none';
        mobileBackToChatList();
    }
}

function closeChatApp() {
    const modal = document.getElementById('whatsapp-modal');
    if (modal) {
        modal.style.display = 'none';
        mobileBackToChatList();
    }
}

// Ensure polling starts on page load
let chatPollCounter = 0;
function ensureChatPollerStarted() {
    if (hasInitializedChatPoller) return;
    hasInitializedChatPoller = true;

    // Load initial conversation count silently for badge
    loadChatConversations(true);

    // Smart Adaptive Polling:
    // - Pause completely when the tab is hidden to save network and CPU.
    // - Every 3.5s:
    //     - If WhatsApp modal is open with active chat: poll messages every 3.5s for real-time feel.
    //     - Poll conversation list & unread counters every 3 ticks (~10.5s), or immediately if modal just opened.
    chatPollingTimer = setInterval(() => {
        if (isPageHidden()) return;

        chatPollCounter++;
        const modal = document.getElementById('whatsapp-modal');
        const isOpen = modal && modal.style.display === 'flex';

        if (isOpen && activeChatTarget) {
            loadActiveChatMessages(true);
        }

        if (chatPollCounter % 3 === 0 || (isOpen && !activeChatTarget)) {
            loadChatConversations(true);
        }
    }, 3500);

    // Immediate refresh on tab visibility change
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            loadChatConversations(true);
            const modal = document.getElementById('whatsapp-modal');
            if (modal && modal.style.display === 'flex' && activeChatTarget) {
                loadActiveChatMessages(true);
            }
        }
    });
}

// Load Conversations from API
async function loadChatConversations(silent = false) {
    const listEl = document.getElementById('whatsapp-conversations-list');
    if (!silent && listEl) {
        listEl.innerHTML = `
            <div class="chat-empty-state">
                <i class="fa-solid fa-spinner fa-spin text-gold" style="font-size: 1.8rem; margin-bottom: 8px;"></i>
                <p>Loading chats...</p>
            </div>
        `;
    }

    try {
        const response = await fetch('/api/conversations/');
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                if (!silent && listEl) {
                    listEl.innerHTML = `
                        <div class="chat-empty-state">
                            <i class="fa-solid fa-lock text-gold" style="font-size: 1.8rem; margin-bottom: 8px;"></i>
                            <p>Please <a href="/login/" style="color: var(--gold); text-decoration: underline;">log in</a> to view your conversations.</p>
                        </div>
                    `;
                }
            }
            return;
        }

        const data = await response.json();
        chatConversations = data.conversations || [];
        const totalUnread = data.total_unread || 0;

        // Global Navbar Badge
        const globalBadge = document.getElementById('global-msg-counter');
        if (globalBadge) {
            if (totalUnread > 0) {
                globalBadge.textContent = totalUnread > 99 ? '99+' : totalUnread;
                globalBadge.style.display = 'inline-flex';
            } else {
                globalBadge.style.display = 'none';
            }
        }

        // Also update legacy messages dropdown if present on page
        const legacyBadge = document.getElementById('messages-badge');
        if (legacyBadge) {
            if (totalUnread > 0) {
                legacyBadge.textContent = totalUnread;
                legacyBadge.style.display = 'block';
            } else {
                legacyBadge.style.display = 'none';
            }
        }
        const legacyList = document.getElementById('conversations-list');
        if (legacyList) {
            if (chatConversations.length > 0) {
                legacyList.innerHTML = chatConversations.map(conv => {
                    const timeAgo = getTimeAgo(new Date(conv.last_message_time));
                    return `
                        <div class="conversation-item ${conv.unread_count > 0 ? 'unread' : ''}" onclick="openWhatsAppChat('${conv.other_user}')" style="cursor: pointer;">
                            <div class="conversation-avatar">${conv.other_user_avatar || conv.other_user.charAt(0).toUpperCase()}</div>
                            <div class="conversation-content">
                                <div class="conversation-header">
                                    <span class="conversation-user">${escapeChatHtml(conv.other_user_name || conv.other_user)}</span>
                                    <span class="conversation-time">${timeAgo}</span>
                                </div>
                                <div class="conversation-gig">${escapeChatHtml(conv.latest_order_title || 'Direct Chat')}</div>
                                <div class="conversation-last-message">
                                    ${escapeChatHtml(conv.last_message)}
                                    ${conv.unread_count > 0 ? `<span class="conversation-unread">${conv.unread_count}</span>` : ''}
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                legacyList.innerHTML = `
                    <div class="empty-conversations">
                        <i class="fas fa-comments"></i>
                        <p>No messages yet</p>
                        <p style="font-size: 0.85rem;">Start a conversation by clicking on a seller</p>
                    </div>
                `;
            }
        }

        // Notification chime & toast when new incoming unread messages appear
        if (totalUnread > lastSeenTotalUnread && lastSeenTotalUnread >= 0) {
            playMessageChime();
            if (typeof showToast === 'function') {
                showToast('You have new incoming messages!', 'info');
            }
        }
        lastSeenTotalUnread = totalUnread;

        renderChatConversationsList();
    } catch (e) {
        console.error('Error loading conversations:', e);
        if (!silent && listEl) {
            listEl.innerHTML = `
                <div class="chat-empty-state">
                    <i class="fa-solid fa-triangle-exclamation" style="color: #ef4444; font-size: 1.8rem; margin-bottom: 8px;"></i>
                    <p>Unable to load chats. Click refresh to retry.</p>
                </div>
            `;
        }
    }
}

// Render Conversations List in Left Sidebar (One entry per contact, just like WhatsApp)
function renderChatConversationsList() {
    const listEl = document.getElementById('whatsapp-conversations-list');
    if (!listEl) return;

    const searchInput = document.getElementById('chat-search-input');
    const query = (searchInput ? searchInput.value : '').toLowerCase().trim();

    // Filter by tab
    let filtered = chatConversations.filter(c => {
        if (currentChatTab === 'unread') return c.unread_count > 0;
        if (currentChatTab === 'orders') return c.has_order === true;
        return true;
    });

    // Filter by search query
    if (query) {
        filtered = filtered.filter(c => {
            const user = (c.other_user || '').toLowerCase();
            const name = (c.other_user_name || '').toLowerCase();
            const orderTitle = (c.latest_order_title || '').toLowerCase();
            const msg = (c.last_message || '').toLowerCase();
            return user.includes(query) || name.includes(query) || orderTitle.includes(query) || msg.includes(query);
        });
    }

    if (filtered.length === 0) {
        listEl.innerHTML = `
            <div class="chat-empty-state">
                <i class="fa-solid fa-comments" style="font-size: 2rem; color: var(--gold); margin-bottom: 10px; opacity: 0.8;"></i>
                <p>No conversations found.<br>
                <span style="font-size: 0.78rem; color: var(--text-muted);">
                    Click the <i class="fa-solid fa-pen-to-square text-gold"></i> icon above to start chatting with a creator!
                </span></p>
            </div>
        `;
        return;
    }

    let html = '';
    filtered.forEach(c => {
        const isActive = (activeChatTarget === c.other_user);
        const avatarLetter = (c.other_user_avatar || c.other_user.charAt(0)).toUpperCase();
        const formattedTime = formatChatTime(c.last_message_time);
        const displayName = escapeChatHtml(c.other_user_name || c.other_user);

        let orderBadgeHtml = '';
        if (c.latest_order_id) {
            orderBadgeHtml = `<span style="font-size: 0.68rem; color: #93c5fd; background: rgba(59, 130, 246, 0.15); padding: 1px 6px; border-radius: 6px; margin-left: 6px;">Order #${c.latest_order_id}</span>`;
        }

        html += `
            <div class="conversation-row ${isActive ? 'active' : ''}" 
                 onclick="selectChat('${escapeChatHtml(c.other_user)}')">
                <div class="chat-avatar">${avatarLetter}</div>
                <div class="conv-meta-col">
                    <div class="conv-top-line">
                        <span class="conv-user-name">${displayName} ${orderBadgeHtml}</span>
                        <span class="conv-time">${formattedTime}</span>
                    </div>
                    <div class="conv-bottom-line">
                        <span class="conv-snippet">
                            ${c.has_attachment ? '<i class="fa-solid fa-paperclip text-gold"></i> ' : ''}
                            ${escapeChatHtml(c.last_message || 'Start chatting')}
                        </span>
                        ${c.unread_count > 0 ? `<span class="conv-unread-pill">${c.unread_count}</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    });

    listEl.innerHTML = html;
}

// Switch Tabs (All / Unread / Orders)
function switchChatTab(tab, btn) {
    currentChatTab = tab;
    document.querySelectorAll('.chat-tab-pill').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    renderChatConversationsList();
}

// Filter Chat List via Search Input
function filterChatList(query) {
    renderChatConversationsList();
}

// Focus search input from header
function focusChatSearch() {
    const input = document.getElementById('chat-search-input');
    if (input) {
        input.focus();
        input.select();
    }
}

// Select Active Chat Conversation (By Contact Username)
function selectChat(username) {
    const conv = chatConversations.find(c => c.other_user === username) || {
        other_user: username,
        other_user_avatar: username.charAt(0).toUpperCase(),
        other_user_name: username,
        latest_order_id: null,
        latest_order_title: null,
        status: 'Online'
    };

    activeChatType = 'direct';
    activeChatTarget = username;
    activeChatMeta = {
        otherUser: username,
        avatar: conv.other_user_avatar,
        name: conv.other_user_name || username,
        orderId: conv.latest_order_id,
        orderTitle: conv.latest_order_title
    };

    // Update Right Panel Header
    const avatarEl = document.getElementById('active-chat-avatar');
    const nameEl = document.getElementById('active-chat-name');
    const subEl = document.getElementById('active-chat-sub');
    const orderPill = document.getElementById('active-order-pill');

    if (avatarEl) avatarEl.textContent = conv.other_user_avatar;
    if (nameEl) nameEl.textContent = conv.other_user_name || username;
    if (subEl) subEl.textContent = 'Active now';

    if (orderPill) {
        if (conv.latest_order_id) {
            orderPill.textContent = `Order #${conv.latest_order_id} • ${conv.latest_order_title || 'Service'}`;
            orderPill.style.display = 'inline-block';
        } else {
            orderPill.style.display = 'none';
        }
    }

    // Toggle Empty View vs Active Chat
    const emptyView = document.getElementById('whatsapp-chat-empty');
    const activeView = document.getElementById('whatsapp-active-chat');
    if (emptyView) emptyView.style.display = 'none';
    if (activeView) activeView.style.display = 'flex';

    // Mobile View Toggle
    const sidebar = document.getElementById('whatsapp-sidebar');
    const panel = document.getElementById('whatsapp-chat-panel');
    if (sidebar && panel) {
        sidebar.classList.add('hide-on-mobile');
        panel.classList.add('show-on-mobile');
    }

    // Clear any previous attachment
    clearSelectedAttachment();

    // Re-render conversation list to highlight active item
    renderChatConversationsList();

    // Immediately load messages for this contact (with immediate clearing of old messages)
    loadActiveChatMessages(false);

    // Focus input
    setTimeout(() => {
        const input = document.getElementById('chat-text-input');
        if (input) input.focus();
    }, 150);
}

// Mobile Back to Conversation List
function mobileBackToChatList() {
    const sidebar = document.getElementById('whatsapp-sidebar');
    const panel = document.getElementById('whatsapp-chat-panel');
    if (sidebar && panel) {
        sidebar.classList.remove('hide-on-mobile');
        panel.classList.remove('show-on-mobile');
    }
}

// Monotonic request ID to completely eliminate async race conditions
let currentChatRequestId = 0;

// Load Messages for Currently Active Chat
async function loadActiveChatMessages(silent = false) {
    if (!activeChatTarget) return;

    const thisRequestId = ++currentChatRequestId;
    const requestedTarget = activeChatTarget;
    const flowEl = document.getElementById('chat-messages-flow');

    // On user chat switch, clear previous messages immediately so no cross-contact leak occurs!
    if (!silent && flowEl) {
        flowEl.innerHTML = `
            <div class="chat-empty-state" style="margin: auto;">
                <i class="fa-solid fa-spinner fa-spin text-gold" style="font-size: 1.8rem; margin-bottom: 8px;"></i>
                <p>Loading conversation...</p>
            </div>
        `;
    }

    try {
        const url = '/api/chat/messages/?username=' + encodeURIComponent(requestedTarget);
        const res = await fetch(url);
        if (!res.ok) return;

        const data = await res.json();
        if (!data.success) return;

        // Discard response if user has already switched to another contact in the meantime!
        if (thisRequestId !== currentChatRequestId || activeChatTarget !== requestedTarget) {
            return;
        }

        // Render message bubbles
        let bubblesHtml = '';
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(m => {
                const rowClass = m.is_own ? 'outgoing' : 'incoming';
                let attachHtml = '';

                if (m.has_attachment && m.attachment_url) {
                    if (m.attachment_type === 'image') {
                        attachHtml = `
                            <div class="bubble-img-wrap" onclick="openChatImageLightbox('${m.attachment_url}')">
                                <img src="${m.attachment_url}" alt="${escapeChatHtml(m.attachment_name || 'Attached Image')}" loading="lazy">
                            </div>
                        `;
                    } else {
                        attachHtml = `
                            <a href="${m.attachment_url}" target="_blank" download class="bubble-doc-card">
                                <i class="fa-solid fa-file-lines bubble-doc-icon"></i>
                                <div class="bubble-doc-meta">
                                    <span class="bubble-doc-name">${escapeChatHtml(m.attachment_name || 'Document')}</span>
                                    <span class="bubble-doc-tag"><i class="fa-solid fa-download"></i> Download file</span>
                                </div>
                            </a>
                        `;
                    }
                }

                let textHtml = '';
                if (m.message) {
                    textHtml = `<div class="bubble-text">${escapeChatHtml(m.message).replace(/\n/g, '<br>')}</div>`;
                }

                bubblesHtml += `
                    <div class="message-bubble-row ${rowClass}">
                        <div class="chat-bubble">
                            ${attachHtml}
                            ${textHtml}
                            <div class="bubble-meta">
                                <span>${m.time_formatted || ''}</span>
                                ${m.is_own ? '<i class="fa-solid fa-check-double text-gold" title="Delivered"></i>' : ''}
                            </div>
                        </div>
                    </div>
                `;
            });
        } else {
            bubblesHtml = `
                <div class="chat-empty-state" style="margin: auto;">
                    <div class="whatsapp-glow-circle" style="width: 60px; height: 60px; font-size: 1.8rem; margin: 0 auto 12px auto;">
                        <i class="fa-solid fa-comments"></i>
                    </div>
                    <p style="color: #ffffff; font-weight: 700; margin-bottom: 4px;">Start a Conversation</p>
                    <span style="font-size: 0.8rem; color: var(--text-muted);">
                        No messages yet with <strong>${escapeChatHtml(data.other_user ? data.other_user.name : requestedTarget)}</strong>. Say hello or discuss order requirements!
                    </span>
                </div>
            `;
        }

        if (flowEl && thisRequestId === currentChatRequestId) {
            const wasNearBottom = flowEl.scrollHeight - flowEl.clientHeight <= flowEl.scrollTop + 80;
            flowEl.innerHTML = bubblesHtml;
            if (!silent || wasNearBottom) {
                flowEl.scrollTop = flowEl.scrollHeight;
            }
        }

        // Mark local unread as cleared
        const found = chatConversations.find(c => c.other_user === requestedTarget);
        if (found && found.unread_count > 0) {
            found.unread_count = 0;
            renderChatConversationsList();
        }

    } catch (e) {
        console.error('Error fetching chat messages:', e);
    }
}

// Refresh Active Chat Manually
function refreshActiveChat() {
    loadActiveChatMessages();
    loadChatConversations(true);
}

// Auto-resize Chat Textarea
function autoResizeChatInput(el) {
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// Enter Key Handler for Chat Input
function handleChatInputKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        const form = document.getElementById('chat-send-form');
        if (form) {
            handleSendChatMessage(e);
        }
    }
}

// Trigger Hidden File Input
function triggerAttachmentSelect() {
    const fileInput = document.getElementById('chat-file-input');
    if (fileInput) fileInput.click();
}

// Handle File Selection
function handleChatFileSelected(input) {
    if (!input.files || !input.files[0]) return;

    const file = input.files[0];
    // Max 25 MB
    if (file.size > 25 * 1024 * 1024) {
        alert('File size exceeds the 25MB limit. Please choose a smaller file.');
        input.value = '';
        return;
    }

    selectedChatAttachment = file;

    const previewBar = document.getElementById('chat-attachment-preview');
    const nameLabel = document.getElementById('attachment-name-label');
    const sizeLabel = document.getElementById('attachment-size-label');
    const thumbEl = document.getElementById('attachment-thumb-preview');

    if (nameLabel) nameLabel.textContent = file.name;
    if (sizeLabel) sizeLabel.textContent = formatChatFileSize(file.size);

    if (thumbEl) {
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                thumbEl.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
            };
            reader.readAsDataURL(file);
        } else {
            thumbEl.innerHTML = `<i class="fa-solid fa-file-zipper"></i>`;
        }
    }

    if (previewBar) previewBar.style.display = 'flex';
}

// Clear Selected Attachment
function clearSelectedAttachment() {
    selectedChatAttachment = null;
    const fileInput = document.getElementById('chat-file-input');
    if (fileInput) fileInput.value = '';
    const previewBar = document.getElementById('chat-attachment-preview');
    if (previewBar) previewBar.style.display = 'none';
}

// Send Message with Text & Optional Attachment
async function handleSendChatMessage(event) {
    if (event) event.preventDefault();

    const input = document.getElementById('chat-text-input');
    const sendBtn = document.getElementById('chat-send-btn');
    const text = input ? input.value.trim() : '';

    if (!text && !selectedChatAttachment) {
        return;
    }

    if (!activeChatTarget) {
        alert('Please select a conversation first.');
        return;
    }

    // Build form data
    const formData = new FormData();
    formData.append('message', text);
    formData.append('username', activeChatTarget);

    if (activeChatMeta && activeChatMeta.orderId) {
        formData.append('order_id', activeChatMeta.orderId);
    }

    if (selectedChatAttachment) {
        formData.append('attachment', selectedChatAttachment);
    }

    // UI state
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    }

    try {
        const response = await fetch('/api/chat/send/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            // Reset input and attachment preview
            if (input) {
                input.value = '';
                autoResizeChatInput(input);
            }
            clearSelectedAttachment();

            // Refresh messages and conversation list
            await loadActiveChatMessages(true);
            loadChatConversations(true);
        } else {
            alert(data.error || 'Could not send message.');
        }
    } catch (e) {
        console.error('Send message error:', e);
        alert('Network error sending message. Please try again.');
    } finally {
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i>';
        }
    }
}

// Start New Chat Contacts Picker
function toggleNewChatPicker() {
    const picker = document.getElementById('new-chat-picker');
    if (!picker) return;

    if (picker.style.display === 'none' || !picker.style.display) {
        picker.style.display = 'block';
        loadChatContacts();
    } else {
        picker.style.display = 'none';
    }
}

// Load Contacts List
async function loadChatContacts() {
    const listEl = document.getElementById('picker-contacts-list');
    if (!listEl) return;

    try {
        const res = await fetch('/api/chat/contacts/');
        const data = await res.json();
        contactsCache = data.contacts || [];

        renderContactPickerList(contactsCache);
    } catch (e) {
        console.error('Error fetching contacts:', e);
        listEl.innerHTML = `<div class="chat-empty-state"><p style="color: #ef4444;">Error loading contacts.</p></div>`;
    }
}

function renderContactPickerList(contacts) {
    const listEl = document.getElementById('picker-contacts-list');
    if (!listEl) return;

    if (contacts.length === 0) {
        listEl.innerHTML = `<div class="chat-empty-state"><p>No creators found.</p></div>`;
        return;
    }

    let html = '';
    contacts.forEach(c => {
        html += `
            <div class="picker-contact-row" onclick="startChatWithContact('${escapeChatHtml(c.username)}', '${c.avatar}')">
                <div class="chat-avatar">${c.avatar}</div>
                <div class="picker-contact-info">
                    <span class="picker-contact-name">${escapeChatHtml(c.username)}</span>
                    <span class="picker-contact-sub">${c.role} • ${c.gigs_count} active services</span>
                </div>
            </div>
        `;
    });
    listEl.innerHTML = html;
}

function filterContactList(query) {
    const q = (query || '').toLowerCase().trim();
    if (!q) {
        renderContactPickerList(contactsCache);
        return;
    }
    const filtered = contactsCache.filter(c => c.username.toLowerCase().includes(q) || c.role.toLowerCase().includes(q));
    renderContactPickerList(filtered);
}

function startChatWithContact(username, avatar) {
    toggleNewChatPicker();
    selectChat(username);
}

// Open Direct Chat from Freelancer Gig Card ("Message Seller" button)
function openChatWithUser(username, gigTitle) {
    toggleChatApp();
    selectChat(username);

    if (gigTitle) {
        setTimeout(() => {
            const input = document.getElementById('chat-text-input');
            if (input) {
                input.value = `Hi @${username}, I'm interested in "${gigTitle}". Can we discuss the requirements?`;
                autoResizeChatInput(input);
                input.focus();
            }
        }, 300);
    }
}

// Open Chat for specific Order
function openChatForOrder(orderId, orderTitle) {
    toggleChatApp();
    loadChatConversations().then(() => {
        const found = chatConversations.find(c => c.latest_order_id == orderId);
        if (found) {
            selectChat(found.other_user);
        }
    });
}

// Image Zoom Lightbox
function openChatImageLightbox(src) {
    const lightbox = document.getElementById('chat-image-lightbox');
    const img = document.getElementById('lightbox-img');
    if (lightbox && img) {
        img.src = src;
        lightbox.style.display = 'flex';
    }
}

function closeChatLightbox() {
    const lightbox = document.getElementById('chat-image-lightbox');
    if (lightbox) lightbox.style.display = 'none';
}

// Expose WhatsApp Messenger methods globally
window.toggleChatApp = toggleChatApp;
window.closeChatApp = closeChatApp;
window.switchChatTab = switchChatTab;
window.filterChatList = filterChatList;
window.selectChat = selectChat;
window.mobileBackToChatList = mobileBackToChatList;
window.refreshActiveChat = refreshActiveChat;
window.autoResizeChatInput = autoResizeChatInput;
window.handleChatInputKey = handleChatInputKey;
window.triggerAttachmentSelect = triggerAttachmentSelect;
window.handleChatFileSelected = handleChatFileSelected;
window.clearSelectedAttachment = clearSelectedAttachment;
window.handleSendChatMessage = handleSendChatMessage;
window.toggleNewChatPicker = toggleNewChatPicker;
window.filterContactList = filterContactList;
window.startChatWithContact = startChatWithContact;
window.openChatWithUser = openChatWithUser;
window.openChatForOrder = openChatForOrder;
window.openChatImageLightbox = openChatImageLightbox;
window.closeChatLightbox = closeChatLightbox;
window.playMessageChime = playMessageChime;
window.focusChatSearch = focusChatSearch;

// Start poller once DOM content is ready
document.addEventListener('DOMContentLoaded', () => {
    ensureChatPollerStarted();
});
