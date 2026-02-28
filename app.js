/* =================================================================
   Flash Sale Engine — Presentation-Grade JavaScript
   ─────────────────────────────────────────────────
   ● localStorage is used ONLY as a TEMPORARY MOCK DATA LAYER.
   ● Every interaction that would hit a real server is routed
     through a single simulated backend function:
         simulateBackendCall(action, payload)
   ● Each call site has a clear comment like:
         // 🔌 BACKEND: POST /api/cart/add  { product_id, qty }
     so you can see exactly where the real API plugs in.
   ● Stock is NEVER decremented optimistically. The "backend"
     confirms first, THEN the UI updates (flash-sale safety).
   ================================================================= */

"use strict";

/* =================================================================
   SECTION 1 — CONSTANTS & CONFIG
   ================================================================= */

const STORAGE_KEYS = {
    products: "fs_products",
    cart: "fs_cart",
};

const CATEGORIES = [
    "All",
    "Men's Fashion",
    "Women's Fashion",
    "Electronics",
    "Footwear",
    "Accessories",
    "Home & Living",
    "Beauty",
];

const SALE_DURATION_HOURS = 6; // flash sale runs for 6 hours from first load

/* =================================================================
   SECTION 2 — SIMULATED PRODUCT CATALOG
   These arrays drive the procedural product generator.
   In production, products come from GET /api/products.
   ================================================================= */

const CATALOG = {
    "Men's Fashion": {
        brands: ["Roadster", "HRX", "Allen Solly", "Peter England", "Levi's", "WROGN", "U.S. Polo", "H&M", "Puma", "Nike"],
        items: [
            "Slim Fit Casual Shirt", "Printed T-Shirt", "Denim Jacket",
            "Chino Trousers", "Polo Collar T-Shirt", "Formal Blazer",
            "Cotton Kurta", "Jogger Pants", "Hooded Sweatshirt",
            "Regular Fit Jeans", "Checked Shirt", "Bomber Jacket",
            "Henley T-Shirt", "Linen Shirt", "Cargo Pants",
            "Track Pants", "Graphic Tee", "Windbreaker Jacket"
        ],
    },
    "Women's Fashion": {
        brands: ["AND", "Vero Moda", "Forever 21", "ONLY", "FabAlley", "Zara", "MANGO", "W", "Biba", "Global Desi"],
        items: [
            "Fit & Flare Dress", "Floral Maxi Dress", "Crop Top",
            "High-Rise Jeggings", "A-line Kurta", "Wrap Top",
            "Pleated Skirt", "Off-Shoulder Top", "Palazzo Pants",
            "Printed Jumpsuit", "Ruffled Blouse", "Denim Shorts",
            "Bodycon Dress", "Cotton Kurti Set", "Straight Pants",
            "Embroidered Top", "Anarkali Suit", "Sheath Dress"
        ],
    },
    "Electronics": {
        brands: ["boAt", "JBL", "Sony", "Samsung", "OnePlus", "Xiaomi", "Noise", "Realme", "Apple", "Lenovo"],
        items: [
            "Wireless Earbuds", "Bluetooth Headphones", "Smart Watch",
            "Portable Speaker", "USB-C Hub", "Fast Charger 65W",
            "Power Bank 20000mAh", "Webcam HD 1080p", "LED Desk Lamp",
            "Wireless Mouse", "Mechanical Keyboard", "32GB Pen Drive",
            "Fitness Band", "Neckband Earphones", "Phone Stand",
            "Car Charger", "HDMI Cable 2m", "Screen Protector"
        ],
    },
    "Footwear": {
        brands: ["Nike", "Adidas", "Puma", "Reebok", "Skechers", "Bata", "Woodland", "Crocs", "Campus", "Red Tape"],
        items: [
            "Running Shoes", "Casual Sneakers", "Flip Flops",
            "Sports Sandals", "Formal Oxford Shoes", "Slip-On Loafers",
            "High-Top Sneakers", "Canvas Shoes", "Hiking Boots",
            "Mesh Walking Shoes", "Leather Boots", "Platform Sneakers",
            "Training Shoes", "Slide Slippers", "Derby Shoes",
            "Driving Loafers", "Trail Running Shoes", "Clogs"
        ],
    },
    "Accessories": {
        brands: ["Fastrack", "Titan", "Fossil", "Wildcraft", "Skybags", "Tommy Hilfiger", "Ray-Ban", "Casio", "Daniel Wellington", "Lavie"],
        items: [
            "Analog Watch", "Classic Sunglasses", "Leather Wallet",
            "Laptop Backpack", "Crossbody Bag", "Baseball Cap",
            "Aviator Sunglasses", "Digital Watch", "Canvas Belt",
            "Travel Duffel Bag", "Card Holder", "Chain Bracelet",
            "Silk Tie", "Scarf", "Beanie",
            "Cufflinks Set", "Phone Case Premium", "Umbrella"
        ],
    },
    "Home & Living": {
        brands: ["HomeTown", "Spaces", "Cortina", "Bombay Dyeing", "Story@Home", "IKEA", "Urban Ladder", "Lushomes", "Solimo", "Kuber"],
        items: [
            "Cushion Cover Set", "Scented Candle", "Wall Clock",
            "Cotton Bedsheet", "Table Lamp", "Photo Frame Set",
            "Bath Towel Pack", "Throw Blanket", "Door Mat",
            "Storage Box Organizer", "Curtains Pair", "Artificial Plant",
            "Coffee Mug Set", "Coaster Set", "Wall Shelf",
            "Vase Ceramic", "Fairy Lights String", "Dinner Set"
        ],
    },
    "Beauty": {
        brands: ["Maybelline", "Lakme", "L'Oreal", "MAC", "Biotique", "Mamaearth", "The Body Shop", "Nykaa", "Cetaphil", "Plum"],
        items: [
            "Matte Lipstick", "BB Cream SPF30", "Sheet Mask Pack",
            "Kajal Eyeliner", "Compact Powder", "Hair Serum",
            "Moisturizer 100ml", "Nail Polish Set", "Face Wash Gel",
            "Perfume 50ml", "Setting Spray", "Eye Shadow Palette",
            "Lip Gloss Trio", "Sunscreen SPF50", "Face Toner",
            "Body Lotion", "Hair Oil 200ml", "Makeup Remover"
        ],
    },
};

