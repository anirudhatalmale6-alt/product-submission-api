#!/usr/bin/env python3
"""
Phase 10AG: Add Buyer-Intent Architecture to 30 PetHub Online Posts
- Type 1: "Best For" Suitability Blocks
- Type 2: Pros/Cons (Key Considerations) Blocks
- Type 3: Practical Routine/Checklist Blocks
"""

import subprocess
import json
import time
import csv
import os
import sys
import tempfile
import html

WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
LOG_DIR = "/var/lib/freelancer/projects/40416335/phase10ag_data"
LOG_FILE = os.path.join(LOG_DIR, "buyer_intent_log.csv")

# ─── Content Blocks by Post ID ─────────────────────────────────────────────────

SUITABILITY_BLOCKS = {
    # Batch 1: Product guides
    3956: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for puppies:</strong> Soft rubber toys and rope toys that are gentle on developing teeth — avoid anything too hard or with small detachable parts",
            "<strong>Best for senior dogs:</strong> Plush toys and gentle fetch toys that don't require intense jaw pressure or high-impact catching",
            "<strong>Best for heavy chewers:</strong> Natural rubber and reinforced nylon toys designed for powerful jaws — look for 'tough chewer' ratings from the manufacturer",
            "<strong>Best for small breeds:</strong> Appropriately sized toys they can carry and grip; oversized toys can frustrate small dogs and discourage play",
            "<strong>Best on a budget:</strong> Rope toys and basic rubber balls offer excellent durability per pound spent — budget and mid-range options often outperform premium alternatives"
        ]
    },
    3957: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for extreme chewers (power jaw breeds):</strong> Solid natural rubber toys rated for aggressive chewing — these withstand sustained pressure without splintering",
            "<strong>Best for moderate-heavy chewers:</strong> Reinforced nylon or layered rubber toys that balance durability with some give for comfortable chewing",
            "<strong>Best for anxious chewers:</strong> Durable toys that also offer food-stuffing options, combining stress relief with lasting construction",
            "<strong>Best for multi-dog households:</strong> Tough toys in multiple sizes so each dog has an appropriate option — reduces competition and breakage",
            "<strong>Best on a budget:</strong> Natural rubber Kong-style toys at budget to mid-range prices tend to last months even with daily heavy use"
        ]
    },
    3959: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for high-energy dogs:</strong> Multi-step puzzle toys and treat-dispensing balls that require sustained effort to solve",
            "<strong>Best for food-motivated dogs:</strong> Snuffle mats and slow-feeder puzzle toys that turn mealtime into mental enrichment",
            "<strong>Best for dogs home alone:</strong> Self-play interactive toys and frozen-stuffable puzzles that provide independent entertainment",
            "<strong>Best for senior dogs:</strong> Simpler puzzle toys with easy-to-manipulate components that maintain cognitive engagement without frustration",
            "<strong>Best on a budget:</strong> DIY enrichment (muffin tin puzzles, towel wraps) combined with one good treat-dispensing toy covers most needs affordably"
        ]
    },
    3996: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for large breeds (25kg+):</strong> Beds with reinforced stitching, thick bolsters, and high-density foam that won't flatten under sustained weight",
            "<strong>Best for dogs with joint issues:</strong> Memory foam or orthopaedic beds with at least 10cm depth — these distribute weight evenly across pressure points",
            "<strong>Best for warm climates or summer:</strong> Elevated mesh beds or beds with cooling gel layers that promote airflow underneath",
            "<strong>Best for puppies and young dogs:</strong> Waterproof, machine-washable beds with removable covers — durability and easy cleaning matter most at this stage",
            "<strong>Best on a budget:</strong> A quality mid-range bed with a removable washable cover will outlast two or three budget beds in most cases"
        ]
    },
    4004: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for dogs with hip dysplasia:</strong> High-density memory foam beds (10cm+ depth) that cradle joints and reduce pressure on the hip socket",
            "<strong>Best for post-surgery recovery:</strong> Flat orthopaedic mattresses with low entry points so dogs don't need to step over raised bolsters",
            "<strong>Best for senior dogs with arthritis:</strong> Beds combining memory foam with a heated element or thermal lining for warmth that soothes stiff joints",
            "<strong>Best for large breeds prone to joint issues:</strong> Extra-large orthopaedic beds with non-skid bases — wobbling beds undermine the orthopaedic benefit",
            "<strong>Best on a budget:</strong> A solid memory foam mattress-style bed without fancy features still delivers the core joint support most dogs need"
        ]
    },
    4011: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for brachycephalic breeds (pugs, bulldogs):</strong> Cooling beds are particularly valuable since flat-faced breeds overheat easily and struggle to self-regulate temperature",
            "<strong>Best for double-coated breeds:</strong> Elevated mesh cooling beds that allow maximum airflow beneath thick coats",
            "<strong>Best for outdoor use:</strong> Raised cooling cots with UV-resistant fabric — gel mats can overheat in direct sunlight",
            "<strong>Best for indoor climate control:</strong> Pressure-activated cooling gel mats that work without electricity or water",
            "<strong>Best on a budget:</strong> Elevated mesh beds at budget prices outperform many premium gel options for consistent cooling"
        ]
    },
    4018: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for crate training puppies:</strong> Flat, machine-washable pads that fit standard crate dimensions — avoid raised bolsters that puppies will chew",
            "<strong>Best for teething puppies (3-6 months):</strong> Chew-resistant beds with waterproof liners, since teething pups will gnaw and drool on everything",
            "<strong>Best for anxious puppies:</strong> Donut-style bolster beds that create a nest-like enclosure, providing a sense of security during the transition period",
            "<strong>Best for fast-growing large breed puppies:</strong> Size up from the start or choose adjustable beds — a bed that fits at 8 weeks will be too small by 16 weeks",
            "<strong>Best on a budget:</strong> Layered towels or fleece blankets inside the crate work perfectly for the first few weeks while you assess your puppy's chewing habits"
        ]
    },
    4027: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for dogs that pull on walks:</strong> Front-clip harnesses that redirect momentum toward you, naturally discouraging pulling without discomfort",
            "<strong>Best for small breeds and toy dogs:</strong> Lightweight step-in harnesses that distribute pressure across the chest instead of the delicate trachea",
            "<strong>Best for hiking and active dogs:</strong> Padded adventure harnesses with a back handle for assistance on steep terrain",
            "<strong>Best for reactive dogs:</strong> Secure, escape-proof harnesses with dual clip points (front and back) for maximum control in unpredictable situations",
            "<strong>Best on a budget:</strong> A well-fitted basic Y-shaped harness offers better comfort and control than most expensive collars"
        ]
    },
    4034: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for strong pullers (20kg+):</strong> Front-clip harnesses with a wide chest panel — the front attachment point redirects forward momentum effectively",
            "<strong>Best for dogs in training:</strong> Dual-clip harnesses (front and back rings) that give you flexibility to switch between training and relaxed walking modes",
            "<strong>Best for nervous or reactive dogs:</strong> Padded, snug-fitting harnesses that provide a gentle 'hugging' sensation without restricting natural gait",
            "<strong>Best for barrel-chested breeds (bulldogs, pugs):</strong> Harnesses with adjustable straps at multiple points, since standard sizing rarely fits these body shapes",
            "<strong>Best on a budget:</strong> Mid-range front-clip harnesses with good reviews typically deliver the same no-pull benefit as premium brands"
        ]
    },
    4042: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for training recall:</strong> Long training leads (5-10 metres) that give controlled freedom while maintaining a safety connection",
            "<strong>Best for strong pullers:</strong> Padded handle leads with traffic handles (short secondary grip near the clip) for close control in busy areas",
            "<strong>Best for multi-dog walking:</strong> Coupler leads or dual-handle systems that keep two dogs at comfortable distance without tangling",
            "<strong>Best for small breeds:</strong> Lightweight, narrow leads that don't weigh down a small dog's collar or harness",
            "<strong>Best on a budget:</strong> A sturdy nylon lead with a quality snap hook outperforms most premium options — the clip quality matters more than the lead material"
        ]
    },
    # Batch 2: Educational/care guides
    4057: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for first-time groomers:</strong> Start with a quality slicker brush, nail clippers, and gentle shampoo — these three tools handle 80% of home grooming needs",
            "<strong>Best for double-coated breeds:</strong> Undercoat rakes and deshedding tools are essential during seasonal coat changes (spring and autumn)",
            "<strong>Best for dogs with sensitive skin:</strong> Hypoallergenic shampoos and soft-bristle brushes that clean without irritating reactive skin",
            "<strong>Best for curly/wire-coated breeds:</strong> Pin brushes and detangling sprays prevent matting between professional grooming appointments",
            "<strong>Best on a budget:</strong> A slicker brush, basic nail clipper, and oatmeal shampoo create a complete grooming kit at a budget-friendly price point"
        ]
    },
    4064: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for short, smooth coats (Labradors, Beagles):</strong> Rubber curry brushes or bristle brushes that remove loose hair and distribute natural oils",
            "<strong>Best for long, silky coats (Setters, Spaniels):</strong> Pin brushes for daily maintenance combined with a wide-toothed comb for tangle prevention",
            "<strong>Best for double coats (Huskies, German Shepherds):</strong> Undercoat rakes for seasonal shedding and slicker brushes for regular upkeep",
            "<strong>Best for curly/wool coats (Poodles, Doodles):</strong> Slicker brushes for daily mat prevention — these coat types require the most frequent brushing",
            "<strong>Best for wire coats (Terriers, Schnauzers):</strong> Stripping knives or stripping combs for hand-stripping, plus a slicker brush for maintenance"
        ]
    },
    4071: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for sensitive or itchy skin:</strong> Oatmeal-based or aloe vera shampoos free from sulphates, parabens, and artificial fragrances",
            "<strong>Best for white or light coats:</strong> Brightening shampoos with natural optical enhancers that lift staining without bleaching agents",
            "<strong>Best for dogs bathed frequently:</strong> Mild, soap-free formulas that won't strip natural oils even with regular use (every 2-4 weeks)",
            "<strong>Best for dogs with a strong odour:</strong> Deodorising shampoos with enzymatic action rather than just fragrance masking",
            "<strong>Best on a budget:</strong> Unscented oatmeal shampoo concentrates diluted properly last months and suit nearly all coat types"
        ]
    },
    4078: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for anxious dogs:</strong> Electric nail grinders that gradually file nails — the slow approach builds confidence in dogs who fear traditional clippers",
            "<strong>Best for dark nails (where the quick isn't visible):</strong> Grinders with LED lights or guillotine-style clippers that allow small, controlled cuts",
            "<strong>Best for large breeds:</strong> Heavy-duty scissor-style clippers with a spring mechanism — these provide the leverage needed for thick nails",
            "<strong>Best for puppies and small breeds:</strong> Small scissor clippers or mini grinders designed for thin, delicate nails",
            "<strong>Best on a budget:</strong> A quality scissor-style clipper with replaceable blades lasts years and handles most nail types effectively"
        ]
    },
    4089: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best starting point for new dog owners:</strong> Focus on flea/tick prevention, dental care basics, and understanding your dog's normal behaviour — these three areas prevent the most common health problems",
            "<strong>Best for senior dogs (7+ years):</strong> Joint supplements, twice-yearly vet check-ups, and weight management become priorities as dogs age",
            "<strong>Best for active/working dogs:</strong> Joint support from an early age, paw care after walks, and monitoring for exercise-related injuries",
            "<strong>Best for puppies:</strong> Vaccination schedule completion, parasite prevention, and establishing a relationship with your vet during the critical first year",
            "<strong>Best on a budget:</strong> Preventative care (dental hygiene, weight management, regular flea treatment) costs far less than treating the conditions they prevent"
        ]
    },
    4096: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for dogs who resist tooth brushing:</strong> Dental chews, water additives, and dental diets that clean teeth passively without daily brushing battles",
            "<strong>Best for toy and small breeds:</strong> Finger brushes and enzymatic toothpastes — small mouths benefit from gentle, precise cleaning tools",
            "<strong>Best for dogs prone to plaque build-up:</strong> Daily brushing combined with VOHC-approved dental chews for maximum plaque disruption",
            "<strong>Best for senior dogs with existing dental disease:</strong> Vet assessment first, then a maintenance routine tailored to their remaining teeth and gum health",
            "<strong>Best on a budget:</strong> A canine toothbrush and enzymatic toothpaste used three times weekly prevents most dental disease at minimal ongoing cost"
        ]
    },
    4103: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for dogs with known flea allergies:</strong> Fast-acting spot-on or oral treatments that kill fleas before they bite — speed matters most for allergic dogs",
            "<strong>Best for multi-pet households:</strong> Treatments that break the flea life cycle in the environment, not just on the pet — otherwise reinfestation is inevitable",
            "<strong>Best for dogs who swim frequently:</strong> Oral flea treatments that aren't affected by water exposure, unlike some topical applications",
            "<strong>Best for puppies:</strong> Age-appropriate treatments (most spot-ons require a minimum of 8 weeks old and a minimum weight) — always check label guidance",
            "<strong>Best on a budget:</strong> Year-round prevention with a reliable spot-on treatment costs a fraction of treating a full-blown flea infestation"
        ]
    },
    4110: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for senior dogs with stiffness:</strong> Glucosamine and chondroitin combinations supported by veterinary evidence for maintaining cartilage health",
            "<strong>Best for large breed puppies:</strong> Early joint support during rapid growth phases — consult your vet about starting supplements from 12 months",
            "<strong>Best for post-surgery recovery:</strong> Green-lipped mussel and omega-3 supplements that support joint lubrication and reduce inflammation naturally",
            "<strong>Best for active and working dogs:</strong> Preventative joint supplementation before symptoms appear, particularly for breeds predisposed to hip or elbow dysplasia",
            "<strong>Best on a budget:</strong> Single-ingredient supplements (e.g., pure glucosamine powder) offer the core benefit at a lower price than multi-ingredient blends"
        ]
    },
    4118: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for first-time dog owners:</strong> Positive reinforcement foundations — reward-based training builds trust and delivers reliable results without specialist equipment",
            "<strong>Best for reactive or fearful dogs:</strong> Counter-conditioning and desensitisation techniques guided by a certified behaviourist, not general training classes",
            "<strong>Best for high-drive breeds:</strong> Structured enrichment and task-based training that channels energy productively (agility, scent work, obedience)",
            "<strong>Best for adolescent dogs (6-18 months):</strong> Consistency and patience during the 'teenage phase' — most regression is normal and resolves with continued practice",
            "<strong>Best on a budget:</strong> Free online resources from reputable organisations (Dogs Trust, Blue Cross, RSPCA) cover all foundational training techniques"
        ]
    },
    4132: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best approach for weeks 8-12:</strong> Focus on socialisation, housetraining basics, and name recognition — this is the critical socialisation window",
            "<strong>Best for nervous puppies:</strong> Gentle, force-free exposure to new experiences at the puppy's own pace — rushing creates lasting fear rather than confidence",
            "<strong>Best for working breed puppies:</strong> Early impulse control games and structured play that channels natural working instincts appropriately",
            "<strong>Best for families with children:</strong> Teaching children calm interaction alongside puppy training — both puppy and child need guidance for safe coexistence",
            "<strong>Best on a budget:</strong> Puppy socialisation classes at local training clubs are typically affordable and provide the structured social exposure puppies need most"
        ]
    },
    # Batch 3: Cat/mixed guides
    4174: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for kittens:</strong> Lightweight, fast-moving toys (feather wands, small balls) that match their developing coordination and high energy levels",
            "<strong>Best for senior cats:</strong> Gentle puzzle feeders and slow-moving toys that engage without requiring athletic leaping or sprinting",
            "<strong>Best for indoor-only cats:</strong> A rotation of interactive, puzzle, and solo-play toys that replicate the variety of outdoor stimulation",
            "<strong>Best for low-energy cats:</strong> Catnip-infused toys and motion-activated toys that spark interest without requiring the cat to initiate play",
            "<strong>Best on a budget:</strong> Crinkle balls, cardboard boxes, and a single quality wand toy provide more enrichment than an expensive toy collection"
        ]
    },
    4181: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for high-energy cats:</strong> Wand toys with feather or ribbon attachments that allow vigorous chase-and-pounce sessions",
            "<strong>Best for food-motivated cats:</strong> Puzzle feeders and treat-dispensing balls that combine mental challenge with a food reward",
            "<strong>Best for cats home alone during the day:</strong> Battery-operated or motion-activated toys that provide stimulation without human involvement",
            "<strong>Best for bonding and socialisation:</strong> Wand toys and laser pointers (always end with a physical 'catch') that create shared play experiences",
            "<strong>Best on a budget:</strong> A homemade wand toy (stick, string, fabric) provides the same interactive engagement as premium wand toys"
        ]
    },
    4188: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for catnip-sensitive cats (approx. 60-70% of cats):</strong> Fresh, high-quality catnip toys that use whole leaf rather than ground stem for maximum potency",
            "<strong>Best for catnip-insensitive cats:</strong> Silver vine or valerian root alternatives, which affect many cats that don't respond to traditional catnip",
            "<strong>Best for kittens under 6 months:</strong> Most kittens don't respond to catnip until maturity — save catnip toys for later and use feather or ball toys instead",
            "<strong>Best for multi-cat households:</strong> Individual catnip toys for each cat to prevent resource guarding — some cats become possessive during catnip sessions",
            "<strong>Best on a budget:</strong> Loose dried catnip sprinkled on an old sock tied in a knot works as well as any commercial catnip toy"
        ]
    },
    4286: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for large cats (5kg+):</strong> Sturdy, heavy-base posts at least 80cm tall — shorter or lighter posts topple and discourage use",
            "<strong>Best for multi-cat households:</strong> Cat trees with multiple scratching surfaces at different heights, giving each cat their own territory",
            "<strong>Best for kittens:</strong> Shorter, stable posts with sisal rope wrapping that teaches healthy scratching habits from the start",
            "<strong>Best for cats who scratch furniture:</strong> Place the scratching post directly next to the targeted furniture piece — location matters more than the post itself",
            "<strong>Best on a budget:</strong> A simple sisal-wrapped vertical post in the right location outperforms expensive cat trees placed in unused corners"
        ]
    },
    4307: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for small flats and limited floor space:</strong> Wall-mounted scratchers that use vertical wall space without any floor footprint",
            "<strong>Best for active climbers:</strong> Wall-mounted systems with multiple levels that double as climbing routes and elevated resting platforms",
            "<strong>Best for cats who scratch walls or door frames:</strong> Mount the scratcher at the exact height and location of the unwanted scratching behaviour",
            "<strong>Best for renters:</strong> Removable wall-mounted options using heavy-duty adhesive strips rather than permanent fixings",
            "<strong>Best on a budget:</strong> A single sisal-wrapped wall panel at the right height addresses most scratching needs without a full wall system"
        ]
    },
    4300: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for horizontal scratchers:</strong> Cats who prefer to scratch along the floor (carpets, rugs) typically prefer flat cardboard scratching pads",
            "<strong>Best for testing scratching preferences:</strong> Inexpensive cardboard scratchers help you determine if your cat prefers horizontal, vertical, or angled surfaces",
            "<strong>Best for multi-cat households:</strong> Cardboard scratchers are affordable enough to place one per cat, reducing territorial competition",
            "<strong>Best for eco-conscious owners:</strong> Cardboard scratchers are recyclable and often made from recycled materials — the most sustainable option available",
            "<strong>Best on a budget:</strong> Cardboard scratchers offer the lowest cost per use of any scratching option and are easily replaced when worn"
        ]
    },
    4314: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for kittens:</strong> Low-entry trays without lids that are easy to access — kittens may avoid covered trays during litter training",
            "<strong>Best for large breeds (Maine Coon, Ragdoll):</strong> Extra-large trays with high sides — standard trays are often too small and cause litter scatter",
            "<strong>Best for multi-cat households:</strong> One tray per cat plus one extra, placed in separate locations — this is the standard veterinary recommendation",
            "<strong>Best for odour control:</strong> Covered or hooded trays with carbon filters, combined with daily scooping and regular full litter changes",
            "<strong>Best on a budget:</strong> A large, basic open tray scooped daily is more hygienic than an expensive self-cleaning unit used inconsistently"
        ]
    },
    4321: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for odour control:</strong> Clumping clay or silica crystal litters form tight clumps that trap odour effectively when scooped daily",
            "<strong>Best for kittens:</strong> Non-clumping litter until 12 weeks old (kittens may ingest clumping litter during exploration), then transition to clumping",
            "<strong>Best for cats with respiratory sensitivity:</strong> Low-dust or dust-free formulas — natural paper or wood pellet litters tend to produce less airborne dust",
            "<strong>Best for the environment:</strong> Biodegradable litters (wood, paper, corn, tofu) that can be composted or disposed of more sustainably than clay",
            "<strong>Best on a budget:</strong> Wood pellet litter offers excellent absorbency and odour control at the lowest ongoing cost per month"
        ]
    },
    4335: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for flat dwellers:</strong> Sealed disposal bins with odour-lock lids that contain smell in small living spaces",
            "<strong>Best for multi-cat households:</strong> Larger-capacity disposal systems or lined bins that handle higher waste volumes without daily outdoor trips",
            "<strong>Best for eco-conscious owners:</strong> Biodegradable litter bags combined with compostable litter — avoid flushing any cat litter regardless of label claims",
            "<strong>Best for convenience:</strong> Dedicated litter disposal bins with one-hand operation for quick daily scooping routines",
            "<strong>Best on a budget:</strong> Nappy disposal bags (widely available and inexpensive) work perfectly for sealing used litter before bin disposal"
        ]
    },
    4406: {
        "title": "Quick Suitability Guide",
        "items": [
            "<strong>Best for solo indoor cats:</strong> A combination of automated toys and puzzle feeders that provide stimulation during owner absence",
            "<strong>Best for overweight indoor cats:</strong> Active play toys (wand toys, laser pointers with physical 'catch' endings) that encourage movement and calorie burn",
            "<strong>Best for anxious indoor cats:</strong> Predictable, gentle toys like slow-moving puzzle feeders rather than erratic electronic toys that may startle",
            "<strong>Best for senior indoor cats:</strong> Low-intensity puzzle feeders and scent-based enrichment that engage the mind without demanding physical agility",
            "<strong>Best on a budget:</strong> Rotating a small toy collection weekly creates novelty without constant purchasing — cats prefer variety over quantity"
        ]
    },
}

