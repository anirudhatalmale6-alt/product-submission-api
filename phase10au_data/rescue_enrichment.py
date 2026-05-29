#!/usr/bin/env python3
"""
Phases 10AR/10AS/10AT/10AU – Cluster Rescue Enrichment for Puppy Care & Dog Health
Adds: Glossary/Key Terms, Common Mistakes, When to Seek Help, Beginner Recommendations,
      At a Glance, Key Takeaways blocks to each post where missing.
"""

import subprocess, json, time, csv, re, sys, os, tempfile

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10au_data"
LOG_FILE = os.path.join(DATA_DIR, "rescue_puppy_care_dog_health.csv")
DELAY = 2

# Post IDs by cluster
PUPPY_CARE_IDS = [5508, 5417, 3960, 7337, 7338, 7339, 7340, 7341, 7170]
DOG_HEALTH_IDS = [5520, 4568, 4110, 4103, 4096, 4089, 7169]

# ─── Block Templates ────────────────────────────────────────────────

def glossary_block(terms_html):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f8fafc"}},"border":{{"radius":"6px","width":"1px","color":"#e2e8f0"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:6px;background-color:#f8fafc;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">Key Terms</h4><!-- /wp:heading -->
<!-- wp:list --><ul class="wp-block-list">{terms_html}</ul><!-- /wp:list -->
</div>
<!-- /wp:group -->'''

def common_mistakes_block(items_html):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fef2f2"}},"border":{{"radius":"6px","width":"1px","color":"#fecaca"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fecaca;border-width:1px;border-radius:6px;background-color:#fef2f2;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">Common Mistakes to Avoid</h4><!-- /wp:heading -->
<!-- wp:list --><ul class="wp-block-list">{items_html}</ul><!-- /wp:list -->
</div>
<!-- /wp:group -->'''

def seek_help_block(items_html):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fffbeb"}},"border":{{"radius":"6px","width":"1px","color":"#fde68a"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fde68a;border-width:1px;border-radius:6px;background-color:#fffbeb;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">When to Seek Professional Help</h4><!-- /wp:heading -->
<!-- wp:paragraph --><p>Contact your vet or use the <a href="https://www.pdsa.org.uk/" rel="nofollow noopener" target="_blank">PDSA</a> or <a href="https://www.rspca.org.uk/" rel="nofollow noopener" target="_blank">RSPCA</a> helplines if you notice any of the following:</p><!-- /wp:paragraph -->
<!-- wp:list --><ul class="wp-block-list">{items_html}</ul><!-- /wp:list -->
</div>
<!-- /wp:group -->'''

def beginner_recs_block(items_html):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#eff6ff"}},"border":{{"radius":"6px","width":"1px","color":"#bfdbfe"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#bfdbfe;border-width:1px;border-radius:6px;background-color:#eff6ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">Beginner Recommendations</h4><!-- /wp:heading -->
<!-- wp:list --><ul class="wp-block-list">{items_html}</ul><!-- /wp:list -->
</div>
<!-- /wp:group -->'''

def at_a_glance_block(items_html):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#eef2ff"}},"border":{{"radius":"6px","width":"1px","color":"#c7d2fe"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#c7d2fe;border-width:1px;border-radius:6px;background-color:#eef2ff;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">At a Glance</h4><!-- /wp:heading -->
<!-- wp:list --><ul class="wp-block-list">{items_html}</ul><!-- /wp:list -->
</div>
<!-- /wp:group -->'''

def key_takeaways_block(items_html):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f0fdf4"}},"border":{{"radius":"6px","width":"1px","color":"#bbf7d0"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#bbf7d0;border-width:1px;border-radius:6px;background-color:#f0fdf4;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">Key Takeaways</h4><!-- /wp:heading -->
<!-- wp:list --><ul class="wp-block-list">{items_html}</ul><!-- /wp:list -->
</div>
<!-- /wp:group -->'''


# ─── Content Data per Post ───────────────────────────────────────────