/* Image service — picsum.photos provides free demo images */
function productImage(id, w = 400, h = 533) {
    return `https://picsum.photos/seed/flash${id}/${w}/${h}`;
}

/* =================================================================
   SECTION 3 — PRODUCT GENERATOR
   Generates 350 products ONCE, then persists to localStorage.
   ● stock_left: random 0-15  (some are sold out from the start)
   ● Prices, discounts all vary per product
   ================================================================= */

function generateProducts() {
    // 🔌 BACKEND: In production, this entire function is replaced
    //    by a single call:  GET /api/products
    //    The backend database holds the real catalog, stock counts,
    //    and prices. This generator is ONLY for demo / presentation.

    const TARGET_COUNT = 350;
    const products = [];
    let id = 1;

    const categoryNames = Object.keys(CATALOG);
    const perCategory = Math.ceil(TARGET_COUNT / categoryNames.length); // ~50 each

    for (const category of categoryNames) {
        const { brands, items } = CATALOG[category];
        for (let i = 0; i < perCategory && id <= TARGET_COUNT; i++) {
            const brand = brands[i % brands.length];
            const item = items[i % items.length];

            const originalPrice = randomInt(299, 7999);
            const discountPercent = randomInt(10, 70);
            const price = Math.round(originalPrice * (1 - discountPercent / 100));

            // Stock: 0-15.  ~15% of products are sold out at generation time.
            const stock = Math.random() < 0.15 ? 0 : randomInt(1, 15);

            products.push({
                id,
                name: item,
                brand,
                price,
                original_price: originalPrice,
                discount_percent: discountPercent,
                stock_left: stock,
                image_url: productImage(id),
                description: `${brand} ${item}. Premium quality, limited flash-sale stock. ${stock === 0 ? "Currently sold out." : `Only ${stock} left — hurry!`}`,
                category,
            });
            id++;
        }
    }

    return products;
}

function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

/* =================================================================
   SECTION 4 — LOCAL STORAGE HELPERS (MOCK DATA LAYER)
   ================================================================= */

