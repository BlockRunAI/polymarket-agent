# Update DNS for polyagent.blockrun.ai

## Current Setup

After cleanup, you now have **only Tokyo region** deployed:

```
✓ Service: polymarket-agent
✓ Region: asia-northeast1 (Tokyo)
✓ URL: https://polymarket-agent-uwh7ke4zsa-an.a.run.app
```

## DNS Update Needed

Your domain `polyagent.blockrun.ai` needs to point to the Tokyo service.

### Option 1: Cloudflare (Most Likely)

If you're using Cloudflare for DNS:

1. **Go to Cloudflare Dashboard**
   - Login to https://dash.cloudflare.com
   - Select domain: `blockrun.ai`

2. **Find the DNS record for `polyagent`**
   - Look for a CNAME record: `polyagent` → `...`

3. **Update the CNAME target to:**
   ```
   polyagent-uwh7ke4zsa-an.a.run.app
   ```

   **OR if using an A record, point to Cloud Run IPs:**
   ```
   216.239.32.21
   216.239.34.21
   216.239.36.21
   216.239.38.21
   ```

4. **Save and wait 1-5 minutes** for DNS propagation

### Option 2: Google Cloud DNS

If using Google Cloud DNS:

```bash
# Check current DNS records
gcloud dns record-sets list --zone=YOUR_ZONE_NAME

# Update the CNAME record
gcloud dns record-sets update polyagent.blockrun.ai. \
    --zone=YOUR_ZONE_NAME \
    --type=CNAME \
    --rrdatas=polyagent-uwh7ke4zsa-an.a.run.app. \
    --ttl=300
```

### Option 3: Cloud Run Domain Mapping (Alternative)

You can also use Cloud Run's built-in domain mapping:

```bash
gcloud beta run domain-mappings create \
    --service polymarket-agent \
    --domain polyagent.blockrun.ai \
    --region asia-northeast1
```

This will give you DNS records to add to your DNS provider.

## Verify It's Working

After updating DNS:

1. **Wait 1-5 minutes** for propagation
2. **Hard refresh** the page: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
3. **Check it loads Tokyo version:**
   - Should see "Positions & Orders" section
   - Check footer or logs for region info

## Quick Test

Check current DNS resolution:
```bash
nslookup polyagent.blockrun.ai
```

This should show the IP or CNAME it currently points to.

## Why Tokyo Only?

**Benefits:**
- ✓ Lower costs (1 region vs 3)
- ✓ Simpler deployment (one `./deploy-tokyo.sh`)
- ✓ Tokyo can place Polymarket orders (not geoblocked)
- ✓ Users can access from anywhere (dashboard access works globally)

**Trade-offs:**
- Slightly higher latency for EU/US users viewing dashboard
- But this doesn't matter for trading (orders execute server-side in Tokyo)