CONTENT_DATA = {
    # ═══════════════════════════════════════════════════════════════
    # PUPPY CARE CLUSTER
    # ═══════════════════════════════════════════════════════════════
    5508: {
        "cluster": "Puppy Care",
        "glossary": [
            ("<strong>Socialisation window</strong>", "The critical period between roughly 3 and 14 weeks of age when puppies are most receptive to new experiences, people, and environments."),
            ("<strong>Neonatal period</strong>", "The first two weeks of life when puppies are blind, deaf, and entirely dependent on their mother."),
            ("<strong>Transitional period</strong>", "Weeks two to four, when a puppy’s eyes and ears open and they begin to interact with littermates."),
            ("<strong>Fear period</strong>", "A developmental phase (typically around 8–11 weeks and again at 6–8 months) when puppies are particularly sensitive to frightening experiences."),
            ("<strong>Positive reinforcement</strong>", "A training approach that rewards desired behaviour with treats, praise, or play, encouraging the puppy to repeat it."),
            ("<strong>Juvenile period</strong>", "The stage from roughly 3 to 6 months when adult teeth emerge and independence grows."),
        ],
        "mistakes": [
            "<li><strong>Skipping early socialisation</strong> – Waiting until vaccinations are fully complete before exposing a puppy to any new experiences can mean missing the critical socialisation window entirely.</li>",
            "<li><strong>Expecting adult behaviour from a puppy</strong> – Puppies cannot hold their bladder for long or focus during extended training sessions. Keep expectations age-appropriate.</li>",
            "<li><strong>Using punishment-based methods</strong> – Shouting or physical correction during fear periods can cause lasting behavioural damage. Positive reinforcement is recommended by the RSPCA and Dogs Trust.</li>",
            "<li><strong>Inconsistent routine</strong> – Changing feeding, walking, and sleeping schedules frequently can increase anxiety and slow house training progress.</li>",
        ],
        "beginner": [
            "<li>Start socialisation safely by carrying your puppy to experience new sights, sounds, and people before full vaccination protection.</li>",
            "<li>Keep initial training sessions to 3–5 minutes and end on a positive note.</li>",
            "<li>Establish a consistent daily routine for feeding, toilet breaks, and sleep from day one.</li>",
            "<li>Register with a UK vet within the first week and ask about a puppy health plan covering vaccinations and flea/worm treatment.</li>",
        ],
        "at_a_glance": [
            "<li>Puppies pass through six developmental stages from birth to roughly 3 years of age.</li>",
            "<li>The socialisation window (3–14 weeks) is the most important period for shaping temperament.</li>",
            "<li>Each stage has specific physical, behavioural, and training milestones.</li>",
            "<li>Fear periods require extra patience – avoid overwhelming your puppy during these phases.</li>",
        ],
        "takeaways": [
            "<li>Understanding developmental stages helps you train and support your puppy at the right time.</li>",
            "<li>The socialisation period between 3 and 14 weeks is irreplaceable – prioritise safe, positive exposure.</li>",
            "<li>Patience during fear periods prevents long-term behavioural problems.</li>",
            "<li>Consistent routine, positive reinforcement, and early vet registration set the foundation for a well-adjusted adult dog.</li>",
        ],
    },
    5417: {
        "cluster": "Puppy Care",
        "glossary": [
            ("<strong>Recall training</strong>", "Teaching a puppy to return to you reliably when called, one of the most important safety commands."),
            ("<strong>Crate training</strong>", "Gradually teaching a puppy to feel safe and relaxed inside a crate, used for house training, travel, and providing a secure den."),
            ("<strong>House training</strong>", "The process of teaching a puppy to toilet outdoors or in a designated area rather than inside the home."),
            ("<strong>Teething phase</strong>", "The period between roughly 3 and 7 months when adult teeth replace baby teeth, often causing increased chewing."),
            ("<strong>Vaccination schedule</strong>", "The timetable of core and optional vaccines a puppy needs during their first year and beyond, as recommended by UK vets."),
            ("<strong>Microchipping</strong>", "A legal requirement in England, Scotland, and Wales: a small chip inserted under the skin containing the owner’s contact details."),
        ],
        "mistakes": None,  # Already has
        "beginner": [
            "<li>Create a checklist of essential supplies before bringing your puppy home: crate, lead, collar, age-appropriate food, and chew toys.</li>",
            "<li>Familiarise yourself with the key terms in this guide so you can communicate clearly with your vet and trainer.</li>",
            "<li>Join a local puppy socialisation class accredited by the APDT or the Kennel Club’s Good Citizen scheme.</li>",
            "<li>Download the PDSA’s free puppy care guide for a reliable UK-based reference.</li>",
        ],
        "at_a_glance": None,  # Already has
        "takeaways": None,  # Already has
        "seek_help": None,  # Already has
    },
    3960: {
        "cluster": "Puppy Care",
        "glossary": None,  # Already has
        "mistakes": None,  # Already has
        "seek_help": None,  # Already has
        "beginner": [
            "<li>Start with two or three different textures of toy (rope, rubber, fabric) and observe which your puppy prefers.</li>",
            "<li>Rotate toys weekly to maintain your puppy’s interest rather than giving everything at once.</li>",
            "<li>Supervise all play with new toys until you know your puppy’s chewing strength.</li>",
            "<li>Choose age-appropriate sizes – toys should be large enough that your puppy cannot swallow them.</li>",
        ],
        "at_a_glance": None,
        "takeaways": None,
    },
    7337: {
        "cluster": "Puppy Care",
        "glossary": [
            ("<strong>Core vaccine</strong>", "A vaccination considered essential for all puppies regardless of lifestyle, covering diseases such as distemper, parvovirus, adenovirus, and leptospirosis."),
            ("<strong>Non-core vaccine</strong>", "An optional vaccination recommended based on a puppy’s individual risk factors, such as kennel cough or rabies for travel."),
            ("<strong>Primary course</strong>", "The initial set of two vaccinations (typically at 6–8 weeks and 10–12 weeks) that establishes baseline immunity."),
            ("<strong>Booster vaccination</strong>", "A follow-up dose given at 12 months and then periodically to maintain protective immunity levels."),
            ("<strong>Titre testing</strong>", "A blood test measuring antibody levels, sometimes used to assess whether a booster is necessary for certain diseases."),
            ("<strong>Maternal antibodies</strong>", "Protective antibodies passed from mother to puppies via colostrum, which gradually wane over the first weeks of life."),
            ("<strong>Herd immunity</strong>", "The indirect protection that occurs when a high percentage of the dog population is vaccinated, reducing disease spread for all."),
        ],
        "mistakes": [
            "<li><strong>Delaying the first vaccination</strong> – Waiting beyond 8 weeks leaves puppies unprotected as maternal antibodies fade.</li>",
            "<li><strong>Assuming indoor puppies don’t need vaccines</strong> – Diseases like parvovirus can be carried indoors on shoes and clothing.</li>",
            "<li><strong>Skipping annual boosters</strong> – Protection from leptospirosis in particular requires yearly boosters to remain effective.</li>",
            "<li><strong>Confusing titre tests with full protection</strong> – Titre testing only covers some diseases and does not replace the leptospirosis booster.</li>",
            "<li><strong>Letting puppies socialise in public spaces too early</strong> – Full protection typically starts 1–2 weeks after the second vaccination.</li>",
        ],
        "seek_help": [
            "<li>Your puppy develops facial swelling, difficulty breathing, or hives within hours of vaccination.</li>",
            "<li>Lethargy, vomiting, or loss of appetite persists for more than 48 hours after a vaccination.</li>",
            "<li>A lump at the injection site grows larger or has not resolved after 3–4 weeks.</li>",
            "<li>Your puppy has diarrhoea containing blood at any point, especially if not yet fully vaccinated.</li>",
        ],
        "beginner": [
            "<li>Book your puppy’s first vaccination appointment as soon as possible after bringing them home – most vets recommend starting at 6–8 weeks.</li>",
            "<li>Keep your vaccination card safe; you will need it for boarding, daycare, and travel.</li>",
            "<li>Ask your vet about a puppy health plan that bundles vaccinations, flea treatment, and worming at a monthly cost.</li>",
            "<li>Carry your puppy to socialise before full vaccination – avoid ground contact in public areas but do not isolate them entirely.</li>",
        ],
        "at_a_glance": [
            "<li>UK puppies need a primary course of two vaccinations, usually at 6–8 weeks and 10–12 weeks.</li>",
            "<li>Core vaccines protect against distemper, parvovirus, adenovirus, and leptospirosis.</li>",
            "<li>Puppies can typically go outdoors 1–2 weeks after their second vaccination.</li>",
            "<li>Annual boosters are needed to maintain protection, especially against leptospirosis.</li>",
            "<li>Kennel cough and rabies vaccines are optional and depend on your puppy’s lifestyle.</li>",
        ],
        "takeaways": [
            "<li>Vaccinations are the most effective way to protect your puppy from serious, potentially fatal diseases.</li>",
            "<li>Follow the standard UK schedule: first jab at 6–8 weeks, second at 10–12 weeks, booster at 12 months.</li>",
            "<li>Do not skip leptospirosis boosters – protection wanes within a year.</li>",
            "<li>Socialisation and vaccination are not mutually exclusive – carry your puppy to experience the world safely before full protection.</li>",
            "<li>Keep vaccination records up to date and discuss any concerns with your vet.</li>",
        ],
    },
    7338: {
        "cluster": "Puppy Care",
        "glossary": [
            ("<strong>Puppy-proofing</strong>", "The process of making your home safe by removing or securing hazards before a puppy arrives."),
            ("<strong>Crate training</strong>", "Gradually teaching a puppy to feel comfortable in a crate that serves as a safe, den-like space."),
            ("<strong>Toxic plants</strong>", "Household and garden plants that are poisonous to dogs if ingested, including lilies, daffodils, and rhubarb leaves."),
            ("<strong>Chew deterrent spray</strong>", "A bitter-tasting spray applied to furniture, cables, or other items to discourage chewing."),
            ("<strong>Baby gate</strong>", "A barrier used to restrict a puppy’s access to certain rooms or staircases."),
            ("<strong>Positive reinforcement</strong>", "Rewarding desired behaviour to encourage a puppy to repeat it, the approach recommended by UK welfare organisations."),
        ],
        "mistakes": [
            "<li><strong>Only puppy-proofing one room</strong> – Puppies are curious and fast; every accessible room needs checking.</li>",
            "<li><strong>Leaving electrical cables exposed</strong> – Chewing live wires is one of the most common causes of serious injury in young puppies.</li>",
            "<li><strong>Overlooking toxic plants</strong> – Many common houseplants and garden flowers are poisonous to dogs. Check the Dogs Trust toxic plant list.</li>",
            "<li><strong>Relying solely on supervision</strong> – Even attentive owners cannot watch a puppy every second. Physical barriers and crate training are essential backups.</li>",
            "<li><strong>Forgetting garden hazards</strong> – Slug pellets, compost bins, unsecured fencing, and garden chemicals are all common outdoor dangers.</li>",
        ],
        "seek_help": [
            "<li>Your puppy has swallowed something they should not have (batteries, chocolate, medication, sharp objects).</li>",
            "<li>You notice signs of poisoning: excessive drooling, trembling, vomiting, or collapse. Call the RSPCA’s 24-hour helpline or your emergency vet.</li>",
            "<li>Your puppy has chewed an electrical cable and shows signs of burns, breathing difficulty, or loss of consciousness.</li>",
            "<li>Persistent anxiety, destructive behaviour, or self-harm when left alone may indicate separation anxiety and warrants professional guidance.</li>",
        ],
        "beginner": [
            "<li>Do a full sweep of each room at puppy height – get on your hands and knees to spot hazards you might miss standing up.</li>",
            "<li>Secure kitchen and bathroom bins with lids or place them behind closed doors.</li>",
            "<li>Store all cleaning products, medications, and chemicals in locked or high cupboards.</li>",
            "<li>Invest in two or three baby gates to manage access during the first few months.</li>",
            "<li>Keep the <a href=\"https://www.dogstrust.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">Dogs Trust</a> toxic plant list bookmarked for quick reference.</li>",
        ],
        "at_a_glance": [
            "<li>Puppy-proofing should cover every room your puppy can access, plus the garden.</li>",
            "<li>Electrical cables, toxic plants, small objects, and chemicals are the biggest indoor hazards.</li>",
            "<li>Baby gates and crate training help restrict access when you cannot supervise directly.</li>",
            "<li>Outdoor hazards include slug pellets, compost, unsecured fencing, and toxic garden plants.</li>",
        ],
        "takeaways": [
            "<li>Thorough puppy-proofing prevents the majority of accidental injuries in young dogs.</li>",
            "<li>Check every room at puppy eye-level and secure hazards before your puppy arrives.</li>",
            "<li>Combine physical barriers (gates, crate) with supervision for the safest environment.</li>",
            "<li>Keep emergency vet and poison helpline numbers saved in your phone.</li>",
        ],
    },
    7339: {
        "cluster": "Puppy Care",
        "glossary": [
            ("<strong>Sleep regression</strong>", "A temporary period when a puppy who previously slept well begins waking more frequently, often linked to developmental changes."),
            ("<strong>Circadian rhythm</strong>", "The internal body clock that gradually develops in puppies, helping them distinguish between day and night over the first few months."),
            ("<strong>Crate training</strong>", "Teaching a puppy to settle calmly in an enclosed crate, which supports safe sleeping and house training."),
            ("<strong>REM sleep</strong>", "Rapid eye movement sleep, the phase when dreaming occurs. Puppies spend more time in REM sleep than adult dogs."),
            ("<strong>Overtiredness</strong>", "A state where an excessively tired puppy becomes hyperactive, mouthy, or difficult to settle – often mistaken for excess energy."),
            ("<strong>Settling cue</strong>", "A consistent word or phrase used to signal that it is time to rest, helping build a predictable bedtime routine."),
        ],
        "mistakes": [
            "<li><strong>Assuming hyperactivity means more exercise is needed</strong> – Overtired puppies often become more frantic. The solution is usually more sleep, not more activity.</li>",
            "<li><strong>Allowing unlimited play without rest</strong> – Young puppies need 18–20 hours of sleep daily. Enforce nap times if your puppy will not settle independently.</li>",
            "<li><strong>Waking a sleeping puppy</strong> – Disturbing deep sleep interrupts important brain development. Let them wake naturally.</li>",
            "<li><strong>Changing the sleeping location frequently</strong> – Consistency helps puppies feel secure. Choose a spot and stick with it.</li>",
            "<li><strong>Ignoring signs of discomfort at night</strong> – A puppy that cries persistently may need a toilet break, be too cold, or be unwell. Rule out physical causes before applying “cry it out” advice.</li>",
        ],
        "seek_help": [
            "<li>Your puppy is lethargic and sleeping far more than expected for their age, with no interest in food or play.</li>",
            "<li>Persistent loud snoring or laboured breathing during sleep, which may indicate a respiratory issue.</li>",
            "<li>Sudden changes in sleep patterns combined with other symptoms such as vomiting, diarrhoea, or limping.</li>",
            "<li>Your puppy seems unable to settle at all despite a consistent routine, which may indicate pain or anxiety.</li>",
        ],
        "beginner": [
            "<li>Set up a quiet, warm sleeping area away from household noise before your puppy arrives.</li>",
            "<li>Use enforced naps: 1 hour awake, 2 hours resting is a good starting ratio for young puppies.</li>",
            "<li>Place a worn t-shirt in the crate so your scent provides comfort during the first few nights.</li>",
            "<li>Keep a brief toilet break in the middle of the night for puppies under 12 weeks, then gradually phase it out.</li>",
        ],
        "at_a_glance": [
            "<li>Puppies aged 8–10 weeks need 18–20 hours of sleep per day.</li>",
            "<li>Sleep needs decrease gradually, reaching around 12–14 hours by adulthood.</li>",
            "<li>Overtired puppies often become hyperactive rather than drowsy.</li>",
            "<li>A consistent sleeping location and bedtime routine help puppies settle faster.</li>",
        ],
        "takeaways": [
            "<li>Adequate sleep is essential for a puppy’s physical growth, immune function, and brain development.</li>",
            "<li>Most puppies need far more rest than new owners expect – enforced naps prevent overtiredness.</li>",
            "<li>Consistency in location, routine, and settling cues builds good sleep habits from the start.</li>",
            "<li>If sleep patterns change suddenly alongside other symptoms, consult your vet.</li>",
        ],
    },
    7340: {
        "cluster": "Puppy Care",
        "glossary": [
            ("<strong>Teething phase</strong>", "The period between roughly 3 and 7 months of age when a puppy’s 28 baby teeth are replaced by 42 adult teeth."),
            ("<strong>Deciduous teeth</strong>", "A puppy’s first set of teeth (baby teeth or milk teeth), which begin to fall out from around 12 weeks."),
            ("<strong>Retained deciduous tooth</strong>", "A baby tooth that fails to fall out when the adult tooth comes through, potentially causing alignment problems."),
            ("<strong>Teething ring</strong>", "A toy specifically designed for chewing during teething, often made from rubber or capable of being frozen for a soothing cooling effect."),
            ("<strong>Mouthing</strong>", "A normal puppy behaviour of gently biting or chewing on hands, clothing, or objects; distinct from aggressive biting."),
            ("<strong>Dental malocclusion</strong>", "Misalignment of the teeth or jaw that can result from retained baby teeth or genetics, sometimes requiring veterinary correction."),
        ],
        "mistakes": [
            "<li><strong>Giving hard bones or antlers to young puppies</strong> – These can fracture developing teeth. Choose softer chew toys suitable for teething puppies.</li>",
            "<li><strong>Punishing mouthing behaviour</strong> – Mouthing is normal during teething. Redirect to an appropriate chew toy rather than scolding.</li>",
            "<li><strong>Ignoring retained baby teeth</strong> – If a baby tooth has not fallen out by the time the adult tooth is visible alongside it, your vet may need to extract it.</li>",
            "<li><strong>Offering ice cubes that are too large</strong> – Small ice chips or frozen wet cloths are safer alternatives that still provide cooling relief.</li>",
            "<li><strong>Assuming all chewing is teething-related</strong> – Destructive chewing that persists well beyond 7 months may signal boredom, anxiety, or lack of enrichment.</li>",
        ],
        "seek_help": [
            "<li>Bleeding from the gums that does not stop within a few minutes or is excessive.</li>",
            "<li>Refusal to eat for more than 24 hours, which may indicate a mouth injury or retained tooth causing pain.</li>",
            "<li>A baby tooth and adult tooth visible side by side (retained deciduous tooth) – your vet should assess it.</li>",
            "<li>Swelling around the jaw or face, or a foul smell from the mouth that could indicate infection.</li>",
        ],
        "beginner": [
            "<li>Stock up on two or three teething-specific toys before teething begins (around 12 weeks).</li>",
            "<li>Freeze a clean, damp flannel for a cheap and effective soothing chew.</li>",
            "<li>Check your puppy’s mouth gently each week to monitor tooth development and spot retained teeth early.</li>",
            "<li>Keep redirect toys within arm’s reach around the house so you can swap them in when your puppy mouths furniture or hands.</li>",
        ],
        "at_a_glance": [
            "<li>Puppies begin losing baby teeth from around 12 weeks, with all 42 adult teeth usually in place by 7 months.</li>",
            "<li>Teething causes increased chewing, drooling, and sometimes minor gum bleeding.</li>",
            "<li>Frozen cloths and age-appropriate rubber toys provide the best relief.</li>",
            "<li>Retained baby teeth need veterinary attention to prevent alignment problems.</li>",
        ],
        "takeaways": [
            "<li>Teething is a normal developmental phase lasting from roughly 3 to 7 months of age.</li>",
            "<li>Redirect mouthing to appropriate toys rather than punishing natural behaviour.</li>",
            "<li>Avoid hard chews such as antlers or bones that can crack developing teeth.</li>",
            "<li>Monitor your puppy’s mouth regularly and see your vet if you spot retained baby teeth.</li>",
        ],
    },
    7341: {
        "cluster": "Puppy Care",
        "glossary": [
            ("<strong>Crate training</strong>", "Gradually teaching a puppy to view a crate as a safe, den-like retreat for sleeping and settling."),
            ("<strong>House training</strong>", "The process of teaching a puppy to toilet outdoors through consistent routine and positive reinforcement."),
            ("<strong>Socialisation window</strong>", "The critical period (3–14 weeks) when puppies are most receptive to new experiences and environments."),
            ("<strong>Settling in period</strong>", "The first one to two weeks in a new home when a puppy adjusts to unfamiliar surroundings, people, and routines."),
            ("<strong>Positive reinforcement</strong>", "Rewarding desired behaviour immediately so the puppy is more likely to repeat it."),
            ("<strong>Recall training</strong>", "Teaching a puppy to come back to you reliably when called, starting indoors before progressing to outdoor environments."),
        ],
        "mistakes": [
            "<li><strong>Overwhelming the puppy on day one</strong> – Too many visitors, too much handling, and too many new rooms can cause stress. Keep the first day calm and quiet.</li>",
            "<li><strong>Leaving the puppy alone too soon</strong> – Build up alone time gradually over days, not hours. Sudden isolation can trigger separation anxiety.</li>",
            "<li><strong>Inconsistent toilet routine</strong> – Take your puppy out after every meal, nap, and play session to the same spot. Inconsistency delays house training.</li>",
            "<li><strong>Punishing accidents indoors</strong> – Puppies cannot connect past accidents with punishment. Clean up calmly and reinforce outdoor toileting instead.</li>",
            "<li><strong>Skipping the first vet visit</strong> – A health check within the first week identifies any issues early and establishes your puppy’s vaccination schedule.</li>",
        ],
        "seek_help": [
            "<li>Your puppy refuses food for more than 24 hours or shows signs of dehydration (dry gums, sunken eyes, lethargy).</li>",
            "<li>Persistent diarrhoea or vomiting, especially in a young, unvaccinated puppy – contact your vet immediately.</li>",
            "<li>Extreme distress (continuous howling, self-harm, destructive behaviour) when left alone, even briefly.</li>",
            "<li>Limping, obvious pain, or any discharge from the eyes, nose, or ears after arriving home.</li>",
        ],
        "beginner": [
            "<li>Set up your puppy’s crate, bed, food, and water in a quiet area before they arrive.</li>",
            "<li>Plan to take at least two to three days off work for the settling-in period.</li>",
            "<li>Introduce one room at a time over the first few days rather than giving full house access immediately.</li>",
            "<li>Start a simple daily log noting feeding times, toilet breaks, and sleep patterns – this helps you and your vet spot patterns quickly.</li>",
        ],
        "at_a_glance": [
            "<li>The first week sets the foundation for your puppy’s behaviour, confidence, and routine.</li>",
            "<li>Keep the environment calm – limit visitors and new experiences to short, positive sessions.</li>",
            "<li>Establish consistent feeding, toileting, and sleeping schedules from day one.</li>",
            "<li>Book a vet health check within the first week.</li>",
        ],
        "takeaways": [
            "<li>A calm, structured first week helps your puppy settle faster and reduces anxiety.</li>",
            "<li>Consistency in routine, sleeping location, and toileting spot is the single most important factor.</li>",
            "<li>Build alone time gradually to prevent separation anxiety developing.</li>",
            "<li>Register with a vet and complete a health check within the first seven days.</li>",
        ],
    },
    7170: {
        # This is the Puppy Care GLOSSARY post (but it's categorised under puppy care IDs)
        # Wait - 7170 is listed under PUPPY_CARE_IDS but title says "Dog Health Terminology"
        # Let me treat it based on content
        "cluster": "Puppy Care",
        "glossary": [
            ("<strong>Socialisation window</strong>", "The period between 3 and 14 weeks when puppies are most open to forming positive associations with new people, animals, and environments."),
            ("<strong>Recall training</strong>", "Teaching a puppy to return to you on command – one of the most important safety skills."),
            ("<strong>Crate training</strong>", "The process of helping a puppy feel secure and relaxed in a crate, supporting house training and providing a safe retreat."),
            ("<strong>Teething phase</strong>", "The developmental period (roughly 3–7 months) when adult teeth replace baby teeth, often causing increased chewing."),
            ("<strong>Positive reinforcement</strong>", "A training method that rewards desired behaviour to encourage repetition, endorsed by UK organisations such as the RSPCA and Dogs Trust."),
            ("<strong>House training</strong>", "Teaching a puppy to toilet in an appropriate outdoor area through consistent routine and reward-based methods."),
            ("<strong>Microchipping</strong>", "A legal requirement in England, Scotland, and Wales: a tiny chip inserted under the skin that stores the owner’s contact details."),
        ],
        "mistakes": [
            "<li><strong>Relying on outdated terminology</strong> – Terms like “dominance” and “alpha” have been discredited by modern veterinary science. Use positive, reward-based language.</li>",
            "<li><strong>Confusing normal behaviour with problems</strong> – Mouthing, zoomies, and occasional toileting accidents are all normal puppy behaviours, not signs of disobedience.</li>",
            "<li><strong>Misunderstanding vaccination timelines</strong> – “Fully vaccinated” means 1–2 weeks after the second jab, not the day of the injection.</li>",
            "<li><strong>Assuming one breed guide fits all</strong> – Developmental timelines and care needs vary significantly between toy, medium, and giant breeds.</li>",
        ],
        "seek_help": [
            "<li>You are unsure about any health or care term your vet has used – always ask for clarification rather than guessing.</li>",
            "<li>Your puppy shows sudden behavioural changes that do not match any normal developmental phase.</li>",
            "<li>You receive conflicting advice from different sources – your vet or a <a href=\"https://www.rspca.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">RSPCA</a>-affiliated behaviourist can help clarify.</li>",
        ],
        "beginner": [
            "<li>Bookmark this glossary and refer back to it when you encounter unfamiliar terms from your vet, trainer, or pet care articles.</li>",
            "<li>Focus on understanding the terms related to your puppy’s current age and stage first.</li>",
            "<li>Ask your vet to explain any medical terminology in plain language – a good vet will always be happy to do so.</li>",
            "<li>Use the <a href=\"https://www.pdsa.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">PDSA</a> and <a href=\"https://www.dogstrust.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">Dogs Trust</a> websites as free, reliable UK resources alongside this glossary.</li>",
        ],
        "at_a_glance": [
            "<li>This glossary covers the most common puppy care and health terms you will encounter as a new owner.</li>",
            "<li>Understanding correct terminology helps you communicate effectively with vets and trainers.</li>",
            "<li>Outdated terms like “dominance” have been replaced by positive, science-based language.</li>",
            "<li>Bookmark this page for quick reference whenever you need to check a term.</li>",
        ],
        "takeaways": [
            "<li>Knowing key puppy care terms improves communication with your vet and helps you follow advice accurately.</li>",
            "<li>Modern puppy care is based on positive reinforcement – ignore outdated dominance-based terminology.</li>",
            "<li>Developmental stages and timelines vary by breed, so always ask your vet about your specific puppy.</li>",
            "<li>Use trusted UK sources (RSPCA, PDSA, Dogs Trust, Kennel Club) to verify any advice you receive.</li>",
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # DOG HEALTH CLUSTER
    # ═══════════════════════════════════════════════════════════════
    5520: {
        "cluster": "Dog Health",
        "glossary": None,  # Already has
        "mistakes": [
            "<li><strong>Skipping annual vet check-ups</strong> – Many conditions such as dental disease, obesity, and joint problems develop silently. Regular check-ups catch issues early.</li>",
            "<li><strong>Self-diagnosing using online symptom checkers</strong> – Symptoms in dogs can overlap across many conditions. Always confirm with a qualified vet.</li>",
            "<li><strong>Stopping flea or worm treatment in winter</strong> – Central heating means fleas survive indoors year-round. Maintain treatment all 12 months.</li>",
            "<li><strong>Ignoring dental health</strong> – Over 80% of dogs over three show signs of dental disease. Prevention is far simpler and cheaper than treatment.</li>",
            "<li><strong>Waiting too long to seek help</strong> – Dogs instinctively hide pain. Subtle changes in behaviour, appetite, or energy often indicate a problem worth investigating.</li>",
        ],
        "seek_help": None,  # Already has
        "beginner": [
            "<li>Register with a local vet and book an initial health check as soon as you get your dog.</li>",
            "<li>Set calendar reminders for vaccinations, flea treatment, and worming on the schedules your vet recommends.</li>",
            "<li>Learn your dog’s normal baseline: resting breathing rate, gum colour, appetite, and activity level. Changes from this baseline are often the first sign of illness.</li>",
            "<li>Consider pet insurance or a <a href=\"https://www.pdsa.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">PDSA</a> health plan to manage unexpected costs.</li>",
        ],
        "at_a_glance": None,
        "takeaways": None,
    },
    4568: {
        "cluster": "Dog Health",
        # Everything already exists
        "glossary": None,
        "mistakes": None,
        "seek_help": None,
        "beginner": None,
        "at_a_glance": None,
        "takeaways": None,
    },
    4110: {
        "cluster": "Dog Health",
        "glossary": None,  # Already has
        "mistakes": None,  # Already has
        "seek_help": None,  # Already has
        "beginner": [
            "<li>If your dog is over 7 years old or a large breed prone to joint issues, discuss joint supplements with your vet at the next check-up.</li>",
            "<li>Start with a supplement containing glucosamine and chondroitin – the most widely studied ingredients for joint support.</li>",
            "<li>Allow at least 4–6 weeks of consistent daily use before assessing whether a supplement is making a difference.</li>",
            "<li>Combine supplementation with appropriate exercise, weight management, and a comfortable bed to support overall joint health.</li>",
        ],
        "at_a_glance": None,
        "takeaways": None,
    },
    4103: {
        "cluster": "Dog Health",
        "glossary": None,
        "mistakes": None,
        "seek_help": None,
        "beginner": [
            "<li>Choose a flea treatment method your vet recommends – spot-on, tablet, or collar – and use it consistently year-round.</li>",
            "<li>Treat all pets in the household at the same time to prevent cross-infestation.</li>",
            "<li>Wash pet bedding at 60°C regularly and vacuum soft furnishings to break the flea lifecycle in your home.</li>",
            "<li>If you are unsure which product suits your dog, ask your vet rather than relying on over-the-counter options alone.</li>",
        ],
        "at_a_glance": None,
        "takeaways": None,
    },
    4096: {
        "cluster": "Dog Health",
        # Everything already exists
        "glossary": None,
        "mistakes": None,
        "seek_help": None,
        "beginner": None,
        "at_a_glance": None,
        "takeaways": None,
    },
    4089: {
        "cluster": "Dog Health",
        "glossary": None,  # Already has
        "mistakes": [
            "<li><strong>Treating symptoms instead of causes</strong> – Persistent scratching, for example, could indicate allergies, parasites, or skin infection. A vet can identify the root cause.</li>",
            "<li><strong>Relying on human medication</strong> – Many common human painkillers (ibuprofen, paracetamol) are toxic to dogs. Never give medication without veterinary advice.</li>",
            "<li><strong>Neglecting weight management</strong> – The PDSA estimates over half of UK dogs are overweight. Excess weight contributes to joint disease, diabetes, and reduced lifespan.</li>",
            "<li><strong>Inconsistent preventive care</strong> – Skipping months of flea, worm, or dental treatment creates gaps in protection that are difficult to recover from.</li>",
        ],
        "seek_help": None,
        "beginner": [
            "<li>Build a relationship with one trusted vet practice so your dog’s full health history is in one place.</li>",
            "<li>Create a simple health calendar covering vaccinations, flea/worm treatments, and dental checks.</li>",
            "<li>Learn to do a basic home health check: eyes, ears, teeth, coat, weight, and movement – the <a href=\"https://www.pdsa.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">PDSA</a> website has a step-by-step guide.</li>",
            "<li>Start dental care early – daily brushing from puppyhood is the gold standard, but dental chews and water additives can supplement the routine.</li>",
        ],
        "at_a_glance": None,
        "takeaways": None,
    },
    7169: {
        # Puppy Care Glossary post (listed under DOG_HEALTH_IDS but title = "Puppy Care Glossary")
        "cluster": "Dog Health",
        "glossary": None,  # Already has Key Terms
        "mistakes": [
            "<li><strong>Using outdated or debunked terms</strong> – Concepts like “alpha dog” and “dominance hierarchy” have been rejected by modern veterinary behaviourists. Stick to evidence-based terminology.</li>",
            "<li><strong>Confusing medical and behavioural terms</strong> – “Aggression” is a behaviour, not a diagnosis. A behaviourist or vet can help distinguish between fear-based reactivity and genuine aggression.</li>",
            "<li><strong>Assuming all puppies develop at the same rate</strong> – Giant breeds may not reach full maturity until 2–3 years, while small breeds may mature by 12 months.</li>",
            "<li><strong>Ignoring breed-specific health terms</strong> – Conditions like brachycephalic obstructive airway syndrome (BOAS) or hip dysplasia are breed-related and worth understanding early.</li>",
        ],
        "seek_help": [
            "<li>You encounter a veterinary term you do not understand during a consultation – always ask your vet to explain.</li>",
            "<li>Your puppy displays behaviour that does not match expected developmental patterns for their age and breed.</li>",
            "<li>You receive conflicting health or training advice – a qualified veterinary behaviourist or <a href=\"https://www.rspca.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">RSPCA</a> advisor can provide clarity.</li>",
        ],
        "beginner": [
            "<li>Start with the terms most relevant to your puppy’s current life stage and revisit this glossary as they grow.</li>",
            "<li>Write down any terms your vet uses that you do not recognise and look them up afterwards.</li>",
            "<li>Cross-reference unfamiliar terms with trusted UK sources: <a href=\"https://www.pdsa.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">PDSA</a>, <a href=\"https://www.rspca.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">RSPCA</a>, and the <a href=\"https://www.bva.co.uk/\" rel=\"nofollow noopener\" target=\"_blank\">BVA</a>.</li>",
            "<li>Understanding the correct meaning of terms like “socialisation” and “positive reinforcement” will help you follow training advice accurately.</li>",
        ],
        "at_a_glance": [
            "<li>This glossary covers essential puppy care and veterinary terms every owner should know.</li>",
            "<li>Modern puppy care uses science-based, positive terminology – outdated dominance language is no longer recommended.</li>",
            "<li>Breed-specific terms matter: some conditions and timelines vary significantly by breed type.</li>",
            "<li>Use this page as a quick reference alongside advice from your vet.</li>",
        ],
        "takeaways": [
            "<li>A solid understanding of puppy care terminology helps you follow veterinary and training advice with confidence.</li>",
            "<li>Always ask your vet to clarify any term you do not understand – there are no silly questions.</li>",
            "<li>Outdated dominance-based terms have been replaced by positive, evidence-based language across UK veterinary practice.</li>",
            "<li>Bookmark this glossary and revisit it as your puppy grows through each developmental stage.</li>",
        ],
    },
}


# ─── Helper Functions ────────────────────────────────────────────────

def api_get(post_id):
    """Fetch post content via WP REST API."""
    url = f"{BASE}/posts/{post_id}?context=edit"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout)

def api_update(post_id, content):
    """Update post content via WP REST API."""
    payload = json.dumps({"content": content})
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir=DATA_DIR) as f:
        f.write(payload)
        tmppath = f.name
    try:
        url = f"{BASE}/posts/{post_id}"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-d", f"@{tmppath}",
             "-H", "Content-Type: application/json",
             "-X", "POST", url],
            capture_output=True, text=True, timeout=60
        )
        resp = json.loads(result.stdout)
        if 'id' in resp:
            return True, resp
        else:
            return False, resp
    finally:
        os.unlink(tmppath)