PROS_CONS_BLOCKS = {
    # Batch 1: Product guides
    3956: {
        "advantages": [
            "Regular play with appropriate toys reduces destructive behaviour and boredom-related issues",
            "Different toy types (fetch, tug, puzzle) address different aspects of your dog's physical and mental needs",
            "Quality toys can last months, making them a cost-effective enrichment investment"
        ],
        "considerations": [
            "No toy is truly indestructible — all toys need regular inspection for wear and loose parts",
            "Some dogs lose interest in toys quickly, so buying in bulk before testing preferences can waste money",
            "Supervised play is recommended for all toys, especially those with squeakers or stuffing"
        ]
    },
    3957: {
        "advantages": [
            "Designed to withstand sustained chewing from powerful jaws, reducing choking and ingestion risks",
            "Saves money long-term compared to constantly replacing standard toys",
            "Provides a safe outlet for natural chewing instincts that might otherwise target furniture or shoes"
        ],
        "considerations": [
            "Tougher materials often mean harder textures, which some dogs find less appealing than softer alternatives",
            "Even 'indestructible' rated toys can break down over time — regular inspection remains essential",
            "Heavy-duty toys may be too firm for puppies or senior dogs with dental sensitivity"
        ]
    },
    3959: {
        "advantages": [
            "Mental stimulation from puzzle toys can tire dogs as effectively as physical exercise",
            "Helps reduce separation anxiety by providing engaging solo activities",
            "Slows down fast eaters when used as feeding tools, improving digestion"
        ],
        "considerations": [
            "Some dogs become frustrated with puzzles that are too difficult — start with easy levels and progress gradually",
            "Battery-operated interactive toys have ongoing replacement costs and may malfunction",
            "Puzzle toys with small removable parts require supervision to prevent swallowing hazards"
        ]
    },
    3996: {
        "advantages": [
            "A comfortable bed reduces joint pressure and supports musculoskeletal health throughout your dog's life",
            "Gives your dog a defined resting space, which supports routine and can reduce anxiety",
            "Machine-washable covers make hygiene maintenance straightforward compared to sofas or carpets"
        ],
        "considerations": [
            "Dogs may take time to transition to a new bed, especially if they're used to sleeping on furniture",
            "Foam quality varies significantly across price points — cheap foam compresses quickly and loses support",
            "Sizing errors are common; measuring your dog's full stretched-out length before purchasing prevents returns"
        ]
    },
    4004: {
        "advantages": [
            "Memory foam conforms to body shape, distributing weight evenly and reducing pressure on arthritic joints",
            "Can noticeably improve mobility and comfort in dogs with diagnosed joint conditions",
            "Veterinarians frequently recommend orthopaedic beds as part of a comprehensive joint care plan"
        ],
        "considerations": [
            "Genuine orthopaedic foam is heavier and more expensive than standard polyester fill beds",
            "Memory foam retains heat, which can be uncomfortable for dogs in warm environments",
            "Not all beds marketed as 'orthopaedic' contain true memory foam — check material specifications carefully"
        ]
    },
    4011: {
        "advantages": [
            "Provides measurable temperature reduction for dogs who struggle to regulate body heat",
            "Essential for brachycephalic breeds and double-coated dogs during warm months",
            "Elevated designs also keep dogs off hot surfaces and improve air circulation"
        ],
        "considerations": [
            "Gel-based cooling mats have a limited active cooling period (typically 1-3 hours) before needing to recharge",
            "Some dogs may chew or puncture gel cooling pads, creating a mess and potential ingestion risk",
            "Not a substitute for shade, fresh water, and avoiding exercise during peak heat"
        ]
    },
    4018: {
        "advantages": [
            "Establishes a positive sleeping routine from the start, which supports housetraining and crate training",
            "Waterproof options handle inevitable puppy accidents without permanent damage",
            "Provides warmth and security during the stressful transition from litter to new home"
        ],
        "considerations": [
            "Puppies will likely outgrow their first bed within 3-4 months, so investing heavily in a first bed rarely pays off",
            "Teething puppies may destroy beds regardless of 'chew-resistant' claims — expect some attrition",
            "Overly soft beds may not provide the firm support growing joints need during early development"
        ]
    },
    4027: {
        "advantages": [
            "Harnesses distribute pressure across the chest and body, eliminating strain on the neck and trachea",
            "A well-fitted harness gives you more control with less effort, especially with pulling dogs",
            "Modern designs combine functionality with comfort, making them suitable for all-day wear"
        ],
        "considerations": [
            "Poorly fitted harnesses can cause chafing, restrict natural gait, or allow escape — proper measurement is critical",
            "Some dogs initially resist harness fitting and need gradual positive introduction",
            "Front-clip harnesses can alter natural movement patterns if used as a permanent solution rather than a training tool"
        ]
    },
    4034: {
        "advantages": [
            "Front-clip designs mechanically redirect pulling energy without any pain or discomfort to the dog",
            "Effective for most dogs within the first few uses, providing immediate improvement on walks",
            "Paired with reward-based training, no-pull harnesses accelerate loose-lead walking progress"
        ],
        "considerations": [
            "A no-pull harness manages pulling but doesn't train your dog — loose-lead training should continue alongside use",
            "Front-clip designs can shift to one side if improperly adjusted, causing an uneven gait",
            "Some muscular or barrel-chested dogs require specific harness shapes that standard no-pull designs don't accommodate"
        ]
    },
    4042: {
        "advantages": [
            "A quality lead is the single most important piece of walking equipment for safety and control",
            "Different lead types (standard, long-line, hands-free) suit different training stages and activities",
            "Fixed-length leads provide consistent, predictable handling compared to retractable alternatives"
        ],
        "considerations": [
            "Retractable leads can encourage pulling and create dangerous situations if the mechanism locks unexpectedly",
            "Very long training leads require open space and awareness to avoid tangling around objects or people",
            "Lead material (nylon, leather, rope) affects grip comfort, especially in wet conditions"
        ]
    },
}