function loadProducts() {
    const raw = localStorage.getItem(STORAGE_KEYS.products);
    if (raw) return JSON.parse(raw);
    const products = generateProducts();
    localStorage.setItem(STORAGE_KEYS.products, JSON.stringify(products));
    return products;
}

function saveProducts(products) {
    localStorage.setItem(STORAGE_KEYS.products, JSON.stringify(products));
}

function loadCart() {
    const raw = localStorage.getItem(STORAGE_KEYS.cart);
    return raw ? JSON.parse(raw) : [];
}

function saveCart(cart) {
    localStorage.setItem(STORAGE_KEYS.cart, JSON.stringify(cart));
}

/* =================================================================
   SECTION 5 — SIMULATED BACKEND
   ─────────────────────────────────────────────────────────────────
   THIS IS THE SINGLE POINT WHERE ALL "SERVER LOGIC" LIVES.
   Every action that modifies state goes through here.

   In a real app, each case becomes a fetch() to the backend API.
   The comment above each case shows the exact endpoint.

   The function returns a Promise to mirror real async network calls.
   ================================================================= */

/**
 * Simulated backend call.
 * @param {string} action - The operation name.
 * @param {object} payload - Data for the operation.
 * @returns {Promise<{ok: boolean, data?: any, error?: string}>}
 */