def has_block(content, marker):
    """Check if a block already exists in content (case-insensitive)."""
    return marker.lower() in content.lower()

def find_trust_footer_position(content):
    """
    Find the position of the trust footer. We look for several patterns:
    1. editorial-trust-footer div
    2. "Our Editorial Standards" heading near the end
    3. "About Our Editorial Standards" heading
    4. Last "Sources and References" section
    """
    # Pattern 1: editorial-trust-footer div
    m = re.search(r'<div class="editorial-trust-footer"', content)
    if m:
        return m.start()

    # Pattern 2: "Our Editorial Standards" as H3/H4 near the end (last occurrence)
    matches = list(re.finditer(r'(?:<!-- wp:heading[^>]*-->[\s]*)?<h[2-4][^>]*>(?:About )?Our Editorial Standards</h[2-4]>', content))
    if matches:
        last = matches[-1]
        # Walk backwards to find the start of the wp:group or separator before it
        search_start = max(0, last.start() - 300)
        chunk = content[search_start:last.start()]
        # Look for separator or group start
        sep = chunk.rfind('<!-- wp:separator')
        grp = chunk.rfind('<!-- wp:group')
        if sep >= 0:
            return search_start + sep
        elif grp >= 0:
            return search_start + grp
        return last.start()

    # Pattern 3: Sources and References (last occurrence)
    matches = list(re.finditer(r'<h[2-4][^>]*>Sources and References</h', content))
    if matches:
        return matches[-1].start()

    # Fallback: end of content
    return len(content)