ROUTINE_BLOCKS = {
    # Batch 2: Educational/care guides
    4057: {
        "title": "Quick Grooming Routine Checklist",
        "items": [
            "Daily: Quick brush-through for long or curly coats (2-3 minutes prevents matting)",
            "Weekly: Full brushing session, ear check (look for redness or odour), and paw pad inspection",
            "Fortnightly: Nail check and trim if needed (nails shouldn't click on hard floors)",
            "Monthly: Full bath with appropriate shampoo, followed by thorough drying and coat inspection",
            "Every 3-6 months: Professional grooming session for breeds that require clipping or hand-stripping"
        ]
    },
    4064: {
        "title": "Quick Brushing Routine Checklist",
        "items": [
            "Daily: 2-3 minutes with a slicker brush for long, curly, or double-coated breeds",
            "Weekly: Thorough brush for short-coated breeds; check for mats behind ears and under legs on long coats",
            "During shedding season: Daily deshedding sessions with an undercoat rake for double-coated breeds",
            "Monthly: Clean your brushes by removing accumulated hair and washing in warm soapy water",
            "Every 3-6 months: Assess brush condition and replace if bristles are bent, missing, or ineffective"
        ]
    },
    4071: {
        "title": "Quick Bathing Routine Checklist",
        "items": [
            "Before each bath: Brush out mats and tangles thoroughly — water tightens mats and makes them harder to remove",
            "During bath: Use lukewarm water, lather shampoo working from neck to tail, avoid eyes and inner ears",
            "After bath: Rinse thoroughly (residual shampoo causes irritation), towel dry, then blow-dry on a cool setting if tolerated",
            "Every 4-6 weeks: Full bath for most dogs (more frequent for dogs with skin conditions, as vet-directed)",
            "Ongoing: Store shampoo at room temperature and check expiry dates — expired products can irritate skin"
        ]
    },
    4078: {
        "title": "Quick Nail Care Routine Checklist",
        "items": [
            "Weekly: Check nail length — if you hear clicking on hard floors, it's time for a trim",
            "Every 2-3 weeks: Trim or grind nails, removing small amounts at a time to avoid the quick",
            "After each trim: Reward your dog immediately to build positive associations with nail care",
            "Monthly: Inspect dewclaws (if present) which don't wear down naturally and can curl into the pad",
            "Ongoing: Keep styptic powder on hand for accidental quick cuts — it stops bleeding within seconds"
        ]
    },
    4089: {
        "title": "Quick Health Maintenance Checklist",
        "items": [
            "Daily: Check food and water intake, energy level, and general behaviour for any changes",
            "Weekly: Quick body check — feel for lumps, check eyes, ears, teeth, and paws",
            "Monthly: Flea and worming treatments as per your vet's prevention schedule",
            "Every 6 months: Weigh your dog and adjust food portions if needed to maintain healthy body condition",
            "Annually: Full veterinary health check, vaccination boosters, and dental assessment (twice yearly for dogs over 7)"
        ]
    },
    4096: {
        "title": "Quick Dental Care Routine Checklist",
        "items": [
            "Daily: Brush teeth with canine enzymatic toothpaste (even 30 seconds makes a measurable difference)",
            "Weekly: Offer a VOHC-approved dental chew to supplement brushing and disrupt plaque formation",
            "Monthly: Lift lips and inspect gums for redness, swelling, or bleeding — early signs of periodontal disease",
            "Every 6 months: Check for bad breath changes, broken teeth, or reluctance to eat hard food",
            "Annually: Professional dental check during your dog's routine veterinary examination"
        ]
    },
    4103: {
        "title": "Quick Flea Prevention Routine Checklist",
        "items": [
            "Monthly: Apply spot-on treatment or administer oral flea prevention on schedule (set a phone reminder)",
            "Weekly: Check your dog for fleas using a fine-toothed flea comb, especially around the neck and tail base",
            "Fortnightly: Wash pet bedding at 60°C to kill flea eggs and larvae in the sleeping environment",
            "Seasonally: Vacuum carpets, furniture, and skirting boards thoroughly — 95% of fleas live in the environment, not on pets",
            "Year-round: Continue flea prevention through winter — heated homes allow fleas to survive year-round in the UK"
        ]
    },
    4110: {
        "title": "Quick Joint Care Routine Checklist",
        "items": [
            "Daily: Administer joint supplement at the same time each day (consistency improves absorption and habit formation)",
            "Weekly: Observe your dog's gait during walks — stiffness after rest or reluctance to jump may indicate joint discomfort",
            "Monthly: Weigh your dog and adjust diet if needed — excess weight is the single biggest modifiable risk factor for joint disease",
            "Every 3-6 months: Review supplement effectiveness with your vet and adjust dosage or formulation if needed",
            "Annually: Veterinary joint assessment, especially for breeds predisposed to hip dysplasia, elbow dysplasia, or arthritis"
        ]
    },
    4118: {
        "title": "Quick Training Routine Checklist",
        "items": [
            "Daily: Two to three short training sessions (5-10 minutes each) — frequent, brief sessions outperform occasional long ones",
            "Weekly: Practise known commands in a new environment to build reliable generalisation",
            "Monthly: Assess progress and introduce one new behaviour or increase the difficulty of existing commands",
            "Every 3-6 months: Consider a group training class or workshop to maintain socialisation and introduce structured challenges",
            "Ongoing: Keep high-value treats accessible for capturing spontaneous good behaviour throughout the day"
        ]
    },
    4132: {
        "title": "Quick Puppy Training Timeline Checklist",
        "items": [
            "Weeks 8-10: Focus on name recognition, housetraining routine, and gentle handling exercises",
            "Weeks 10-12: Begin basic cue training (sit, look at me), continue socialisation with new people and surfaces",
            "Weeks 12-16: Close of the critical socialisation window — prioritise positive exposure to varied environments, sounds, and other vaccinated dogs",
            "Months 4-6: Strengthen recall, introduce lead walking, and begin impulse control exercises (wait, leave it)",
            "Months 6-12: Maintain consistency through the adolescent phase — expect some regression and respond with patience, not frustration"
        ]
    },
}