async function simulateBackendCall(action, payload = {}) {
    // Simulate network latency (50-200ms) for realism
    await sleep(randomInt(50, 200));

    const products = loadProducts();

    switch (action) {

        /* ──────────────────────────────────────────────
           GET ALL PRODUCTS
           🔌 BACKEND: GET /api/products?category=...&search=...
           ────────────────────────────────────────────── */
        case "GET_PRODUCTS": {
            let filtered = [...products];
            if (payload.category && payload.category !== "All") {
                filtered = filtered.filter(p => p.category === payload.category);
            }
            if (payload.search) {
                const q = payload.search.toLowerCase();
                filtered = filtered.filter(p =>
                    p.name.toLowerCase().includes(q) ||
                    p.brand.toLowerCase().includes(q) ||
                    p.category.toLowerCase().includes(q)
                );
            }
            return { ok: true, data: filtered };
        }

        /* ──────────────────────────────────────────────
           GET SINGLE PRODUCT BY ID
           🔌 BACKEND: GET /api/products/{id}
           ────────────────────────────────────────────── */
        case "GET_PRODUCT": {
            const product = products.find(p => p.id === payload.id);
            if (!product) return { ok: false, error: "Product not found" };
            return { ok: true, data: { ...product } };
        }

        /* ──────────────────────────────────────────────
           ADD TO CART  (with stock validation)
           🔌 BACKEND: POST /api/cart/add  { product_id, quantity: 1 }
           ── Flash-sale rule: Stock is checked server-side.
              If stock < 1, the add is REJECTED.
              This prevents overselling.
           ────────────────────────────────────────────── */
        case "ADD_TO_CART": {
            const product = products.find(p => p.id === payload.product_id);
            if (!product) return { ok: false, error: "Product not found" };

            // 🛡️ OVERSELL PREVENTION: Check stock BEFORE allowing add
            if (product.stock_left < 1) {
                return { ok: false, error: "Sorry, this item is sold out!" };
            }

            const cart = loadCart();
            const existing = cart.find(c => c.product_id === payload.product_id);

            if (existing) {
                return { ok: false, error: "Item is already in your cart" };
            }

            // ✅ Stock is available — reserve 1 unit
            // 🔌 In real backend, this uses SELECT FOR UPDATE + atomic decrement
            //    to prevent race conditions (two users buying the last item)
            product.stock_left -= 1;
            saveProducts(products);

            cart.push({
                product_id: product.id,
                name: product.name,
                brand: product.brand,
                price: product.price,
                original_price: product.original_price,
                discount_percent: product.discount_percent,
                image_url: product.image_url,
                quantity: 1,  // Flash sale: quantity fixed at 1 per person
            });
            saveCart(cart);

            return { ok: true, data: { cart_size: cart.length, stock_remaining: product.stock_left } };
        }

        /* ──────────────────────────────────────────────
           REMOVE FROM CART  (restore stock)
           🔌 BACKEND: DELETE /api/cart/{product_id}
           ── When a user removes an item, stock is restored
              so another user can buy it.
           ────────────────────────────────────────────── */
        case "REMOVE_FROM_CART": {
            const cart = loadCart();
            const idx = cart.findIndex(c => c.product_id === payload.product_id);
            if (idx === -1) return { ok: false, error: "Item not in cart" };

            // Restore stock
            const prod = products.find(p => p.id === payload.product_id);
            if (prod) {
                prod.stock_left += 1;
                saveProducts(products);
            }

            cart.splice(idx, 1);
            saveCart(cart);
            return { ok: true, data: { cart_size: cart.length } };
        }

        /* ──────────────────────────────────────────────
           GET CART
           🔌 BACKEND: GET /api/cart
           ────────────────────────────────────────────── */
        case "GET_CART": {
            const cart = loadCart();
            // Refresh stock info from products (may have changed)
            const enriched = cart.map(item => {
                const p = products.find(pr => pr.id === item.product_id);
                return {
                    ...item,
                    current_stock: p ? p.stock_left : 0,
                };
            });
            return { ok: true, data: enriched };
        }

        /* ──────────────────────────────────────────────
           PLACE ORDER  (checkout)
           🔌 BACKEND: POST /api/orders  { items: [...] }
           ── In a real flash sale, the backend does a FINAL
              stock check, creates the order, processes payment,
              and only THEN confirms. If payment fails, stock
              is restored (compensation pattern).
           ────────────────────────────────────────────── */
        case "PLACE_ORDER": {
            const cart = loadCart();
            if (cart.length === 0) return { ok: false, error: "Cart is empty" };

            // Final stock check for each item
            for (const item of cart) {
                const p = products.find(pr => pr.id === item.product_id);
                // Stock was already decremented at add-to-cart time,
                // so we just validate the product still exists
                if (!p) return { ok: false, error: `Product #${item.product_id} no longer available` };
            }

            // Clear cart (order placed successfully)
            saveCart([]);

            const total = cart.reduce((sum, i) => sum + i.price * i.quantity, 0);
            return {
                ok: true,
                data: {
                    order_id: `FS-${Date.now()}`,
                    items_count: cart.length,
                    total,
                    message: "Order placed successfully! 🎉",
                },
            };
        }

        default:
            return { ok: false, error: `Unknown action: ${action}` };
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/* =================================================================
   SECTION 6 — APPLICATION STATE
   ================================================================= */

let currentPage = "home";       // "home" | "detail" | "cart"
let currentCategory = "All";
let currentSearch = "";
let currentProductId = null;     // for detail page
let cartCount = 0;

/* =================================================================
   SECTION 7 — SPA NAVIGATION
   Switches between the 3 pages by toggling visibility.
   ================================================================= */

function navigateTo(page, data = {}) {
    currentPage = page;

    // Hide all pages
    document.getElementById("pageHome").classList.add("hidden");
    document.getElementById("pageDetail").classList.add("hidden");
    document.getElementById("pageCart").classList.add("hidden");

    // Show/hide category chips (only on home)
    document.getElementById("categorySection").classList.toggle("hidden", page !== "home");

    // Update active nav button
    document.getElementById("navHome").classList.toggle("active", page === "home");
    document.getElementById("navCart").classList.toggle("active", page === "cart");

    switch (page) {
        case "home":
            document.getElementById("pageHome").classList.remove("hidden");
            renderProductGrid();
            window.scrollTo({ top: 0, behavior: "smooth" });
            break;

        case "detail":
            currentProductId = data.productId;
            document.getElementById("pageDetail").classList.remove("hidden");
            renderProductDetail(data.productId);
            window.scrollTo({ top: 0, behavior: "smooth" });
            break;

        case "cart":
            document.getElementById("pageCart").classList.remove("hidden");
            renderCart();
            window.scrollTo({ top: 0, behavior: "smooth" });
            break;
    }
}

/* =================================================================
   SECTION 8 — RENDER: PRODUCT GRID (Home Page)
   ================================================================= */

async function renderProductGrid() {
    const grid = document.getElementById("productGrid");
    const empty = document.getElementById("emptyState");
    const title = document.getElementById("listingTitle");
    const count = document.getElementById("listingCount");

    grid.innerHTML = '<div class="empty-state"><p>Loading...</p></div>';

    // 🔌 BACKEND: GET /api/products?category=...&search=...
    const res = await simulateBackendCall("GET_PRODUCTS", {
        category: currentCategory,
        search: currentSearch,
    });

    if (!res.ok) {
        grid.innerHTML = "";
        empty.classList.remove("hidden");
        return;
    }

    const products = res.data;

    title.textContent = currentCategory === "All" ? "All Products" : currentCategory;
    count.textContent = `(${products.length} items)`;

    if (products.length === 0) {
        grid.innerHTML = "";
        empty.classList.remove("hidden");
        return;
    }

    empty.classList.add("hidden");
    grid.innerHTML = products.map(p => productCardHTML(p)).join("");

    // Attach click handlers
    grid.querySelectorAll(".product-card").forEach(card => {
        card.addEventListener("click", () => {
            const id = parseInt(card.dataset.id, 10);
            if (card.classList.contains("sold-out")) return; // can't click sold-out
            navigateTo("detail", { productId: id });
        });
    });
}

function productCardHTML(p) {
    const isSoldOut = p.stock_left === 0;
    const isLowStock = p.stock_left > 0 && p.stock_left <= 3;
    const stockClass = isSoldOut ? "critical" : (p.stock_left <= 3 ? "low" : "ok");
    const stockPct = Math.min((p.stock_left / 15) * 100, 100);

    return `
    <div class="product-card slide-up ${isSoldOut ? "sold-out" : ""}" data-id="${p.id}">
        <div class="card-img">
            <img src="${p.image_url}" alt="${p.name}" loading="lazy">
            <div class="card-badges">
                ${p.discount_percent >= 30 ? `<span class="badge badge-sale">${p.discount_percent}% OFF</span>` : ""}
                ${isLowStock ? '<span class="badge badge-low-stock">Few Left!</span>' : ""}
                ${isSoldOut ? '<span class="badge badge-sold-out">Sold Out</span>' : ""}
            </div>
        </div>
        <div class="card-body">
            <div class="card-brand">${p.brand}</div>
            <div class="card-name">${p.name}</div>
            <div class="card-price-row">
                <span class="card-price">₹${p.price.toLocaleString("en-IN")}</span>
                <span class="card-mrp">₹${p.original_price.toLocaleString("en-IN")}</span>
                <span class="card-discount">(${p.discount_percent}% OFF)</span>
            </div>
        </div>
        <div class="stock-bar-wrap">
            <div class="stock-info">
                <span class="stock-label">${isSoldOut ? "Sold Out" : "Stock"}</span>
                <span class="stock-count ${stockClass}">${isSoldOut ? "0" : p.stock_left} left</span>
            </div>
            <div class="stock-bar">
                <div class="stock-bar-fill ${stockClass}" style="width: ${stockPct}%"></div>
            </div>
        </div>
    </div>`;
}

/* =================================================================
   SECTION 9 — RENDER: PRODUCT DETAIL PAGE
   ================================================================= */

async function renderProductDetail(productId) {
    const container = document.getElementById("detailContent");
    container.innerHTML = '<p style="padding: 40px; text-align: center;">Loading product...</p>';

    // 🔌 BACKEND: GET /api/products/{id}
    const res = await simulateBackendCall("GET_PRODUCT", { id: productId });

    if (!res.ok) {
        container.innerHTML = `<p style="padding: 40px; text-align:center;">Product not found.</p>`;
        return;
    }

    const p = res.data;
    const isSoldOut = p.stock_left === 0;
    const isLowStock = p.stock_left > 0 && p.stock_left <= 3;

    // Check if already in cart
    const cart = loadCart();
    const inCart = cart.some(c => c.product_id === p.id);

    let stockBoxClass, stockIcon, stockText;
    if (isSoldOut) {
        stockBoxClass = "out-stock";
        stockIcon = "❌";
        stockText = "Sold Out — No stock remaining";
    } else if (isLowStock) {
        stockBoxClass = "low-stock";
        stockIcon = "⚠️";
        stockText = `Hurry! Only ${p.stock_left} left in stock`;
    } else {
        stockBoxClass = "in-stock";
        stockIcon = "✅";
        stockText = `${p.stock_left} items in stock`;
    }

    container.innerHTML = `
        <button class="detail-back" onclick="navigateTo('home')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>
            Back to products
        </button>

        <div class="detail-img-wrap ${isSoldOut ? 'sold-out' : ''}">
            <img src="${p.image_url}" alt="${p.name}">
            <div class="card-badges">
                ${p.discount_percent >= 30 ? `<span class="badge badge-sale">${p.discount_percent}% OFF</span>` : ""}
                ${isLowStock ? '<span class="badge badge-low-stock">Few Left!</span>' : ""}
                ${isSoldOut ? '<span class="badge badge-sold-out">Sold Out</span>' : ""}
            </div>
        </div>

        <div class="detail-info">
            <div class="detail-brand">${p.brand}</div>
            <div class="detail-name">${p.name}</div>

            <div class="detail-price-box">
                <span class="detail-price">₹${p.price.toLocaleString("en-IN")}</span>
                <span class="detail-mrp">MRP ₹${p.original_price.toLocaleString("en-IN")}</span>
                <span class="detail-discount">(${p.discount_percent}% OFF)</span>
            </div>
            <div class="detail-tax">inclusive of all taxes</div>

            <div class="detail-stock-box ${stockBoxClass}">
                <span class="detail-stock-icon">${stockIcon}</span>
                <span class="detail-stock-text">${stockText}</span>
            </div>

            <div class="detail-actions">
                <button
                    class="btn btn-primary"
                    id="btnAddToCart"
                    ${isSoldOut || inCart ? "disabled" : ""}
                    onclick="handleAddToCart(${p.id})"
                >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
                    ${isSoldOut ? "SOLD OUT" : inCart ? "IN CART ✓" : "ADD TO BAG"}
                </button>
                <button class="btn btn-outline" onclick="navigateTo('cart')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                    GO TO CART
                </button>
            </div>

            <div class="detail-description">
                <h3>Product Details</h3>
                <p>${p.description}</p>
                <br>
                <p><strong>Category:</strong> ${p.category}</p>
                <p><strong>Brand:</strong> ${p.brand}</p>
                <p><strong>Discount:</strong> ${p.discount_percent}% off MRP</p>
            </div>
        </div>
    `;
}

/* =================================================================
   SECTION 10 — ADD TO CART HANDLER
   ─────────────────────────────────────────────────────────────────
   Critical flash-sale path:
   1. User clicks "ADD TO BAG"
   2. We call the simulated backend
   3. Backend checks stock ➜ if available, decrements stock and adds to cart
   4. ONLY on success do we update the UI
   5. If stock = 0, the request is REJECTED
   This prevents overselling even in a concurrent environment.
   ================================================================= */

async function handleAddToCart(productId) {
    const btn = document.getElementById("btnAddToCart");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "ADDING...";
    }

    // 🔌 BACKEND: POST /api/cart/add  { product_id, quantity: 1 }
    // 🛡️ Server-side stock check prevents overselling
    const res = await simulateBackendCall("ADD_TO_CART", { product_id: productId });

    if (res.ok) {
        updateCartBadge(res.data.cart_size);
        showToast(`Added to bag! (${res.data.stock_remaining} left in stock)`, "success");

        // Re-render the detail page to show updated stock & "IN CART" state
        renderProductDetail(productId);
    } else {
        showToast(res.error, "error");
        if (btn) {
            btn.disabled = false;
            btn.textContent = "ADD TO BAG";
        }
    }
}

/* =================================================================
   SECTION 11 — RENDER: CART PAGE
   ================================================================= */

async function renderCart() {
    const container = document.getElementById("cartContent");
    container.innerHTML = '<p style="padding: 40px; text-align: center;">Loading cart...</p>';

    // 🔌 BACKEND: GET /api/cart
    const res = await simulateBackendCall("GET_CART");
    const items = res.ok ? res.data : [];

    updateCartBadge(items.length);

    if (items.length === 0) {
        container.innerHTML = `
            <div class="cart-header">
                <h2>My Bag</h2>
            </div>
            <div class="cart-empty">
                <div class="cart-empty-icon">🛍️</div>
                <h3>Your bag is empty</h3>
                <p>Looks like you haven't added anything yet. Flash sale items are going fast!</p>
                <button class="btn btn-primary" onclick="navigateTo('home')" style="margin: 0 auto;">
                    CONTINUE SHOPPING
                </button>
            </div>
        `;
        return;
    }

    const subtotal = items.reduce((s, i) => s + i.price * i.quantity, 0);
    const totalMrp = items.reduce((s, i) => s + i.original_price * i.quantity, 0);
    const savings = totalMrp - subtotal;

    container.innerHTML = `
        <div class="cart-header">
            <h2>My Bag</h2>
            <span class="cart-count-tag">${items.length} item${items.length > 1 ? "s" : ""}</span>
        </div>

        <div class="cart-items">
            ${items.map(item => cartItemHTML(item)).join("")}
        </div>

        <div class="cart-summary">
            <h3>Price Details (${items.length} Item${items.length > 1 ? "s" : ""})</h3>
            <div class="summary-row">
                <span>Total MRP</span>
                <span>₹${totalMrp.toLocaleString("en-IN")}</span>
            </div>
            <div class="summary-row">
                <span>Discount on MRP</span>
                <span class="summary-savings">-₹${savings.toLocaleString("en-IN")}</span>
            </div>
            <div class="summary-row">
                <span>Shipping</span>
                <span class="summary-savings">FREE</span>
            </div>
            <div class="summary-row total">
                <span>Total Amount</span>
                <span>₹${subtotal.toLocaleString("en-IN")}</span>
            </div>
            <button class="btn btn-primary btn-checkout" onclick="handleCheckout()">
                PLACE ORDER
            </button>
        </div>
    `;

    // Attach remove handlers
    container.querySelectorAll(".cart-item-remove").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            e.stopPropagation();
            const pid = parseInt(btn.dataset.productId, 10);
            await handleRemoveFromCart(pid);
        });
    });

    // Attach click to image (go to detail)
    container.querySelectorAll(".cart-item-img").forEach(el => {
        el.addEventListener("click", () => {
            const pid = parseInt(el.dataset.productId, 10);
            navigateTo("detail", { productId: pid });
        });
    });
}

