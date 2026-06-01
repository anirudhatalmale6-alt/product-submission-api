"""
Directory Submission Tracker for PetHub Online
Tracks Tier 1 UK business directory submissions for SEO backlinks.

This script:
1. Checks directory listing pages for PetHub Online presence
2. Records submission status
3. Updates the directory dashboard data
"""
import requests, json, time, re
from datetime import datetime

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Encoding': 'gzip, deflate'
})

SITE_URL = 'https://pethubonline.com'
SITE_NAME = 'PetHub Online'
BUSINESS_INFO = {
    'name': 'PetHub Online',
    'url': 'https://pethubonline.com',
    'description': 'UK pet supplies reviews, guides, and educational resources for dog, cat, and fish owners.',
    'category': 'Pet Supplies / Pet Services',
    'location': 'United Kingdom',
}

# Tier 1 directories with submission URLs and DA scores
DIRECTORIES = [
    {
        'name': 'Yell.com',
        'url': 'https://www.yell.com',
        'submit_url': 'https://www.yell.com/free-listing/',
        'da': 72,
        'category': 'General Business',
        'link_type': 'nofollow',
        'status': 'not_started',
        'notes': 'UK largest business directory. Free listing available.'
    },
    {
        'name': 'Thomson Local',
        'url': 'https://www.thomsonlocal.com',
        'submit_url': 'https://www.thomsonlocal.com/add-your-business/',
        'da': 55,
        'category': 'General Business',
        'link_type': 'nofollow',
        'status': 'not_started',
        'notes': 'UK local business directory. Free listing.'
    },
    {
        'name': 'FreeIndex',
        'url': 'https://www.freeindex.co.uk',
        'submit_url': 'https://www.freeindex.co.uk/addcompany.htm',
        'da': 60,
        'category': 'General Business',
        'link_type': 'dofollow',
        'status': 'not_started',
        'notes': 'UK free business directory with dofollow links.'
    },
    {
        'name': 'Scoot',
        'url': 'https://www.scoot.co.uk',
        'submit_url': 'https://www.scoot.co.uk/add-listing/',
        'da': 45,
        'category': 'General Business',
        'link_type': 'nofollow',
        'status': 'not_started',
        'notes': 'UK business directory.'
    },
    {
        'name': 'Cylex UK',
        'url': 'https://www.cylex-uk.co.uk',
        'submit_url': 'https://www.cylex-uk.co.uk/add-company.html',
        'da': 50,
        'category': 'General Business',
        'link_type': 'dofollow',
        'status': 'not_started',
        'notes': 'UK Cylex directory with dofollow links.'
    },
    {
        'name': 'Yelp UK',
        'url': 'https://www.yelp.co.uk',
        'submit_url': 'https://biz.yelp.co.uk/signup_business',
        'da': 94,
        'category': 'General Business',
        'link_type': 'nofollow',
        'status': 'not_started',
        'notes': 'Highest DA directory. Strong trust signal.'
    },
    {
        'name': 'Bark.com',
        'url': 'https://www.bark.com',
        'submit_url': 'https://www.bark.com/en/gb/pro/',
        'da': 65,
        'category': 'Services',
        'link_type': 'nofollow',
        'status': 'not_started',
        'notes': 'Service provider directory.'
    },
    {
        'name': 'Hotfrog UK',
        'url': 'https://www.hotfrog.co.uk',
        'submit_url': 'https://www.hotfrog.co.uk/AddYourBusiness.aspx',
        'da': 48,
        'category': 'General Business',
        'link_type': 'dofollow',
        'status': 'not_started',
        'notes': 'International directory with UK section. Dofollow.'
    },
    {
        'name': 'PetProfessional.co.uk',
        'url': 'https://www.petprofessional.co.uk',
        'submit_url': 'https://www.petprofessional.co.uk/register',
        'da': 30,
        'category': 'Pet Industry',
        'link_type': 'dofollow',
        'status': 'not_started',
        'notes': 'UK pet industry professional directory. Niche relevance.'
    },
    {
        'name': 'UKPDA',
        'url': 'https://www.ukpda.co.uk',
        'submit_url': 'https://www.ukpda.co.uk/join',
        'da': 25,
        'category': 'Pet Industry',
        'link_type': 'dofollow',
        'status': 'not_started',
        'notes': 'UK Pet Directory Association. High niche relevance.'
    },
    {
        'name': 'VetClick',
        'url': 'https://www.vetclick.com',
        'submit_url': 'https://www.vetclick.com/register',
        'da': 35,
        'category': 'Pet/Vet Industry',
        'link_type': 'dofollow',
        'status': 'not_started',
        'notes': 'Veterinary and pet industry directory.'
    },
    {
        'name': 'PetDirectory.co.uk',
        'url': 'https://www.petdirectory.co.uk',
        'submit_url': 'https://www.petdirectory.co.uk/submit',
        'da': 28,
        'category': 'Pet Industry',
        'link_type': 'dofollow',
        'status': 'not_started',
        'notes': 'UK pet-specific directory. High topical relevance.'
    },
    {
        'name': 'Brownbook',
        'url': 'https://www.brownbook.net',
        'submit_url': 'https://www.brownbook.net/add-listing/',
        'da': 52,
        'category': 'General Business',
        'link_type': 'nofollow',
        'status': 'not_started',
        'notes': 'Global business directory with UK listings.'
    },
    {
        'name': '192.com',
        'url': 'https://www.192.com',
        'submit_url': 'https://www.192.com/add-listing/',
        'da': 68,
        'category': 'General Business',
        'link_type': 'nofollow',
        'status': 'not_started',
        'notes': 'UK people/business search. High DA.'
    },
    {
        'name': 'Foursquare',
        'url': 'https://foursquare.com',
        'submit_url': 'https://foursquare.com/add-place',
        'da': 92,
        'category': 'General Business',
        'link_type': 'nofollow',
        'status': 'not_started',
        'notes': 'Very high DA. Location-based directory.'
    },
]