# Batch 3 cat/mixed also get routines where appropriate
ROUTINE_BLOCKS_EXTRA = {
    4174: {
        "title": "Quick Play Routine Checklist",
        "items": [
            "Daily: Two interactive play sessions of 10-15 minutes each (morning and evening match natural hunting rhythms)",
            "Weekly: Rotate toy selection to maintain novelty — store unused toys out of sight and reintroduce them fresh",
            "Monthly: Inspect all toys for wear, loose parts, or fraying strings that could pose ingestion risks",
            "Every 3-6 months: Introduce a completely new toy type to assess evolving play preferences",
            "Ongoing: End each play session with a 'catch' moment and a small treat to simulate a successful hunt"
        ]
    },
    4286: {
        "title": "Quick Scratching Post Maintenance Checklist",
        "items": [
            "Daily: Check post stability — a wobbly post discourages use and can tip onto your cat",
            "Weekly: Vacuum around the base to remove sisal or cardboard debris",
            "Monthly: Inspect sisal wrapping for fraying or looseness and re-secure if needed",
            "Every 3-6 months: Assess whether the post still meets your cat's size — growing cats may need a taller replacement",
            "Ongoing: Sprinkle catnip on the post periodically to maintain interest, especially if your cat has started scratching elsewhere"
        ]
    },
    4314: {
        "title": "Quick Litter Tray Maintenance Checklist",
        "items": [
            "Daily: Scoop clumps and solid waste at least once (ideally twice for multi-cat households)",
            "Weekly: Top up litter to maintain a depth of 5-7cm for effective clumping and digging",
            "Fortnightly: Full litter change and tray wash with warm water and mild unscented soap",
            "Monthly: Inspect tray for scratches or cracks where bacteria can harbour — replace heavily scratched trays",
            "Every 6-12 months: Replace the entire tray, as plastic absorbs odours over time regardless of cleaning"
        ]
    },
    4321: {
        "title": "Quick Litter Management Checklist",
        "items": [
            "Daily: Scoop all clumps and solids — daily scooping extends the life of clumping litter significantly",
            "Weekly: Stir remaining litter to distribute moisture evenly and check for odour breakthrough",
            "Fortnightly: Complete litter change for non-clumping types; top-up for clumping types",
            "Monthly: Deep clean tray during a full litter change — hot water and mild soap only, avoid strong disinfectants",
            "Ongoing: Store unused litter in a cool, dry place — moisture-compromised litter clumps poorly and controls odour less effectively"
        ]
    },
    4335: {
        "title": "Quick Waste Disposal Routine Checklist",
        "items": [
            "Daily: Scoop waste into lined disposal bin or sealed bag immediately after scooping the tray",
            "Weekly: Empty disposal bin and clean with mild disinfectant to prevent odour build-up in the bin itself",
            "Fortnightly: Check disposal bag supply and restock before running out (interrupted routines lead to odour issues)",
            "Monthly: Clean the area around the disposal bin and litter tray to prevent bacterial transfer",
            "Ongoing: Never flush cat litter — even 'flushable' varieties can damage plumbing and introduce parasites into waterways"
        ]
    },
}