def find_first_paragraph_end(content):
    """Find the position after the first substantial paragraph for At a Glance insertion."""
    # Skip any initial group blocks (like editorial info boxes) and find first real <p> or </p>
    # Look for the first H1 or H2 heading, then insert after the paragraph following it
    h_match = re.search(r'<h[12][^>]*>.*?</h[12]>', content)
    if h_match:
        # Find the end of the paragraph after this heading
        after_heading = content[h_match.end():]
        p_end = after_heading.find('</p>')
        if p_end >= 0:
            return h_match.end() + p_end + 4

    # Fallback: after the first real paragraph (skip quick-answer if present)
    # Look for any </p> that's not inside a group div
    p_matches = list(re.finditer(r'</p>', content))
    if len(p_matches) >= 2:
        return p_matches[1].end()
    elif p_matches:
        return p_matches[0].end()
    return 0

def build_items_html(items):
    return "\n".join(items)

def build_terms_html(terms):
    return "\n".join([f"<li>{term} – {defn}</li>" for term, defn in terms])


# ─── Main Processing ────────────────────────────────────────────────

def process_post(post_id, data):
    """Process a single post, adding all missing blocks."""
    print(f"\n{'='*60}")
    print(f"Processing post {post_id} ({data['cluster']})")

    post = api_get(post_id)
    title = post.get('title', {}).get('rendered', 'Unknown')
    content = post.get('content', {}).get('raw', '')
    print(f"Title: {title[:70]}")
    print(f"Content length: {len(content)}")

    result = {
        'id': post_id,
        'title': title,
        'cluster': data['cluster'],
        'glossary_added': 'skipped',
        'common_mistakes_added': 'skipped',
        'seek_help_added': 'skipped',
        'beginner_recs_added': 'skipped',
        'at_a_glance_status': 'skipped',
        'key_takeaways_status': 'skipped',
        'status': 'ok',
    }

    modified = False

    # ── 1. At a Glance (after first paragraph) ──
    if data.get('at_a_glance') and not has_block(content, 'at a glance'):
        items_html = build_items_html(data['at_a_glance'])
        block = at_a_glance_block(items_html)
        pos = find_first_paragraph_end(content)
        if pos > 0:
            content = content[:pos] + "\n\n" + block + "\n\n" + content[pos:]
            result['at_a_glance_status'] = 'added'
            modified = True
            print(f"  + At a Glance added at position {pos}")
        else:
            result['at_a_glance_status'] = 'failed_no_position'
            print(f"  ! At a Glance: could not find insertion position")
    elif has_block(content, 'at a glance'):
        result['at_a_glance_status'] = 'already_exists'
        print(f"  = At a Glance already exists")
    else:
        result['at_a_glance_status'] = 'no_data'

    # ── Find trust footer position (for all blocks inserted before it) ──
    footer_pos = find_trust_footer_position(content)
    print(f"  Trust footer detected at position {footer_pos} / {len(content)}")

    # We need to insert blocks BEFORE the trust footer in this order:
    # ... Common Mistakes ... When to Seek Help ... Beginner Recs ... Key Terms ... Key Takeaways ... [trust footer]
    # We'll build the blocks to insert and place them all at once before the footer

    blocks_to_insert = []

    # ── 2. Common Mistakes ──
    if data.get('mistakes') and not has_block(content, 'common mistakes'):
        items_html = build_items_html(data['mistakes'])
        block = common_mistakes_block(items_html)
        blocks_to_insert.append(('common_mistakes', block))
        result['common_mistakes_added'] = 'added'
        print(f"  + Common Mistakes prepared")
    elif has_block(content, 'common mistakes'):
        result['common_mistakes_added'] = 'already_exists'
        print(f"  = Common Mistakes already exists")
    else:
        result['common_mistakes_added'] = 'no_data'

    # ── 3. When to Seek Help ──
    if data.get('seek_help') and not has_block(content, 'when to seek'):
        items_html = build_items_html(data['seek_help'])
        block = seek_help_block(items_html)
        blocks_to_insert.append(('seek_help', block))
        result['seek_help_added'] = 'added'
        print(f"  + When to Seek Help prepared")
    elif has_block(content, 'when to seek'):
        result['seek_help_added'] = 'already_exists'
        print(f"  = When to Seek Help already exists")
    else:
        result['seek_help_added'] = 'no_data'

    # ── 4. Beginner Recommendations ──
    if data.get('beginner') and not has_block(content, 'beginner'):
        items_html = build_items_html(data['beginner'])
        block = beginner_recs_block(items_html)
        blocks_to_insert.append(('beginner', block))
        result['beginner_recs_added'] = 'added'
        print(f"  + Beginner Recommendations prepared")
    elif has_block(content, 'beginner'):
        result['beginner_recs_added'] = 'already_exists'
        print(f"  = Beginner Recommendations already exists")
    else:
        result['beginner_recs_added'] = 'no_data'

    # ── 5. Key Terms (Glossary) ──
    if data.get('glossary') and not has_block(content, 'key terms'):
        terms_html = build_terms_html(data['glossary'])
        block = glossary_block(terms_html)
        blocks_to_insert.append(('glossary', block))
        result['glossary_added'] = 'added'
        print(f"  + Key Terms (Glossary) prepared")
    elif has_block(content, 'key terms'):
        result['glossary_added'] = 'already_exists'
        print(f"  = Key Terms already exists")
    else:
        result['glossary_added'] = 'no_data'

    # ── 6. Key Takeaways ──
    if data.get('takeaways') and not has_block(content, 'key takeaways'):
        items_html = build_items_html(data['takeaways'])
        block = key_takeaways_block(items_html)
        blocks_to_insert.append(('takeaways', block))
        result['key_takeaways_status'] = 'added'
        print(f"  + Key Takeaways prepared")
    elif has_block(content, 'key takeaways'):
        result['key_takeaways_status'] = 'already_exists'
        print(f"  = Key Takeaways already exists")
    else:
        result['key_takeaways_status'] = 'no_data'

    # ── Insert all blocks before trust footer ──
    if blocks_to_insert:
        # Re-calculate footer position since At a Glance may have shifted it
        footer_pos = find_trust_footer_position(content)
        combined = "\n\n".join([b for _, b in blocks_to_insert])
        content = content[:footer_pos] + "\n\n" + combined + "\n\n" + content[footer_pos:]
        modified = True
        print(f"  Inserted {len(blocks_to_insert)} block(s) before trust footer")

    # ── Update post if modified ──
    if modified:
        time.sleep(DELAY)
        success, resp = api_update(post_id, content)
        if success:
            new_len = len(resp.get('content', {}).get('raw', ''))
            print(f"  UPDATE SUCCESS - new content length: {new_len}")
            result['status'] = 'updated'
        else:
            print(f"  UPDATE FAILED: {json.dumps(resp)[:300]}")
            result['status'] = 'update_failed'
    else:
        print(f"  No changes needed for this post")
        result['status'] = 'no_changes'

    return result