function cartItemHTML(item) {
    let stockHtml = "";
    if (item.current_stock === 0) {
        stockHtml = `<div class="cart-item-stock danger">⚠ Last one was yours!</div>`;
    } else if (item.current_stock <= 3) {
        stockHtml = `<div class="cart-item-stock warn">Only ${item.current_stock} more in stock</div>`;
    } else {
        stockHtml = `<div class="cart-item-stock safe">${item.current_stock} in stock</div>`;
    }

    return `
    <div class="cart-item">
        <div class="cart-item-img" data-product-id="${item.product_id}">
            <img src="${item.image_url}" alt="${item.name}" loading="lazy">
        </div>
        <div class="cart-item-body">
            <div class="cart-item-brand">${item.brand}</div>
            <div class="cart-item-name">${item.name}</div>
            <div class="cart-item-price-row">
                <span class="cart-item-price">₹${item.price.toLocaleString("en-IN")}</span>
                <span class="cart-item-mrp">₹${item.original_price.toLocaleString("en-IN")}</span>
                <span class="cart-item-discount">(${item.discount_percent}% OFF)</span>
            </div>
            ${stockHtml}
            <button class="cart-item-remove" data-product-id="${item.product_id}">✕ REMOVE</button>
        </div>
    </div>`;
}

/* =================================================================
   SECTION 12 — REMOVE FROM CART
   ================================================================= */