PROS_CONS_BATCH3 = {
    4174: {
        "advantages": [
            "Regular play reduces behavioural problems like aggression, overeating, and furniture destruction in indoor cats",
            "Interactive toys strengthen the bond between cat and owner through shared activity",
            "A well-exercised cat is calmer, sleeps better, and maintains healthier body weight"
        ],
        "considerations": [
            "Cats have short play attention spans (10-15 minutes typically) — don't expect extended sessions",
            "Battery-operated toys need supervision and have ongoing battery replacement costs",
            "Some cats are highly specific about toy preferences — expect some trial and error initially"
        ]
    },
    4181: {
        "advantages": [
            "Wand and puzzle toys engage natural hunting instincts that purely solo toys cannot replicate",
            "Interactive play provides both mental stimulation and physical exercise simultaneously",
            "Puzzle feeders slow down eating, improving digestion for cats who eat too quickly"
        ],
        "considerations": [
            "Wand toys require your active participation — they're not set-and-forget enrichment",
            "String and ribbon attachments can be ingested if left unsupervised, causing serious intestinal problems",
            "Electronic interactive toys vary widely in quality — cheaper models may stop working quickly"
        ]
    },
    4188: {
        "advantages": [
            "Catnip provides safe, natural stimulation that encourages active play and exercise",
            "Responses are self-limiting — cats naturally lose interest after 10-15 minutes and need a 30-minute reset",
            "No risk of addiction or dependency; catnip is completely safe and non-toxic for cats"
        ],
        "considerations": [
            "Approximately 30-40% of cats show no response to catnip at all (it's genetically determined)",
            "Catnip loses potency over time — dried catnip should be stored sealed and replaced every few months",
            "A small percentage of cats become briefly aggressive during catnip sessions — separate cats in multi-cat homes if this occurs"
        ]
    },
    4286: {
        "advantages": [
            "Scratching posts protect furniture by redirecting natural scratching behaviour to an appropriate surface",
            "Vertical scratching provides stretching that maintains healthy claws, muscles, and tendons",
            "Multi-level cat trees combine scratching, climbing, and resting in a single piece of furniture"
        ],
        "considerations": [
            "A post that's too short, too light, or poorly placed will be ignored in favour of furniture",
            "Sisal wrapping wears out and needs replacing — budget for maintenance or replacement over time",
            "Cats develop surface and orientation preferences early — some prefer horizontal scratching and will ignore vertical posts"
        ]
    },
    4307: {
        "advantages": [
            "Uses vertical wall space efficiently, ideal for small homes where floor space is limited",
            "Wall-mounted scratchers can be positioned at the exact height your cat naturally stretches to",
            "Can form part of a wall-mounted enrichment system with shelves and perches"
        ],
        "considerations": [
            "Requires wall drilling in most cases, which may not be suitable for renters",
            "Installation must be secure — a scratcher that moves or falls will frighten your cat away permanently",
            "Limited scratching surface area compared to large freestanding posts or cat trees"
        ]
    },
    4300: {
        "advantages": [
            "Extremely affordable, making them accessible for any budget",
            "Lightweight and easy to reposition as you determine your cat's preferred scratching locations",
            "Recyclable and often made from recycled materials — the most eco-friendly scratching option"
        ],
        "considerations": [
            "Wear out faster than sisal or wood alternatives — expect replacement every 2-4 months with regular use",
            "Create cardboard debris that needs regular vacuuming around the scratching area",
            "Some cats prefer the firmer resistance of sisal rope and find cardboard too soft or unsatisfying"
        ]
    },
    4314: {
        "advantages": [
            "A clean, appropriate litter tray is the foundation of reliable indoor toileting behaviour",
            "The right tray size and style reduces litter tracking and makes cleaning more efficient",
            "Covered trays contain odour and provide privacy that some cats prefer"
        ],
        "considerations": [
            "Covered trays can trap odour inside, making the tray unpleasant for the cat even if owners can't smell it",
            "Self-cleaning trays have mechanical parts that can malfunction and may frighten noise-sensitive cats",
            "The 'one tray per cat plus one extra' guideline means multiple trays for multi-cat households, which requires space"
        ]
    },
    4321: {
        "advantages": [
            "Choosing the right litter type significantly reduces odour, tracking, and daily maintenance effort",
            "Clumping litters make waste removal faster and more hygienic with daily scooping",
            "Natural litter alternatives are better for the environment and avoid the dust associated with clay"
        ],
        "considerations": [
            "Cats can be highly particular about litter texture and scent — sudden changes may cause tray avoidance",
            "Scented litters may appeal to owners but can deter cats with sensitive noses",
            "Natural litters (wood, paper, corn) may not clump as tightly as clay, requiring more frequent full changes"
        ]
    },
    4335: {
        "advantages": [
            "A dedicated disposal system controls odour far better than standard household bins",
            "Sealed disposal reduces bacterial spread in the home, particularly important for immunocompromised owners",
            "Streamlines the daily scooping routine, making consistent tray hygiene more likely"
        ],
        "considerations": [
            "Proprietary refill cartridges for some disposal systems add ongoing costs",
            "Disposal bins still need regular cleaning themselves to prevent internal odour build-up",
            "Biodegradable bag options exist but cost more than standard plastic alternatives"
        ]
    },
    4406: {
        "advantages": [
            "Specifically designed for indoor cats who lack the natural stimulation of an outdoor environment",
            "Addresses the leading causes of indoor cat behavioural problems: boredom, inactivity, and under-stimulation",
            "Automated options provide enrichment during owner absence, reducing loneliness-related stress"
        ],
        "considerations": [
            "No toy fully replaces human interactive play — aim for at least two dedicated play sessions daily",
            "Electronic toys can be noisy and may disturb cats (or owners) if activated at unexpected times",
            "Over-reliance on automated toys without varying the enrichment can lead to habituation and disinterest"
        ]
    },
}