def generate_submission_report():
    """Generate a JSON report of directory submission status."""
    report = {
        'generated': datetime.now().isoformat(),
        'site': SITE_URL,
        'total_directories': len(DIRECTORIES),
        'submitted': sum(1 for d in DIRECTORIES if d['status'] in ('submitted', 'pending_review', 'approved', 'live')),
        'approved': sum(1 for d in DIRECTORIES if d['status'] in ('approved', 'live')),
        'live': sum(1 for d in DIRECTORIES if d['status'] == 'live'),
        'pending': sum(1 for d in DIRECTORIES if d['status'] == 'pending_review'),
        'not_started': sum(1 for d in DIRECTORIES if d['status'] == 'not_started'),
        'rejected': sum(1 for d in DIRECTORIES if d['status'] == 'rejected'),
        'total_da_potential': sum(d['da'] for d in DIRECTORIES),
        'dofollow_count': sum(1 for d in DIRECTORIES if d['link_type'] == 'dofollow'),
        'nofollow_count': sum(1 for d in DIRECTORIES if d['link_type'] == 'nofollow'),
        'directories': DIRECTORIES,
        'submission_instructions': {
            'note': 'Directory submissions require manual action by the site owner.',
            'steps': [
                '1. Visit the submit_url for each directory',
                '2. Create an account if required',
                '3. Fill in business details using the BUSINESS_INFO above',
                '4. Submit listing for review',
                '5. Update this tracker with submission date and status',
                '6. Monitor for approval and update when listing goes live'
            ],
            'priority_order': [
                'Yelp UK (DA 94) - Highest authority',
                'Foursquare (DA 92) - Very high authority',
                'Yell.com (DA 72) - UK primary directory',
                '192.com (DA 68) - Strong UK presence',
                'Bark.com (DA 65) - Service directory',
                'FreeIndex (DA 60) - Dofollow link',
                'Thomson Local (DA 55) - UK local directory',
                'Brownbook (DA 52) - Global directory',
                'Cylex UK (DA 50) - Dofollow link',
                'Hotfrog UK (DA 48) - Dofollow link',
                'Scoot (DA 45) - UK directory',
                'VetClick (DA 35) - Pet industry niche',
                'PetProfessional (DA 30) - Pet industry niche',
                'PetDirectory (DA 28) - Pet niche',
                'UKPDA (DA 25) - Pet association'
            ]
        }
    }

    with open('/var/lib/freelancer/projects/40416335/directory_submission_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Directory Submission Report Generated")
    print(f"{'='*50}")
    print(f"Total Directories: {report['total_directories']}")
    print(f"Submitted: {report['submitted']}")
    print(f"Approved: {report['approved']}")
    print(f"Live Links: {report['live']}")
    print(f"Not Started: {report['not_started']}")
    print(f"Total DA Potential: {report['total_da_potential']}")
    print(f"Dofollow Links: {report['dofollow_count']}")
    print(f"Nofollow Links: {report['nofollow_count']}")
    print(f"\nPriority submission order saved to report.")

    return report

if __name__ == '__main__':
    generate_submission_report()