async function handleRemoveFromCart(productId) {
    // 🔌 BACKEND: DELETE /api/cart/{product_id}
    // Stock is restored on server when item is removed
    const res = await simulateBackendCall("REMOVE_FROM_CART", { product_id: productId });

    if (res.ok) {
        updateCartBadge(res.data.cart_size);
        showToast("Item removed from bag", "warning");
        renderCart(); // re-render cart page
    } else {
        showToast(res.error, "error");
    }
}

/* =================================================================
   SECTION 13 — CHECKOUT / PLACE ORDER
   ================================================================= */

async function handleCheckout() {
    const btn = document.querySelector(".btn-checkout");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "PLACING ORDER...";
    }

    // 🔌 BACKEND: POST /api/orders
    // Real backend does: final stock check → create order → process payment
    // If payment fails → compensate (restore stock)
    const res = await simulateBackendCall("PLACE_ORDER");

    if (res.ok) {
        showToast(`${res.data.message} Order: ${res.data.order_id}`, "success");
        updateCartBadge(0);
        // Show empty cart after short delay
        setTimeout(() => renderCart(), 500);
    } else {
        showToast(res.error, "error");
        if (btn) {
            btn.disabled = false;
            btn.textContent = "PLACE ORDER";
        }
    }
}

/* =================================================================
   SECTION 14 — CATEGORY FILTER CHIPS
   ================================================================= */