def build_suitability_html(data):
    """Build HTML for a suitability block."""
    items_html = "\n".join(f"<li>{item}</li>" for item in data["items"])
    return f"""

<h3 class="wp-block-heading">{data["title"]}</h3>

<ul class="wp-block-list">
{items_html}
</ul>

"""


def build_pros_cons_html(data):
    """Build HTML for a pros/cons block."""
    adv_html = "\n".join(f"<li>{a}</li>" for a in data["advantages"])
    con_html = "\n".join(f"<li>{c}</li>" for c in data["considerations"])
    return f"""

<h3 class="wp-block-heading">Key Considerations</h3>

<div class="wp-block-columns">
<div class="wp-block-column">

<h4 class="wp-block-heading">Advantages</h4>

<ul class="wp-block-list">
{adv_html}
</ul>

</div>
<div class="wp-block-column">

<h4 class="wp-block-heading">Things to Watch</h4>

<ul class="wp-block-list">
{con_html}
</ul>

</div>
</div>

"""


def build_routine_html(data):
    """Build HTML for a routine/checklist block."""
    items_html = "\n".join(f"<li>{item}</li>" for item in data["items"])
    return f"""

<h3 class="wp-block-heading">{data["title"]}</h3>

<ul class="wp-block-list">
{items_html}
</ul>

"""


