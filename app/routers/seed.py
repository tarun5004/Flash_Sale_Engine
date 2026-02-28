"""
Seed Router — populates DB with demo flash-sale products.
Only active in DEBUG mode. Hit POST /seed/products to populate.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc
import random

from app.db.session import get_db
from app.core.config import settings
from app.models.product import Product

router = APIRouter(prefix="/seed", tags=["seed"])

# 350 realistic e-commerce products across 7 categories
CATEGORIES = {
    "Electronics": [
        "Wireless Bluetooth Earbuds", "Noise Cancelling Headphones", "USB-C Fast Charger",
        "Portable Power Bank 20000mAh", "Smart Watch Series 5", "Mechanical Gaming Keyboard",
        "Wireless Gaming Mouse", "4K Webcam HD", "Portable Bluetooth Speaker", "USB Hub 7-Port",
        "LED Desk Lamp Smart", "Laptop Stand Aluminium", "Wireless Charging Pad", "HDMI Cable 4K",
        "Smart Plug WiFi", "Ring Light 12 inch", "Streaming Microphone USB", "SSD 1TB NVMe",
        "RAM 16GB DDR5", "Graphics Tablet Drawing", "Smartphone Gimbal", "Drone Mini Camera",
        "Action Camera 4K", "VR Headset Standalone", "Portable Monitor 15.6",
        "Thunderbolt Dock", "Mesh WiFi Router", "Smart Doorbell Camera", "Solar Power Bank",
        "Electric Screwdriver Kit", "Thermal Printer Mini", "LED Strip Lights 10m",
        "Wireless Presenter Clicker", "Dash Cam 1440p", "Smart Light Bulb RGB",
        "Fitness Tracker Band", "E-Reader 6 inch", "Digital Alarm Clock", "Cable Management Kit",
        "Screen Protector Matte", "Phone Ring Holder", "Car Phone Mount Magnetic",
        "Bluetooth FM Transmitter", "Portable Air Purifier", "Mini Projector HD",
        "Surge Protector Strip", "Ethernet Cable Cat6 10ft", "WiFi Range Extender",
        "Smart Thermostat", "Robot Vacuum Cleaner",
    ],
    "Fashion": [
        "Premium Cotton T-Shirt", "Slim Fit Jeans Dark", "Running Sneakers Pro",
        "Leather Belt Classic", "Aviator Sunglasses UV400", "Wool Blend Overcoat",
        "Canvas Backpack Urban", "Sports Joggers Flex", "Formal Oxford Shoes",
        "Silk Pocket Square", "Denim Jacket Vintage", "Linen Summer Shirt",
        "Hoodie Zip-Up Fleece", "Chino Pants Stretch", "Crossbody Bag Compact",
        "Beanie Winter Knit", "Polo Shirt Classic", "Cargo Shorts Utility",
        "Loafers Suede Tan", "Watch Strap Leather", "Dress Socks Pack 6",
        "Athletic Compression Tights", "Rain Jacket Packable", "Trucker Cap Mesh",
        "Scarf Cashmere Blend", "Chelsea Boots Leather", "Swim Trunks Quick Dry",
        "Tie Slim Silk", "Wallet RFID Block", "Cufflinks Silver Set",
        "Puffer Vest Lightweight", "Track Jacket Retro", "Sandals Slide Comfort",
        "Graphic Sweatshirt Art", "Flannel Shirt Plaid", "Tote Bag Canvas",
        "Blazer Casual Knit", "Baseball Cap Fitted", "Pajama Set Cotton",
        "Gym Duffle Bag", "Flip Flops Premium", "Windbreaker Jacket",
        "Thermal Underwear Set", "Bucket Hat Summer", "Corduroy Pants Classic",
        "Sneaker Socks No-Show 8pk", "Peacoat Navy Wool", "Espadrilles Summer",
        "Messenger Bag Leather", "Quilted Jacket Padded",
    ],
    "Home & Kitchen": [
        "Stainless Steel Water Bottle", "Non-Stick Frying Pan 12in", "Bamboo Cutting Board Set",
        "French Press Coffee Maker", "Silicone Spatula Set 5pc", "Cast Iron Skillet 10in",
        "Electric Kettle 1.7L", "Knife Set Chef 8pc", "Measuring Cup Set Glass",
        "Spice Rack Rotating 20jar", "Dish Drying Rack Collapsible", "Baking Sheet Set 3pc",
        "Mixing Bowls Stainless 5pc", "Kitchen Scale Digital", "Can Opener Electric",
        "Salad Spinner Large", "Herb Garden Indoor Kit", "Ice Cube Tray Silicone 4pk",
        "Pizza Stone Ceramic", "Vegetable Peeler Y-Shape", "Colander Stainless Steel",
        "Wine Opener Electric", "Bread Box Bamboo Lid", "Salt and Pepper Grinder Set",
        "Oven Mitts Heat Resistant", "Food Storage Container 10pc", "Mandoline Slicer Pro",
        "Tea Infuser Stainless", "Apron Cotton Canvas", "Potato Masher Stainless",
        "Garlic Press Heavy Duty", "Rolling Pin Marble", "Whisk Silicone Coated",
        "Ladle Soup Stainless", "Trivet Set Silicone 4pc", "Cheese Grater 4-Side Box",
        "Kitchen Timer Magnetic", "Toaster 2-Slice Retro", "Blender Portable USB",
        "Air Fryer 5.5L Digital", "Slow Cooker 6qt", "Hand Mixer 5-Speed",
        "Rice Cooker 10-Cup", "Sous Vide Precision", "Espresso Machine Manual",
        "Juicer Centrifugal", "Waffle Maker Belgian", "Pancake Griddle Electric",
        "Meat Thermometer Instant", "Vacuum Sealer Machine",
    ],
    "Sports & Fitness": [
        "Yoga Mat Premium 6mm", "Resistance Bands Set 5", "Jump Rope Speed Pro",
        "Foam Roller Muscle", "Dumbbell Set Adjustable", "Pull-Up Bar Doorway",
        "Ab Roller Wheel", "Kettlebell Vinyl 20lb", "Boxing Gloves 12oz",
        "Tennis Racket Pro", "Basketball Indoor/Outdoor", "Soccer Ball Size 5",
        "Yoga Block Set 2pc", "Gym Gloves Weightlifting", "Battle Rope 30ft",
        "Agility Ladder 12 Rung", "Medicine Ball 10lb", "Ankle Weights 5lb Pair",
        "Stretching Strap Yoga", "Pushup Board Multi-Angle", "Suspension Trainer Kit",
        "Grip Strength Trainer", "Skipping Rope Weighted", "Stability Ball 65cm",
        "Pilates Ring Resistance", "Swim Goggles Anti-Fog", "Cycling Gloves Padded",
        "Climbing Chalk Bag", "Massage Gun Deep Tissue", "Ice Pack Gel Reusable",
        "Wrist Wraps Lifting", "Knee Sleeve Compression", "Back Brace Support",
        "Shin Guards Soccer", "Badminton Set Complete", "Table Tennis Paddle Pro",
        "Golf Balls Practice 50pk", "Fishing Rod Combo", "Camping Hammock Ultralight",
        "Hiking Poles Carbon", "Water Bottle Sport 32oz", "Headband Sweat Wicking",
        "Running Armband Phone", "Bicycle Pump Portable", "Skateboard Complete 31in",
        "Roller Skates Adult", "Snorkel Set Complete", "Surfboard Foam Beginner",
        "Rock Climbing Harness", "Trail Running Shoes",
    ],
    "Beauty & Care": [
        "Vitamin C Serum 30ml", "Moisturizer SPF 30", "Lip Balm Organic 4pk",
        "Shampoo Sulfate Free", "Conditioner Deep Repair", "Face Wash Gentle Foam",
        "Sunscreen SPF 50 Lotion", "Hair Oil Argan 100ml", "Body Lotion Shea Butter",
        "Deodorant Natural Roll-On", "Face Mask Sheet 10pk", "Eye Cream Anti-Aging",
        "Toothpaste Whitening Mint", "Hand Cream Intensive", "Perfume Eau de Toilette",
        "Nail Polish Set Gel 6pk", "Makeup Brush Set 12pc", "Foundation Liquid Matte",
        "Mascara Waterproof Volume", "Concealer Full Coverage", "Blush Palette 6shade",
        "Eyeshadow Palette Neutral", "Setting Spray Matte", "Primer Pore Minimizing",
        "Micellar Water Cleansing", "Toner Hydrating Rose", "Exfoliator Gentle Scrub",
        "Night Cream Retinol", "BB Cream Tinted SPF25", "Dry Shampoo Volumizing",
        "Hair Spray Strong Hold", "Beard Oil Cedar Wood", "Razor Safety Metal",
        "Aftershave Balm Cooling", "Bath Bomb Gift Set 8pc", "Shower Gel Energizing",
        "Foot Cream Repair", "Cuticle Oil Pen", "Eyelash Curler Gold",
        "Hair Ties Elastic 50pk", "Makeup Mirror LED", "Cotton Pads Organic 100pk",
        "Facial Roller Jade", "Tweezers Precision Tip", "Scalp Massager Shampoo",
        "Hair Dryer Ionic Fast", "Straightener Ceramic Pro", "Curling Iron 1.5in",
        "Teeth Whitening Strips", "Electric Toothbrush Sonic",
    ],
    "Books & Stationery": [
        "Notebook A5 Dotted 200pg", "Fountain Pen Classic", "Highlighter Set 12clr",
        "Planner 2025 Weekly", "Sticky Notes Neon 6pk", "Pencil Mechanical 0.5mm 3pk",
        "Sketchbook A4 Spiral", "Marker Fine Tip 24clr", "Eraser Dust-Free 4pk",
        "Ruler Steel 30cm", "Scissors Precision 8in", "Tape Dispenser Desktop",
        "Stapler Mini Compact", "Paper Clips Colorful 200pk", "Binder Clips Assorted",
        "Folder Expanding A4", "Index Cards Ruled 200pk", "Glue Stick Set 8pc",
        "Correction Tape 6pk", "Pencil Case Canvas", "Desk Organizer Bamboo",
        "Bookmarks Magnetic 8pk", "Washi Tape Set 20 rolls", "Calligraphy Pen Set",
        "Drawing Pencil Set 12pc", "Colored Pencil 48set", "Watercolor Paint 24clr",
        "Brush Pen Lettering 6pk", "Clipboard Acrylic A4", "Envelope Kraft 50pk",
        "Stamp Pad Ink Multi", "Page Flags Arrow 5clr", "Label Maker Handheld",
        "Whiteboard Marker 8pk", "Cork Board 24x36", "Easel Pad Large 25sh",
        "Calculator Scientific", "Laminating Sheets A4 50pk", "Paper Trimmer Guillotine",
        "Book Stand Adjustable", "Desk Pad Leather Large", "Pen Holder Ceramic",
        "Letter Opener Brass", "Wax Seal Stamp Kit", "Journal Gratitude Daily",
        "Bullet Journal Dotgrid", "Diary Leather Bound", "Origami Paper 200sh",
        "Globe Desktop Decor", "Magnifying Glass Brass",
    ],
    "Toys & Games": [
        "Building Blocks 1000pcs", "Board Game Strategy", "Puzzle 1000pc Landscape",
        "RC Car Off-Road 4WD", "Drone Mini Indoor", "Card Game Party Pack",
        "Chess Set Wooden Premium", "Rubiks Cube Speed", "Nerf Blaster Elite",
        "Lego Architecture Set", "Stuffed Animal Bear XL", "Play-Doh 24 Color Pack",
        "Marble Run 150pc", "Science Kit Chemistry", "Telescope Kids Beginner",
        "Microscope Student 40x", "Magic Kit 100 Tricks", "Yo-Yo Professional Metal",
        "Frisbee Ultimate 175g", "Kite Diamond Large", "Bubble Machine Automatic",
        "Water Gun Super Soaker", "Slinky Original Metal", "Etch A Sketch Classic",
        "Dominos Double 12 Set", "Jenga Giant Outdoor", "Operation Board Game",
        "Monopoly Classic Edition", "Scrabble Deluxe", "Risk World Conquest",
        "Uno Card Game Deluxe", "Connect Four Classic", "Battleship Strategy",
        "Twister Party Game", "Pictionary Air", "Trivial Pursuit Family",
        "Boggle Word Game", "Clue Mystery Game", "Sorry Board Game",
        "Yahtzee Score Pads", "Checkers Wood Set", "Backgammon Travel Set",
        "Dart Board Pro Cork", "Ping Pong Ball 50pk", "Juggling Ball Set 3pc",
        "Kendama Wooden Pro", "Spinning Top Metal", "Walkie Talkie Kids 2pk",
        "Binoculars Compact 10x25", "Compass Navigator Brass",
    ],
}


@router.post("/products")
async def seed_products(session: AsyncSession = Depends(get_db)):
    """Populate DB with 350 demo products across 7 categories. Idempotent — skips if products exist."""
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Seed only available in DEBUG mode")

    # Check if products already exist
    count_result = await session.execute(select(sqlfunc.count(Product.id)))
    existing_count = count_result.scalar()
    if existing_count > 0:
        return {"message": f"Already seeded ({existing_count} products exist). Delete DB to re-seed."}

    products = []
    for category, names in CATEGORIES.items():
        for name in names:
            price = round(random.uniform(99, 9999), 2)
            stock = random.randint(5, 200)
            products.append(
                Product(
                    name=f"{name} — {category}",
                    price=price,
                    stock=stock,
                    is_active=True,
                )
            )

    session.add_all(products)
    await session.commit()

    return {"message": f"Seeded {len(products)} products across {len(CATEGORIES)} categories."}