def main():
    print("=" * 60)
    print("Phase 10AU Cluster Rescue - Puppy Care & Dog Health")
    print("=" * 60)

    all_ids = PUPPY_CARE_IDS + DOG_HEALTH_IDS
    results = []

    for post_id in all_ids:
        if post_id not in CONTENT_DATA:
            print(f"\nWARNING: No content data for post {post_id}, skipping")
            continue

        data = CONTENT_DATA[post_id]
        try:
            result = process_post(post_id, data)
            results.append(result)
        except Exception as e:
            print(f"\nERROR processing post {post_id}: {e}")
            results.append({
                'id': post_id,
                'title': 'ERROR',
                'cluster': data.get('cluster', '?'),
                'glossary_added': 'error',
                'common_mistakes_added': 'error',
                'seek_help_added': 'error',
                'beginner_recs_added': 'error',
                'at_a_glance_status': 'error',
                'key_takeaways_status': 'error',
                'status': f'error: {str(e)[:100]}',
            })

        time.sleep(DELAY)

    # ── Write CSV log ──
    fieldnames = ['id', 'title', 'cluster', 'glossary_added', 'common_mistakes_added',
                  'seek_help_added', 'beginner_recs_added', 'at_a_glance_status',
                  'key_takeaways_status', 'status']

    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"\n{'='*60}")
    print(f"COMPLETE - {len(results)} posts processed")
    print(f"Log written to: {LOG_FILE}")

    # Summary
    added_counts = {
        'glossary': sum(1 for r in results if r['glossary_added'] == 'added'),
        'common_mistakes': sum(1 for r in results if r['common_mistakes_added'] == 'added'),
        'seek_help': sum(1 for r in results if r['seek_help_added'] == 'added'),
        'beginner_recs': sum(1 for r in results if r['beginner_recs_added'] == 'added'),
        'at_a_glance': sum(1 for r in results if r['at_a_glance_status'] == 'added'),
        'key_takeaways': sum(1 for r in results if r['key_takeaways_status'] == 'added'),
    }
    updated = sum(1 for r in results if r['status'] == 'updated')
    no_changes = sum(1 for r in results if r['status'] == 'no_changes')
    errors = sum(1 for r in results if 'error' in r['status'])

    print(f"\nBlocks added:")
    for k, v in added_counts.items():
        print(f"  {k}: {v}")
    print(f"\nPosts updated: {updated}")
    print(f"Posts unchanged: {no_changes}")
    print(f"Errors: {errors}")


if __name__ == "__main__":
    main()