def fetch_post(post_id):
    """Fetch post content via WP API."""
    url = f"{WP_API}/posts/{post_id}?context=edit&_fields=id,title,content"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        return data
    except json.JSONDecodeError:
        return None


def update_post(post_id, new_content):
    """Update post content via WP API using temp file."""
    payload = json.dumps({"content": new_content})
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(payload)
        tmpfile = f.name

    try:
        url = f"{WP_API}/posts/{post_id}"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmpfile}",
             url],
            capture_output=True, text=True,
            timeout=30
        )
        if result.returncode != 0:
            return False, f"curl error: {result.stderr}"

        try:
            resp = json.loads(result.stdout)
            if "id" in resp:
                return True, "OK"
            else:
                return False, f"API error: {result.stdout[:300]}"
        except json.JSONDecodeError:
            return False, f"Invalid JSON response: {result.stdout[:300]}"
    finally:
        os.unlink(tmpfile)


def has_section(content, markers):
    """Check if content already has any of the given section markers."""
    for marker in markers:
        if marker in content:
            return True
    return False


def insert_before_sources(content, new_blocks):
    """Insert new content blocks before the Sources and Further Reading section."""
    # Look for the HR + Sources pattern
    sources_markers = [
        '<h3 class="wp-block-heading">Sources and Further Reading</h3>',
        '<h3 class="wp-block-heading">Sources and Further Reading',
        'Sources and Further Reading</h3>',
    ]

    insert_point = -1
    for marker in sources_markers:
        idx = content.find(marker)
        if idx >= 0:
            # Look for the HR separator before sources
            hr_idx = content.rfind('<hr', max(0, idx - 200), idx)
            if hr_idx >= 0:
                insert_point = hr_idx
            else:
                insert_point = idx
            break

    if insert_point < 0:
        # Fallback: look for "Related Guides" section as alternative anchor
        related_markers = [
            '<h2 class="wp-block-heading">Related Guides</h2>',
            'Related Guides</h2>',
        ]
        for marker in related_markers:
            idx = content.find(marker)
            if idx >= 0:
                insert_point = idx
                break

    if insert_point < 0:
        # Last resort: append before closing content
        insert_point = len(content)

    combined_block = "\n".join(new_blocks)
    new_content = content[:insert_point] + combined_block + "\n\n" + content[insert_point:]
    return new_content