function renderCategoryChips() {
    const scroll = document.getElementById("categoryScroll");
    scroll.innerHTML = CATEGORIES.map(cat => `
        <button class="chip ${cat === currentCategory ? "active" : ""}" data-category="${cat}">
            ${cat}
        </button>
    `).join("");

    scroll.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            currentCategory = chip.dataset.category;
            renderCategoryChips();
            renderProductGrid();
        });
    });
}

/* =================================================================
   SECTION 15 — SEARCH
   ================================================================= */

function initSearch() {
    const input = document.getElementById("searchInput");
    let debounceTimer;

    input.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            currentSearch = input.value.trim();
            if (currentPage !== "home") navigateTo("home");
            else renderProductGrid();
        }, 300);
    });
}

/* =================================================================
   SECTION 16 — FLASH SALE COUNTDOWN TIMER
   ================================================================= */

function initCountdownTimer() {
    const TIMER_KEY = "fs_sale_end";
    let endTime = localStorage.getItem(TIMER_KEY);

    if (!endTime) {
        endTime = Date.now() + SALE_DURATION_HOURS * 60 * 60 * 1000;
        localStorage.setItem(TIMER_KEY, endTime);
    } else {
        endTime = parseInt(endTime, 10);
    }

    function tick() {
        const now = Date.now();
        const diff = Math.max(0, endTime - now);

        const h = Math.floor(diff / 3600000);
        const m = Math.floor((diff % 3600000) / 60000);
        const s = Math.floor((diff % 60000) / 1000);

        document.getElementById("timerH").textContent = String(h).padStart(2, "0");
        document.getElementById("timerM").textContent = String(m).padStart(2, "0");
        document.getElementById("timerS").textContent = String(s).padStart(2, "0");

        if (diff > 0) {
            requestAnimationFrame(() => setTimeout(tick, 1000));
        } else {
            document.querySelector(".sale-strip").style.background =
                "linear-gradient(90deg, #333 0%, #555 100%)";
            document.querySelector(".sale-msg").textContent = "Sale has ended!";
        }
    }

    tick();
}

/* =================================================================
   SECTION 17 — UTILITIES (Toast, Cart Badge)
   ================================================================= */

function showToast(message, type = "info") {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.className = `toast toast-${type} show`;

    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}

function updateCartBadge(count) {
    cartCount = count;
    const badge = document.getElementById("cartBadge");
    badge.textContent = count;
    badge.classList.toggle("hidden", count === 0);
}

/* =================================================================
   SECTION 18 — APP INITIALIZATION
   ================================================================= */

document.addEventListener("DOMContentLoaded", () => {
    // Load products into localStorage if first visit
    loadProducts();

    // Set initial cart badge count
    const cart = loadCart();
    updateCartBadge(cart.length);

    // Render UI
    renderCategoryChips();
    renderProductGrid();

    // Start systems
    initSearch();
    initCountdownTimer();

    console.log("⚡ Flash Sale Engine loaded.");
    console.log("📦 Products in store:", loadProducts().length);
    console.log("🛒 Items in cart:", cart.length);
    console.log("──────────────────────────────────────────");
    console.log("💡 TIP: To reset all data, run in console:");
    console.log('   localStorage.clear(); location.reload();');
});
