# GSC Activation Pack - pethubonline.com

**For: Jason**
**Date: May 31, 2026**
**Time required: About 5 minutes of your time**

---

## What This Is About

Google Search Console (GSC) is a free Google tool that shows how your site appears in Google search results - how many people see it, how many click through, and what keywords bring them in.

We need to reconnect the GSC data feed so your dashboards light up with real traffic data, indexing status, and growth opportunities. All you need to do is click a link and copy a code back to me. That's it.

---

## Section 1: What You Need Before Starting

You only need ONE thing:

1. The Google account (Gmail or Google Workspace email) that has **owner access** to pethubonline.com in Google Search Console.

That's it. No passwords to share, no software to install, no technical knowledge required.

---

## Section 2: Option A - Quick Re-Authentication (Preferred)

This is the fastest path. Follow these steps in order:

### Step 1: Confirm Your GSC Access

1. Open your web browser (Chrome, Safari, Firefox - any will work).
2. Go to: **https://search.google.com/search-console**
3. Sign in with your Google account if prompted.
4. Look for **pethubonline.com** in the list of properties on the left side or in the property selector dropdown at the top.
5. Click on it. If you can see data (or even an empty dashboard), you have access.

### Step 2: Tell Me Which Email You Used

1. Look at the top-right corner of the Google Search Console page.
2. You will see a small circular icon or your profile picture - click it.
3. It will show the email address you are signed in with.
4. Send me that email address.

### Step 3: Click the Authorization Link I Send You

1. After you send me the email, I will reply with a special link (it will start with "https://accounts.google.com/...").
2. Click that link. It will open a Google sign-in page.
3. Sign in with the SAME Google account that has GSC access for pethubonline.com.
4. Google will ask: "Allow this app to access your Search Console data?" - Click **Allow**.
5. You may need to click "Allow" one more time on a confirmation screen.

### Step 4: Copy the Code and Send It to Me

1. After you click Allow, Google will show you a page with a code. It looks something like: `4/0AX4XfWh8...` (a long string of letters and numbers).
2. Copy that entire code.
3. Paste it in a message and send it to me.

### Step 5: Done - I Handle the Rest

1. I take that code and update the token file on the server (at 167.99.198.145).
2. The credential file at `/opt/pethub-agents/credentials/google-oauth.json` gets refreshed.
3. Data starts flowing within minutes.

**That's all you need to do. Five steps, about five minutes.**

---

## Section 3: Option B - Fresh Setup (Only If You Don't Have GSC Access Yet)

If you went to search.google.com/search-console and did NOT see pethubonline.com listed, follow these steps first:

### Step 1: Add Your Site to Google Search Console

1. Go to: **https://search.google.com/search-console**
2. Sign in with your Google account.
3. Click the property selector dropdown (top-left area).
4. Click **"Add property"**.
5. Choose **"URL prefix"** on the right side.
6. Type in: **https://pethubonline.com**
7. Click **Continue**.

### Step 2: Verify You Own the Site

Google needs to confirm you actually own pethubonline.com. The easiest method:

**Method A - HTML File Upload (Easiest if you have hosting access):**
1. Google will offer you a small HTML file to download.
2. Send me that file and I will upload it to your server for you.
3. Then click "Verify" in Google Search Console.

**Method B - DNS TXT Record (If you manage your domain):**
1. Google will show you a TXT record that looks like: `google-site-verification=xxxxxx`
2. Send me that text and tell me where your domain is registered (GoDaddy, Namecheap, Cloudflare, etc.).
3. I can guide you through adding it, or add it for you if I have access.

### Step 3: Once Verified, Follow Option A Above

After verification is complete, go back to Section 2 (Option A) and follow those steps to complete the OAuth connection.

---

## Section 4: What Happens After Reconnection

Once the connection is live, here is what activates automatically on your behalf:

1. **Search Performance Data** - Impressions (how often your pages appear in Google), clicks (how many people visit from Google), click-through rate, and average position for every keyword.

2. **Indexing Status Monitoring** - We can see which of your pages Google has indexed, which ones have issues, and fix problems before they hurt your traffic.

3. **Crawl Frequency Tracking** - How often Google visits your site to check for new content. More crawling usually means Google sees your site as active and valuable.

4. **Growth Opportunity Report** - Generated automatically. This identifies keywords where you are close to page 1 (positions 11-20) and shows exactly which pages to optimize for quick wins.

5. **Traffic Realization Engine** - The system that turns search impressions into actual clicks by identifying underperforming pages and recommending title/description improvements.

All of this runs in the background. You will receive reports - no action needed from you unless you want to make changes.

---

## Section 5: Expected Timeline

| What | How Long |
|------|----------|
| Your part (clicking link + sending code) | About 5 minutes |
| Server token update (my part) | Under 1 hour |
| First data appearing in dashboards | 24-48 hours |
| Full historical data loaded | 48-72 hours |

The 24-48 hour wait is on Google's side - they batch-process data and don't release it instantly. This is completely normal.

---

## Section 6: Fallback Option (Service Account)

If for any reason the OAuth link method does not work (sometimes corporate Google accounts have restrictions), we have a backup plan:

### What Is a Service Account?

Think of it as a robot email address that can read your Search Console data on your behalf. No passwords involved - you just add it as a user.

### How to Set It Up (Only If Needed):

1. I will send you a service account email address. It will look something like: `gsc-reader@pethub-agents.iam.gserviceaccount.com`
2. Go to: **https://search.google.com/search-console**
3. Select **pethubonline.com**.
4. Click the **gear icon** (Settings) in the bottom-left.
5. Click **"Users and permissions"**.
6. Click the blue **"Add user"** button.
7. Paste the service account email I gave you.
8. Set permission to **"Full"** (so it can read all data).
9. Click **Add**.
10. Let me know it's done.

That's it. No links to click, no codes to copy. I handle everything else on the server side.

---

## Quick Summary

| Option | What You Do | Difficulty |
|--------|------------|------------|
| Option A (Preferred) | Click a link, copy a code, send it to me | Very Easy |
| Option B | Add site to GSC first, then do Option A | Easy (one extra step) |
| Fallback | Add a robot email as a user in GSC settings | Very Easy |

---

## Need Help?

If you get stuck at any step, just send me a screenshot of what you see and I will guide you through it. There is no way to break anything here - worst case, we just try again.

**Site:** https://pethubonline.com
**Server:** 167.99.198.145
**Credential file:** /opt/pethub-agents/credentials/google-oauth.json