def process_post(post_id, batch_num):
    """Process a single post: fetch, determine blocks, insert, update."""
    post = fetch_post(post_id)
    if not post:
        return {"id": post_id, "title": "FETCH_ERROR", "suitability": False,
                "pros_cons": False, "routine": False, "status": "FETCH_ERROR"}

    title = html.unescape(post["title"]["raw"])
    content = post["content"]["raw"]

    # Determine which blocks to add
    blocks_to_insert = []
    suitability_added = False
    pros_cons_added = False
    routine_added = False

    existing_markers = ["Quick Suitability", "Key Considerations", "Quick Routine",
                        "Quick Grooming Routine", "Quick Brushing Routine",
                        "Quick Bathing Routine", "Quick Nail Care Routine",
                        "Quick Health Maintenance", "Quick Dental Care Routine",
                        "Quick Flea Prevention", "Quick Joint Care Routine",
                        "Quick Training Routine", "Quick Puppy Training Timeline",
                        "Quick Play Routine", "Quick Scratching Post",
                        "Quick Litter Tray", "Quick Litter Management",
                        "Quick Waste Disposal", "Advantages", "Things to Watch"]

    if has_section(content, existing_markers):
        return {"id": post_id, "title": title, "suitability": False,
                "pros_cons": False, "routine": False, "status": "ALREADY_HAS_SECTIONS"}

    # Add suitability block if available
    if post_id in SUITABILITY_BLOCKS:
        blocks_to_insert.append(build_suitability_html(SUITABILITY_BLOCKS[post_id]))
        suitability_added = True

    # Add pros/cons block if available
    if post_id in PROS_CONS_BLOCKS:
        blocks_to_insert.append(build_pros_cons_html(PROS_CONS_BLOCKS[post_id]))
        pros_cons_added = True
    if post_id in PROS_CONS_BATCH3:
        blocks_to_insert.append(build_pros_cons_html(PROS_CONS_BATCH3[post_id]))
        pros_cons_added = True

    # Add routine block if available
    if post_id in ROUTINE_BLOCKS:
        blocks_to_insert.append(build_routine_html(ROUTINE_BLOCKS[post_id]))
        routine_added = True
    if post_id in ROUTINE_BLOCKS_EXTRA:
        blocks_to_insert.append(build_routine_html(ROUTINE_BLOCKS_EXTRA[post_id]))
        routine_added = True

    if not blocks_to_insert:
        return {"id": post_id, "title": title, "suitability": False,
                "pros_cons": False, "routine": False, "status": "NO_BLOCKS_DEFINED"}

    # Insert blocks before Sources section
    new_content = insert_before_sources(content, blocks_to_insert)

    # Update via API
    success, msg = update_post(post_id, new_content)

    status = "OK" if success else f"UPDATE_ERROR: {msg}"

    return {
        "id": post_id,
        "title": title,
        "suitability": suitability_added,
        "pros_cons": pros_cons_added,
        "routine": routine_added,
        "status": status
    }


def main():
    # All 30 post IDs in batches
    batch1 = [3956, 3957, 3959, 3996, 4004, 4011, 4018, 4027, 4034, 4042]
    batch2 = [4057, 4064, 4071, 4078, 4089, 4096, 4103, 4110, 4118, 4132]
    batch3 = [4174, 4181, 4188, 4286, 4307, 4300, 4314, 4321, 4335, 4406]

    all_ids = batch1 + batch2 + batch3

    # Initialize CSV log
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "suitability_added", "pros_cons_added", "routine_added", "status"])

    results = []
    total = len(all_ids)

    for i, post_id in enumerate(all_ids):
        batch_label = "Batch 1" if post_id in batch1 else ("Batch 2" if post_id in batch2 else "Batch 3")
        print(f"[{i+1}/{total}] Processing post {post_id} ({batch_label})...", flush=True)

        result = process_post(post_id, batch_label)
        results.append(result)

        # Write to CSV
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                result["id"],
                result["title"],
                result["suitability"],
                result["pros_cons"],
                result["routine"],
                result["status"]
            ])

        print(f"  -> {result['status']} | Suitability: {result['suitability']} | "
              f"Pros/Cons: {result['pros_cons']} | Routine: {result['routine']}", flush=True)

        # Delay between API calls
        if i < total - 1:
            time.sleep(0.5)

    # Summary
    print("\n" + "=" * 70)
    print("BUYER INTENT BLOCKS — SUMMARY")
    print("=" * 70)

    ok_count = sum(1 for r in results if r["status"] == "OK")
    suit_count = sum(1 for r in results if r["suitability"])
    pc_count = sum(1 for r in results if r["pros_cons"])
    rt_count = sum(1 for r in results if r["routine"])

    print(f"Total posts processed: {total}")
    print(f"Successfully updated:  {ok_count}")
    print(f"Suitability blocks:    {suit_count}")
    print(f"Pros/Cons blocks:      {pc_count}")
    print(f"Routine blocks:        {rt_count}")

    errors = [r for r in results if r["status"] not in ("OK", "ALREADY_HAS_SECTIONS")]
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  Post {e['id']}: {e['status']}")

    print(f"\nLog saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()
